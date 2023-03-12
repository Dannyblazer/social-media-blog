# chat/routing.py
from django.urls import re_path

from public_chat.consumers import PublicChatConsumer

websocket_urlpatterns = [
    re_path(r"public_chat/$", PublicChatConsumer.as_asgi()),
]