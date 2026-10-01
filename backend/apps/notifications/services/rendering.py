"""Placeholder rendering shared by all channels.

Templates use ``{{ placeholder }}``. Each placeholder is resolved through the template's
``variable_mapping`` (placeholder -> context key) and falls back to the placeholder name itself,
so ``{{user.first_name}}`` works with no mapping and WhatsApp-style ``{{1}}`` works with
``{"1": "user.first_name"}``.
"""
import re

from django.conf import settings

PLACEHOLDER_RE = re.compile(r"\{\{\s*([\w.]+)\s*\}\}")

# Keys the admin UI offers in the variable picker.
AVAILABLE_VARIABLES = [
    {"key": "user.first_name", "label": "First name"},
    {"key": "user.username", "label": "Username"},
    {"key": "user.email", "label": "Email"},
    {"key": "user.phone", "label": "Phone"},
    {"key": "site_name", "label": "Site name"},
    {"key": "days_inactive", "label": "Days inactive (inactivity triggers)"},
    {"key": "reset_link", "label": "Reset link (password reset)"},
]


def build_context(user, extra=None):
    profile = getattr(user, "profile", None)
    ctx = {
        "user.first_name": user.first_name or user.username,
        "user.username": user.username,
        "user.email": user.email,
        "user.phone": getattr(profile, "phone", "") or "",
        "site_name": settings.SITE_NAME,
    }
    ctx.update(extra or {})
    return ctx


def extract_placeholders(text):
    seen = []
    for m in PLACEHOLDER_RE.findall(text or ""):
        if m not in seen:
            seen.append(m)
    return seen


def render_text(text, mapping, context):
    def repl(match):
        name = match.group(1)
        key = (mapping or {}).get(name, name)
        return str(context.get(key, ""))

    return PLACEHOLDER_RE.sub(repl, text or "")


def ordered_values(text, mapping, context):
    """Values in order of first appearance - used for WhatsApp positional parameters."""
    return [str(context.get((mapping or {}).get(p, p), "")) for p in extract_placeholders(text)]
