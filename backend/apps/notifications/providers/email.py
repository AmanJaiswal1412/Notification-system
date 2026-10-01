"""Transactional email. Pick the backend with EMAIL_PROVIDER=postmark|brevo|resend."""
import html

import requests
from django.conf import settings

from ..services.rendering import render_text
from .base import BaseProvider, ProviderError, http_error

TIMEOUT = 15


def _to_html(text):
    return "<div>" + html.escape(text).replace("\n", "<br>") + "</div>"


def _postmark(cfg, to, subject, text):
    resp = requests.post(
        "https://api.postmarkapp.com/email",
        headers={"X-Postmark-Server-Token": cfg["token"], "Accept": "application/json"},
        json={"From": cfg["from_email"], "To": to, "Subject": subject, "TextBody": text,
              "HtmlBody": _to_html(text), "MessageStream": "outbound"},
        timeout=TIMEOUT,
    )
    if not resp.ok:
        raise http_error(resp)
    return resp.json().get("MessageID", "")


def _brevo(cfg, to, subject, text):
    resp = requests.post(
        "https://api.brevo.com/v3/smtp/email",
        headers={"api-key": cfg["token"], "accept": "application/json"},
        json={"sender": {"email": cfg["from_email"]}, "to": [{"email": to}], "subject": subject,
              "textContent": text, "htmlContent": _to_html(text)},
        timeout=TIMEOUT,
    )
    if not resp.ok:
        raise http_error(resp)
    return resp.json().get("messageId", "")


def _resend(cfg, to, subject, text):
    resp = requests.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {cfg['token']}"},
        json={"from": cfg["from_email"], "to": [to], "subject": subject, "text": text, "html": _to_html(text)},
        timeout=TIMEOUT,
    )
    if not resp.ok:
        raise http_error(resp)
    return resp.json().get("id", "")


BACKENDS = {"postmark": _postmark, "brevo": _brevo, "resend": _resend}


class EmailProvider(BaseProvider):
    channel = "email"

    def send(self, template, recipient, context):
        name = settings.EMAIL_PROVIDER
        backend = BACKENDS.get(name)
        if not backend:
            raise ProviderError(f"Unknown EMAIL_PROVIDER '{name}'")
        cfg = settings.EMAIL_CONFIG[name]
        if not cfg["token"] or not cfg["from_email"]:
            raise ProviderError(f"{name} token / sender email not configured")
        if not recipient:
            raise ProviderError("User has no email address")
        subject = render_text(template.subject, template.variable_mapping, context)
        body = render_text(template.body, template.variable_mapping, context)
        msg_id = backend(cfg, recipient, subject, body)
        return f"{name} message id {msg_id}"
