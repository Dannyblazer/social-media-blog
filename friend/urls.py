from django.urls import path
from .views import send_friend_request, friend_requests, accept_friend_request, remove_friend, decline_friend_request, cancel_friend_request, view_friends

app_name = "friend"
urlpatterns = [
    path('accept_friend_request/<friend_request_id>', accept_friend_request, name="friend-request-accept"),
    path('decline_friend_request/<friend_request_id>', decline_friend_request, name="friend-request-decline"),
    path('friends/<friend_id>', view_friends, name="friends-view"),
    path('friend_remove/', remove_friend, name="remove-friend"),
    path('friend_requests/', send_friend_request, name="friend-request"),
    path('friend_request_cancel/', cancel_friend_request, name="friend-request-cancel"),
    path('friend_requests/<user_id>', friend_requests, name="friend-requests"),
]