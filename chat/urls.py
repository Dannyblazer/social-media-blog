from django.urls import path

from chat.views import chatroom

app_name = 'chat'
urlpatterns = [
    path('<str:chat_box_name>/', chatroom, name='chatroom'),
]