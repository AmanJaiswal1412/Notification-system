"""Fires notifications: Trigger -> enabled templates -> provider per channel."""
import logging
import threading

from django.conf import settings
from django.db import close_old_connections

from ..constants import Channel, LogStatus
from ..models import NotificationLog, PushSubscription, Template, Trigger
from ..providers import get_provider
from ..providers.base import ProviderError
from .rendering import build_context

logger = logging.getLogger(__name__)


def resolve_recipient(channel, user):
    if channel == Channel.WHATSAPP:
        return getattr(user.profile, "phone", "")
    if channel == Channel.EMAIL:
        return user.email
    return list(PushSubscription.objects.filter(user=user).values_list("subscription_id", flat=True))


def send_one(template, user, context, recipient=None, is_test=False):
    """Send a single template, log the outcome and return the NotificationLog."""
    channel = template.channel
    recipient = recipient if recipient else resolve_recipient(channel, user)
    shown = ",".join(recipient) if isinstance(recipient, list) else (recipient or "")
    try:
        detail = get_provider(channel).send(template, recipient, context)
        status = LogStatus.SENT
    except ProviderError as exc:
        detail, status = str(exc), LogStatus.FAILED
    except Exception as exc:  # network errors etc. must never break the website flow
        logger.exception("Unexpected error sending %s", template)
        detail, status = f"Unexpected error: {exc}", LogStatus.FAILED
    return NotificationLog.objects.create(
        trigger=template.trigger, template=template, user=user, channel=channel,
        recipient=shown[:255], status=status, detail=detail[:2000], is_test=is_test,
    )


def _run(trigger_key, user, extra):
    close_old_connections()
    try:
        trigger = Trigger.objects.filter(key=trigger_key, is_active=True).first()
        if not trigger:
            return
        context = build_context(user, extra)
        for template in trigger.templates.filter(is_enabled=True).select_related("trigger"):
            send_one(template, user, context)
    except Exception:
        logger.exception("fire_trigger(%s) failed", trigger_key)
    finally:
        close_old_connections()


def fire_trigger(trigger_key, user, extra=None):
    """Public entry point - call this wherever the website event happens.

    Never raises: a notification failure must not break login/logout/etc.
    """
    if settings.NOTIFICATIONS_ASYNC:
        threading.Thread(target=_run, args=(trigger_key, user, extra), daemon=True).start()
    else:
        _run(trigger_key, user, extra)
