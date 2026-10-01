from django.contrib import admin

from .models import NotificationLog, PushSubscription, Template, Trigger

admin.site.register(Trigger)
admin.site.register(Template)
admin.site.register(PushSubscription)
admin.site.register(NotificationLog)
