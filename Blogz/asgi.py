import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application
from django.urls import re_path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Blogz.settings")
# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
django_asgi_app = get_asgi_application()

from public_chat.consumers import PublicChatConsumer
from chat.consumers import ChatConsumer
from notification.consumers import NotificationConsumer
application = ProtocolTypeRouter({
    # Django's ASGI application to handle traditional HTTP requests
    "http": django_asgi_app,

    # WebSocket chat handler
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter([
                re_path(r"chat/(?P<room_name>\w+)/$", ChatConsumer.as_asgi()),
                re_path(r"public_chat/$", PublicChatConsumer.as_asgi()),
                re_path(r"notification/$", NotificationConsumer.as_asgi()),
            ])
        )
    ),
})