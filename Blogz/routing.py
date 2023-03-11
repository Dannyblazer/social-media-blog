from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRoute, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.urls import path
from public_chat.consumers import PublicChatConsumer

application = ProtocolTypeRoute({
    'websocket': AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter([
                path("public_chat/<room_id>/", PublicChatConsumer),
            ])
        ),
    ),
})