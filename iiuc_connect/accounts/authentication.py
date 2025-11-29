# accounts/authentication.py
import jwt
from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions
from django.conf import settings
from accounts.models import User

class JWTAuthentication(BaseAuthentication):
    keyword = "Bearer"

    def authenticate(self, request):
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header:
            return None

        parts = auth_header.split()
        if len(parts) != 2 or parts[0] != self.keyword:
            return None

        token = parts[1]
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed("Token expired")
        except Exception:
            raise exceptions.AuthenticationFailed("Invalid token")

        user_id = payload.get("user_id")
        user = User.objects(id=user_id).first()
        if not user:
            raise exceptions.AuthenticationFailed("User not found")

        return (user, token)


import jwt
from django.conf import settings
from rest_framework import authentication, exceptions
from event.models import GuestUser

class GuestJWTAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        token = auth_header.replace("Bearer ", "")
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed("Token expired")
        except jwt.InvalidTokenError:
            raise exceptions.AuthenticationFailed("Invalid token")

        guest_id = payload.get("guest_id")
        try:
            guest = GuestUser.objects.get(id=guest_id)
        except GuestUser.DoesNotExist:
            raise exceptions.AuthenticationFailed("Guest not found")

        return (guest, None)
