from django.db.models import Prefetch
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .constants import Channel
from .models import NotificationLog, PushSubscription, Template, Trigger
from .providers import get_provider
from .providers.base import ProviderError
from .serializers import (NotificationLogSerializer, PushSubscriptionSerializer,
                          TemplateSerializer, TriggerSerializer)
from .services.dispatcher import resolve_recipient, send_one
from .services.rendering import AVAILABLE_VARIABLES, build_context


class TriggerViewSet(viewsets.ModelViewSet):
    """Admin matrix rows. GET /admin/triggers/ returns each trigger with its 3 channel cells."""

    permission_classes = [IsAdminUser]
    serializer_class = TriggerSerializer

    def get_queryset(self):
        return Trigger.objects.prefetch_related(Prefetch("templates", queryset=Template.objects.select_related("trigger")))


class TemplateViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    serializer_class = TemplateSerializer
    queryset = Template.objects.select_related("trigger")

    @action(detail=True, methods=["post"])
    def toggle(self, request, pk=None):
        """Turn the channel on/off for this trigger."""
        tpl = self.get_object()
        tpl.is_enabled = bool(request.data.get("is_enabled", not tpl.is_enabled))
        tpl.save(update_fields=["is_enabled", "updated_at"])
        return Response(self.get_serializer(tpl).data)

    @action(detail=True, methods=["post"])
    def test(self, request, pk=None):
        """Test send. Optional body: {"recipient": "<phone or email>"}; defaults to the admin's own contact details."""
        tpl = self.get_object()
        override = (request.data.get("recipient") or "").strip() or None
        context = build_context(request.user)
        log = send_one(tpl, request.user, context, recipient=override, is_test=True)
        code = status.HTTP_200_OK if log.status == "sent" else status.HTTP_502_BAD_GATEWAY
        return Response(NotificationLogSerializer(log).data, status=code)

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        """WhatsApp only: submit the template to Meta for approval."""
        return self._provider_call(self.get_object(), "submit_template")

    @action(detail=True, methods=["post"])
    def sync(self, request, pk=None):
        """WhatsApp only: pull approval status from Meta."""
        return self._provider_call(self.get_object(), "sync_template")

    # helpers
    def _provider_call(self, tpl, method):
        if tpl.channel != Channel.WHATSAPP:
            return Response({"detail": "Only WhatsApp templates need approval."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            getattr(get_provider(Channel.WHATSAPP), method)(tpl)
        except ProviderError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        tpl.refresh_from_db()
        return Response(self.get_serializer(tpl).data)


class LogViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAdminUser]
    serializer_class = NotificationLogSerializer

    def get_queryset(self):
        qs = NotificationLog.objects.select_related("trigger", "user")
        return qs[:200]


class VariablesView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        return Response(AVAILABLE_VARIABLES)


class PushSubscribeView(APIView):
    """Called by the browser after OneSignal gives it a subscription id."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        ser = PushSubscriptionSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        PushSubscription.objects.update_or_create(
            subscription_id=ser.validated_data["subscription_id"], defaults={"user": request.user}
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get(self, request):
        return Response({"subscribed": bool(resolve_recipient(Channel.PUSH, request.user))})
