from rest_framework import serializers

from .constants import Channel
from .models import NotificationLog, PushSubscription, Template, Trigger


class TemplateSerializer(serializers.ModelSerializer):
    trigger_key = serializers.CharField(source="trigger.key", read_only=True)

    class Meta:
        model = Template
        fields = [
            "id", "trigger", "trigger_key", "channel", "name", "is_enabled",
            "subject", "title", "body", "url", "variable_mapping",
            "wa_template_name", "wa_language", "wa_category", "wa_status",
            "wa_external_id", "wa_rejection_reason", "updated_at",
        ]
        read_only_fields = ["wa_status", "wa_external_id", "wa_rejection_reason", "updated_at"]

    def validate(self, attrs):
        channel = attrs.get("channel", getattr(self.instance, "channel", None))
        body = attrs.get("body", getattr(self.instance, "body", ""))
        if not (body or "").strip():
            raise serializers.ValidationError({"body": "Body is required."})
        if channel == Channel.EMAIL and not (attrs.get("subject", getattr(self.instance, "subject", "")) or "").strip():
            raise serializers.ValidationError({"subject": "Subject is required for email."})
        if channel == Channel.PUSH and not (attrs.get("title", getattr(self.instance, "title", "")) or "").strip():
            raise serializers.ValidationError({"title": "Title is required for web push."})
        return attrs


class TriggerSerializer(serializers.ModelSerializer):
    """Serialises a trigger as one matrix row: templates keyed by channel."""

    cells = serializers.SerializerMethodField()

    class Meta:
        model = Trigger
        fields = ["id", "key", "name", "description", "inactivity_days", "is_active", "cells"]

    def get_cells(self, obj):
        by_channel = {c: None for c in Channel.ALL}
        for t in obj.templates.all():
            by_channel[t.channel] = TemplateSerializer(t).data
        return by_channel


class NotificationLogSerializer(serializers.ModelSerializer):
    trigger_key = serializers.CharField(source="trigger.key", read_only=True, default=None)
    username = serializers.CharField(source="user.username", read_only=True, default=None)

    class Meta:
        model = NotificationLog
        fields = ["id", "trigger_key", "template", "username", "channel", "recipient", "status", "is_test", "detail", "created_at"]


class PushSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PushSubscription
        fields = ["subscription_id"]
