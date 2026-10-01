from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.notifications.constants import Channel
from apps.notifications.models import Template, Trigger

TRIGGERS = [
    ("login", "Login", "User signs in on the website", None,
     {"whatsapp": "Hi {{1}}, welcome back to {{2}}!", "email": ("You logged in successfully", "Hi {{user.first_name}},\n\nYou just signed in to {{site_name}}."),
      "push": ("Welcome back!", "Good to see you again, {{user.first_name}}.")}),
    ("logout", "Logout", "User signs out", None,
     {"whatsapp": "Bye {{1}}, see you again soon on {{2}}.", "email": ("You have been signed out", "Hi {{user.first_name}},\n\nYou signed out of {{site_name}}."),
      "push": ("Signed out", "See you soon, {{user.first_name}}.")}),
    ("inactive_1_day", "Not logged in for 1 day", "User has not visited for 24 hours", 1, {}),
    ("inactive_1_week", "Not logged in for 1 week", "User has not visited for 7 days", 7, {}),
    ("password_reset", "Password reset", "User asks to reset password", None, {}),
]


class Command(BaseCommand):
    help = "Create the admin user, default triggers and (for login/logout) starter templates. Idempotent."

    def handle(self, *args, **opts):
        self._admin()
        for key, name, desc, days, tpls in TRIGGERS:
            trig, _ = Trigger.objects.get_or_create(key=key, defaults={"name": name, "description": desc, "inactivity_days": days})
            for channel, content in tpls.items():
                defaults = {"name": f"{name} - {channel}", "is_enabled": False}
                if channel == Channel.WHATSAPP:
                    defaults.update(body=content, variable_mapping={"1": "user.first_name", "2": "site_name"},
                                    wa_template_name="hello_world" if key == "login" else "")
                elif channel == Channel.EMAIL:
                    defaults.update(subject=content[0], body=content[1])
                else:
                    defaults.update(title=content[0], body=content[1])
                Template.objects.get_or_create(trigger=trig, channel=channel, defaults=defaults)
        self.stdout.write(self.style.SUCCESS("Seeded triggers and starter templates."))

    def _admin(self):
        import os
        User = get_user_model()
        username = os.getenv("ADMIN_USERNAME", "admin")
        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(
                username, os.getenv("ADMIN_EMAIL", "admin@example.com"), os.getenv("ADMIN_PASSWORD", "admin12345"))
            self.stdout.write(f"Created admin user '{username}'.")
