"""Web Push through OneSignal (browser only)."""
import requests
from django.conf import settings

from ..services.rendering import render_text
from .base import BaseProvider, ProviderError, http_error

TIMEOUT = 15


class WebPushProvider(BaseProvider):
    channel = "push"

    def send(self, template, recipient, context):
        """`recipient` is a list of OneSignal subscription ids."""
        cfg = settings.ONESIGNAL
        if not cfg["APP_ID"] or not cfg["REST_API_KEY"]:
            raise ProviderError("ONESIGNAL_APP_ID / ONESIGNAL_REST_API_KEY not configured")
        if not recipient:
            raise ProviderError("User has no browser subscribed to Web Push")
        payload = {
            "app_id": cfg["APP_ID"],
            "target_channel": "push",
            "include_subscription_ids": list(recipient),
            "headings": {"en": render_text(template.title, template.variable_mapping, context) or settings.SITE_NAME},
            "contents": {"en": render_text(template.body, template.variable_mapping, context)},
        }
        if template.url:
            payload["url"] = template.url
        resp = requests.post(
            "https://api.onesignal.com/notifications",
            headers={"Authorization": f"Key {cfg['REST_API_KEY']}", "Content-Type": "application/json"},
            json=payload, timeout=TIMEOUT,
        )
        if not resp.ok:
            raise http_error(resp)
        data = resp.json()
        if data.get("errors"):
            raise ProviderError(f"OneSignal: {data['errors']}")
        return f"OneSignal notification id {data.get('id', '')}"
