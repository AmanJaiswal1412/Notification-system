from django.conf import settings
from django.db import models

from .constants import ApprovalStatus, Channel, LogStatus


class Trigger(models.Model):
    """Anything on the website that should cause notifications (one row in the admin table)."""

    key = models.SlugField(unique=True, help_text="Code identifier used by fire_trigger('<key>', user)")
    name = models.CharField(max_length=120)
    description = models.CharField(max_length=255, blank=True)
    inactivity_days = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="For inactivity triggers: fire after this many days without a visit.",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.name


class Template(models.Model):
    """One template = one cell in the admin matrix (trigger x channel)."""

    trigger = models.ForeignKey(Trigger, on_delete=models.CASCADE, related_name="templates")
    channel = models.CharField(max_length=20, choices=Channel.CHOICES)
    name = models.CharField(max_length=120, blank=True)
    is_enabled = models.BooleanField(default=False)

    # Content. `subject` is email only, `title` is push only; `body` is used by every channel.
    subject = models.CharField(max_length=255, blank=True)
    title = models.CharField(max_length=120, blank=True)
    body = models.TextField(blank=True)
    url = models.URLField(blank=True, help_text="Push only: page opened on click")

    # Placeholder -> context key, e.g. {"1": "user.first_name"} or {"name": "user.first_name"}.
    variable_mapping = models.JSONField(default=dict, blank=True)

    # WhatsApp specifics (templates need Meta approval).
    wa_template_name = models.CharField(max_length=512, blank=True)
    wa_language = models.CharField(max_length=10, default="en_US", blank=True)
    wa_category = models.CharField(max_length=20, default="UTILITY", blank=True)
    wa_status = models.CharField(max_length=20, choices=ApprovalStatus.CHOICES, default=ApprovalStatus.DRAFT, blank=True)
    wa_external_id = models.CharField(max_length=64, blank=True)
    wa_rejection_reason = models.CharField(max_length=255, blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["trigger_id", "channel"]
        constraints = [models.UniqueConstraint(fields=["trigger", "channel"], name="one_template_per_cell")]

    def __str__(self):
        return f"{self.trigger.key}/{self.channel}"


class PushSubscription(models.Model):
    """OneSignal subscription id of a user's browser."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="push_subscriptions")
    subscription_id = models.CharField(max_length=128, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)


class NotificationLog(models.Model):
    """Audit trail of every attempted send (including test sends)."""

    trigger = models.ForeignKey(Trigger, null=True, on_delete=models.SET_NULL, related_name="logs")
    template = models.ForeignKey(Template, null=True, on_delete=models.SET_NULL, related_name="logs")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    channel = models.CharField(max_length=20, choices=Channel.CHOICES)
    recipient = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=10, choices=LogStatus.CHOICES)
    is_test = models.BooleanField(default=False)
    detail = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
