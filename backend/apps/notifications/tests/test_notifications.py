from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.notifications.models import NotificationLog, PushSubscription, Template, Trigger
from apps.notifications.services.rendering import ordered_values, render_text

User = get_user_model()


@override_settings(NOTIFICATIONS_ASYNC=False)
class NotificationFlowTests(TestCase):
    def setUp(self):
        call_command("seed_defaults", verbosity=0)
        self.client = APIClient()
        self.user = User.objects.create_user("bob", "bob@example.com", "secret12", first_name="Bob")
        self.user.profile.phone = "919999999999"
        self.user.profile.save()
        PushSubscription.objects.create(user=self.user, subscription_id="sub-1")
        self.admin = User.objects.get(username="admin")

    def _auth(self, user):
        from rest_framework.authtoken.models import Token
        token, _ = Token.objects.get_or_create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    # ---- rendering ----
    def test_render_with_mapping(self):
        ctx = {"user.first_name": "Bob", "site_name": "X"}
        self.assertEqual(render_text("Hi {{1}} on {{ 2 }}", {"1": "user.first_name", "2": "site_name"}, ctx), "Hi Bob on X")
        self.assertEqual(render_text("Hi {{user.first_name}}", {}, ctx), "Hi Bob")
        self.assertEqual(ordered_values("{{a}} {{b}} {{a}}", {"a": "site_name", "b": "user.first_name"}, ctx), ["X", "Bob"])

    # ---- firing ----
    @mock.patch("requests.post")
    def test_login_fires_all_enabled_channels(self, post):
        def fake(url, **kw):
            if "graph.facebook" in url:
                return mock.Mock(ok=True, json=lambda: {"messages": [{"id": "wamid.1"}]})
            if "postmark" in url:
                return mock.Mock(ok=True, json=lambda: {"MessageID": "m1"})
            return mock.Mock(ok=True, json=lambda: {"id": "n1"})
        post.side_effect = fake
        Template.objects.filter(trigger__key="login").update(is_enabled=True)
        with override_settings(
            WHATSAPP={"ACCESS_TOKEN": "t", "PHONE_NUMBER_ID": "p", "BUSINESS_ACCOUNT_ID": "", "API_VERSION": "v21.0"},
            EMAIL_CONFIG={"postmark": {"token": "t", "from_email": "a@b.c"}, "brevo": {}, "resend": {}},
            ONESIGNAL={"APP_ID": "a", "REST_API_KEY": "k"},
        ):
            res = self.client.post("/api/auth/login/", {"username": "bob", "password": "secret12"}, format="json")
        self.assertEqual(res.status_code, 200)
        logs = NotificationLog.objects.filter(trigger__key="login")
        self.assertEqual(sorted(logs.values_list("channel", flat=True)), ["email", "push", "whatsapp"])
        self.assertTrue(all(l.status == "sent" for l in logs), [l.detail for l in logs])
        calls = {c.args[0]: c.kwargs["json"] for c in post.call_args_list}
        self.assertEqual(calls["https://api.postmarkapp.com/email"]["To"], "bob@example.com")
        self.assertEqual(calls["https://api.onesignal.com/notifications"]["include_subscription_ids"], ["sub-1"])
        wa_payload = next(v for k, v in calls.items() if "graph.facebook" in k)
        self.assertEqual(wa_payload["to"], "919999999999")

    def test_disabled_channel_is_not_sent(self):
        res = self.client.post("/api/auth/login/", {"username": "bob", "password": "secret12"}, format="json")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(NotificationLog.objects.count(), 0)

    def test_logout_fires_trigger_and_provider_failure_does_not_break_request(self):
        Template.objects.filter(trigger__key="logout", channel="email").update(is_enabled=True)
        self._auth(self.user)
        res = self.client.post("/api/auth/logout/")
        self.assertEqual(res.status_code, 204)
        log = NotificationLog.objects.get()
        self.assertEqual((log.status, log.channel), ("failed", "email"))  # no keys configured

    # ---- admin API ----
    def test_admin_only(self):
        self._auth(self.user)
        self.assertEqual(self.client.get("/api/admin/triggers/").status_code, 403)

    def test_matrix_shape_and_toggle(self):
        self._auth(self.admin)
        rows = self.client.get("/api/admin/triggers/").json()
        login = next(r for r in rows if r["key"] == "login")
        self.assertEqual(set(login["cells"]), {"whatsapp", "email", "push"})
        tid = login["cells"]["email"]["id"]
        res = self.client.post(f"/api/admin/templates/{tid}/toggle/", {"is_enabled": True}, format="json")
        self.assertTrue(res.json()["is_enabled"])

    def test_create_template_validation(self):
        self._auth(self.admin)
        trig = Trigger.objects.get(key="password_reset")
        bad = self.client.post("/api/admin/templates/", {"trigger": trig.id, "channel": "email", "body": "x"}, format="json")
        self.assertEqual(bad.status_code, 400)
        ok = self.client.post("/api/admin/templates/", {"trigger": trig.id, "channel": "email", "subject": "s", "body": "x"}, format="json")
        self.assertEqual(ok.status_code, 201)
        dup = self.client.post("/api/admin/templates/", {"trigger": trig.id, "channel": "email", "subject": "s", "body": "x"}, format="json")
        self.assertEqual(dup.status_code, 400)

    @mock.patch("apps.notifications.providers.email.requests.post")
    def test_test_send_uses_recipient_override(self, post):
        post.return_value = mock.Mock(ok=True, json=lambda: {"MessageID": "m"})
        self._auth(self.admin)
        tid = Template.objects.get(trigger__key="login", channel="email").id
        with override_settings(EMAIL_CONFIG={"postmark": {"token": "t", "from_email": "a@b.c"}, "brevo": {}, "resend": {}}):
            res = self.client.post(f"/api/admin/templates/{tid}/test/", {"recipient": "me@x.com"}, format="json")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(post.call_args.kwargs["json"]["To"], "me@x.com")
        self.assertTrue(NotificationLog.objects.get().is_test)

    def test_push_subscribe(self):
        self._auth(self.user)
        res = self.client.post("/api/push/subscribe/", {"subscription_id": "sub-2"}, format="json")
        self.assertEqual(res.status_code, 204)
        self.assertTrue(PushSubscription.objects.filter(user=self.user, subscription_id="sub-2").exists())

    def test_inactivity_command(self):
        from datetime import timedelta
        from django.utils import timezone
        self.user.profile.last_seen = timezone.now() - timedelta(days=1, hours=2)
        self.user.profile.save()
        Template.objects.filter(trigger__key="inactive_1_day").delete()
        t = Trigger.objects.get(key="inactive_1_day")
        Template.objects.create(trigger=t, channel="email", subject="Miss you", body="{{days_inactive}}d", is_enabled=True)
        call_command("fire_inactivity_triggers", verbosity=0)
        self.assertEqual(NotificationLog.objects.filter(trigger=t).count(), 1)
