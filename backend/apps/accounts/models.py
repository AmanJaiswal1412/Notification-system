from django.conf import settings
from django.db import models
from django.utils import timezone


class Profile(models.Model):
    """Extra per-user data: phone for WhatsApp and last activity for inactivity triggers."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    phone = models.CharField(max_length=20, blank=True, help_text="International format, digits only, e.g. 919876543210")
    last_seen = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Profile({self.user})"
