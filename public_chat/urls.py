from django.urls import path

from .views import room

app_name = 'public_chat'
urlpatterns = [
    path("", room, name="room"),

]