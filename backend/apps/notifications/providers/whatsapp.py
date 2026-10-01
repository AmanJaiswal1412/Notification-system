"""WhatsApp Cloud API (sandbox/test number)."""
import re

import requests
from django.conf import settings

from ..constants import ApprovalStatus
from ..services.rendering import extract_placeholders, ordered_values
from .base import BaseProvider, ProviderError, http_error

TIMEOUT = 15
# Meta's pre-approved sandbox template - handy for a first smoke test.
SANDBOX_TEMPLATE = "hello_world"


def _cfg():
    return settings.WHATSAPP


def _base():
    return f"https://graph.facebook.com/{_cfg()['API_VERSION']}"


def _headers():
    token = _cfg()["ACCESS_TOKEN"]
    if not token:
        raise ProviderError("WHATSAPP_ACCESS_TOKEN is not configured")
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def slugify_template_name(name):
    return re.sub(r"[^a-z0-9_]+", "_", name.lower()).strip("_")[:500]


class WhatsAppProvider(BaseProvider):
    channel = "whatsapp"

    # ---- sending ----
    def send(self, template, recipient, context):
        phone_id = _cfg()["PHONE_NUMBER_ID"]
        if not phone_id:
            raise ProviderError("PHONE_NUMBER_ID is not configured")
        if not recipient:
            raise ProviderError("User has no phone number")
        name = template.wa_template_name or SANDBOX_TEMPLATE
        if name != SANDBOX_TEMPLATE and template.wa_status != ApprovalStatus.APPROVED:
            raise ProviderError(f"WhatsApp template is '{template.wa_status}' - submit and sync until approved")

        payload = {
            "messaging_product": "whatsapp",
            "to": re.sub(r"\D", "", recipient),
            "type": "template",
            "template": {"name": name, "language": {"code": template.wa_language or "en_US"}},
        }
        values = ordered_values(template.body, template.variable_mapping, context)
        if values and name != SANDBOX_TEMPLATE:
            payload["template"]["components"] = [
                {"type": "body", "parameters": [{"type": "text", "text": v or "-"} for v in values]}
            ]
        resp = requests.post(f"{_base()}/{phone_id}/messages", json=payload, headers=_headers(), timeout=TIMEOUT)
        if not resp.ok:
            raise http_error(resp)
        msg_id = (resp.json().get("messages") or [{}])[0].get("id", "")
        return f"WhatsApp message id {msg_id}"

    # ---- template management (Meta review flow) ----
    def submit_template(self, template):
        """Create the template at Meta (status becomes PENDING)."""
        waba = _cfg()["BUSINESS_ACCOUNT_ID"]
        if not waba:
            raise ProviderError("WHATSAPP_BUSINESS_ACCOUNT_ID is not configured")
        name = template.wa_template_name or slugify_template_name(f"{template.trigger.key}_{template.id}")
        placeholders = extract_placeholders(template.body)
        # Meta requires sequential numeric variables {{1}}, {{2}}... - convert named ones.
        body, mapping = template.body, dict(template.variable_mapping or {})
        numeric = {}
        for i, p in enumerate(placeholders, start=1):
            numeric[str(i)] = mapping.get(p, p)
            body = body.replace("{{" + p + "}}", "{{" + str(i) + "}}")
            body = re.sub(r"\{\{\s*" + re.escape(p) + r"\s*\}\}", "{{" + str(i) + "}}", body)
        body_component = {"type": "BODY", "text": body}
        if placeholders:
            body_component["example"] = {"body_text": [[f"sample {i}" for i in range(1, len(placeholders) + 1)]]}
        payload = {
            "name": name,
            "language": template.wa_language or "en_US",
            "category": template.wa_category or "UTILITY",
            "components": [body_component],
        }
        resp = requests.post(f"{_base()}/{waba}/message_templates", json=payload, headers=_headers(), timeout=TIMEOUT)
        if not resp.ok:
            raise http_error(resp)
        data = resp.json()
        template.wa_template_name = name
        template.body = body
        template.variable_mapping = numeric
        template.wa_external_id = data.get("id", "")
        template.wa_status = (data.get("status") or "PENDING").lower()
        template.wa_rejection_reason = ""
        template.save()
        return template.wa_status

    def sync_template(self, template):
        """Pull the latest approval status from Meta."""
        if template.wa_template_name == SANDBOX_TEMPLATE:
            template.wa_status = ApprovalStatus.APPROVED
            template.save(update_fields=["wa_status", "updated_at"])
            return template.wa_status
        waba = _cfg()["BUSINESS_ACCOUNT_ID"]
        if not waba:
            raise ProviderError("WHATSAPP_BUSINESS_ACCOUNT_ID is not configured")
        if not template.wa_template_name:
            raise ProviderError("Template has not been submitted yet")
        resp = requests.get(
            f"{_base()}/{waba}/message_templates",
            params={"name": template.wa_template_name, "fields": "name,status,rejected_reason,id,language"},
            headers=_headers(), timeout=TIMEOUT,
        )
        if not resp.ok:
            raise http_error(resp)
        rows = resp.json().get("data", [])
        if not rows:
            raise ProviderError("Template not found at Meta")
        row = rows[0]
        status = (row.get("status") or "").lower()
        template.wa_status = status if status in dict(ApprovalStatus.CHOICES) else ApprovalStatus.PENDING
        template.wa_external_id = row.get("id", template.wa_external_id)
        reason = row.get("rejected_reason") or ""
        template.wa_rejection_reason = "" if reason == "NONE" else reason
        template.save()
        return template.wa_status
