"""Run daily (Render cron job): notifies users who were away for a trigger's inactivity_days.

A user is notified once per absence: we only fire when last_seen falls in the window
[N days, N days + 1 day) so the daily schedule never double-sends.
"""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.notifications.models import Trigger
from apps.notifications.services.dispatcher import _run


class Command(BaseCommand):
    help = "Fire inactivity triggers (not logged in for N days)."

    def handle(self, *args, **opts):
        now = timezone.now()
        User = get_user_model()
        total = 0
        for trig in Trigger.objects.filter(is_active=True, inactivity_days__isnull=False):
            upper = now - timedelta(days=trig.inactivity_days)
            lower = upper - timedelta(days=1)
            users = User.objects.filter(is_active=True, is_staff=False, profile__last_seen__lte=upper, profile__last_seen__gt=lower)
            for user in users:
                _run(trig.key, user, {"days_inactive": trig.inactivity_days})
                total += 1
        self.stdout.write(self.style.SUCCESS(f"Inactivity triggers fired for {total} user(s)."))
