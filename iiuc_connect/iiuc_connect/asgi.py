# iiuc_connect/asgi.py
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
import notification.routing

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "iiuc_connect.settings")

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": URLRouter(
        notification.routing.websocket_urlpatterns
    ),
})
