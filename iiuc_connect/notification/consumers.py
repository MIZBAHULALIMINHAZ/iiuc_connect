import json
from channels.generic.websocket import AsyncWebsocketConsumer
from accounts.models import User
import jwt
from django.conf import settings
from urllib.parse import parse_qs
from bson import ObjectId


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Extract token from query params
        query = parse_qs(self.scope["query_string"].decode())
        token = query.get("token", [None])[0]

        self.user = None

        # Verify token
        if token:
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
                user_id = payload.get("user_id")
                self.user = User.objects(id=ObjectId(user_id)).first()
            except Exception:
                await self.close()
                return

        if not self.user:
            await self.close()
            return

        # Each user gets personal notification group
        self.group_name = f"notifications_{self.user.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)

        # Admin gets extra "inactive users" live update group
        if self.user.role == "admin":
            await self.channel_layer.group_add("admin_inactive_users", self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

        if self.user and self.user.role == "admin":
            await self.channel_layer.group_discard("admin_inactive_users", self.channel_name)

    # User-specific notifications
    async def send_notification(self, event):
        await self.send(text_data=json.dumps({
            "type": "user_notification",
            "data": event["data"]
        }))

    # Admin-only events for inactive users
    async def inactive_user_event(self, event):
        await self.send(json.dumps({
            "type": "inactive_user",
            "user": event["data"]
        }))
