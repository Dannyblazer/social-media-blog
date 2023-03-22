from django.urls import path

from chat.views import private_chat_room, create_or_return_private_chat

app_name = 'chat'
urlpatterns = [
    path('', private_chat_room, name='private-chatroom'),
    path('create_or_return_private_chat/', create_or_return_private_chat, name='create-or-return-private-chat'),
]