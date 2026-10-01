from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("admin/triggers", views.TriggerViewSet, basename="trigger")
router.register("admin/templates", views.TemplateViewSet, basename="template")
router.register("admin/logs", views.LogViewSet, basename="log")

urlpatterns = [
    path("admin/variables/", views.VariablesView.as_view()),
    path("push/subscribe/", views.PushSubscribeView.as_view()),
    path("", include(router.urls)),
]
