from django.contrib.auth import authenticate, get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notifications.services.dispatcher import fire_trigger

from .models import Profile
from .serializers import LoginSerializer, PhoneSerializer, RegisterSerializer, UserSerializer


def _touch(user):
    Profile.objects.update_or_create(user=user, defaults={"last_seen": timezone.now()})


class RegisterView(APIView):
    permission_classes = [AllowAny]
    authentication_classes: list = []

    def post(self, request):
        ser = RegisterSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response({"token": token.key, "user": UserSerializer(user).data}, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes: list = []

    def post(self, request):
        ser = LoginSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = authenticate(username=ser.validated_data["username"], password=ser.validated_data["password"])
        if not user:
            return Response({"detail": "Invalid username or password."}, status=status.HTTP_400_BAD_REQUEST)
        token, _ = Token.objects.get_or_create(user=user)
        _touch(user)
        fire_trigger("login", user)  # <-- website event -> notifications
        return Response({"token": token.key, "user": UserSerializer(user).data})


class LogoutView(APIView):
    def post(self, request):
        user = request.user
        fire_trigger("logout", user)  # <-- website event -> notifications
        Token.objects.filter(user=user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    def get(self, request):
        _touch(request.user)
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        ser = PhoneSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        request.user.profile.phone = ser.validated_data["phone"]
        request.user.profile.save()
        return Response(UserSerializer(request.user).data)


class PasswordResetRequestView(APIView):
    """Demo endpoint for the `password_reset` trigger (does not actually reset anything)."""

    permission_classes = [AllowAny]
    authentication_classes: list = []

    def post(self, request):
        User = get_user_model()
        user = User.objects.filter(username__iexact=request.data.get("username", "")).first()
        if user:
            fire_trigger("password_reset", user, {"reset_link": "https://example.com/reset/demo-token"})
        return Response({"detail": "If the account exists, a notification was sent."})
