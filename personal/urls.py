from django.urls import path
from .views import news_articles, public_chat
app_name = "personal"
urlpatterns = [
    path('', news_articles, name="new_articles"),
    path('public_chat/', public_chat, name="public_chat"),
]
