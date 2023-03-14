from django.urls import path

from chat.views import private_chat_room

app_name = 'chat'
urlpatterns = [
    path('', private_chat_room, name='private-chatroom'),
]