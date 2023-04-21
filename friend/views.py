from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
import json
from users.models import Account
from .models import FriendRequest, FriendList

# Create your views here.


@login_required
def send_friend_request(request, *args, **kwargs):
    user = request.user
    payload = {}
    if request.method == "POST":
        user_id = request.POST.get("receiver_user_id")
        if user_id:
            receiver = get_object_or_404(Account, pk=user_id)
            try:
                friend_request = FriendRequest.objects.get(sender=user, receiver=receiver)
                if friend_request.is_active:
                    payload['response'] = "You already sent them a friend request."
                else:
                    friend_request.is_active = True
                    friend_request.save()
                    payload['response'] = "Friend request sent."
            except FriendRequest.DoesNotExist:
                friend_request = FriendRequest(sender=user, receiver=receiver, is_active=True)
                friend_request.save()
                payload['response'] = "Friend request sent."
        else:
            payload['response'] = "Unable to send a friend request."
    else:
        payload['response'] = "Invalid request method."
    return HttpResponse(json.dumps(payload), content_type="application/json")


def friend_requests(request, *args, **kwargs):
    user = request.user
    context = {}
    if user.is_authenticated:
        user_id = kwargs.get("user_id")
        acct = Account.objects.get(pk=user_id)
        if acct == user:
            friend_requests = FriendRequest.objects.filter(receiver=user, is_active=True)
            context['friend_requests'] = friend_requests
        else:
            return HttpResponse("You're trying to do shit, Fuc* off!")
    else:
        return redirect("users:must_authenticate")
    return render(request, "friend/friend_requests.html", context)


def accept_friend_request(request, *args, **kwargs):
    user = request.user
    payload = {}
    if request.method == "GET" and user.is_authenticated:
        friend_request_id = kwargs.get("friend_request_id")
        if friend_request_id:
            friend_request = FriendRequest.objects.get(pk=friend_request_id)
            # Confirm that is the correct request
            if friend_request.receiver == user:
                if friend_request:
                    # found the request. Now accept it
                    friend_request.accept()
                    payload['response'] = "Friend request accepted."
                else:
                    payload['response'] = "Something went wrong."
            else:
                payload['response'] = "This is not your request to accept."
        else:
            payload['response'] = "Unable to accept that friend request."
    else:
        payload['response'] = "You must authenticate to accept a friend request."
    return HttpResponse(json.dumps(payload), content_type="application/json")

def remove_friend(request, *args, **kwargs):
    user = request.user
    payload = {}
    if request.method == "POST" and user.is_authenticated:
        user_id = request.POST["receiver_user_id"]
        if user_id:
            try:
                removee = Account.objects.get(id=user_id)
                friend_list = FriendList.objects.get(user=user.pk)
                friend_list.unfriend(removee)
                payload['response'] = "Successfully removed that friend."
            except Exception as e:
                payload['response'] = f"Something went wrong: {str(e)}."
        else:
            payload['response'] = f"There was an error. Unable to remove that friend."
    else:
        payload['response'] = "You must be authenticated to remove a friend."
    return HttpResponse(json.dumps(payload), content_type="application/json")


def decline_friend_request(request, *args, **kwargs):
    user = request.user
    payload = {}
    if request.method == "GET" and user.is_authenticated:
        friend_request_id = kwargs.get("friend_request_id")
        if friend_request_id:
            friend_request = FriendRequest.objects.get(pk=friend_request_id)
            if friend_request:
                if friend_request.receiver == user:
                    friend_request.decline()
                    payload['response'] = "Friend request declined."
                else:
                    payload['response'] = "Unable to decline friend request."
            else:
                payload['response'] = "You're unable to decline the request."
        else:
            payload['response'] = "Something really went wrong."
    else:
        payload['response'] = "You must be authenticated to decline a friend request."
    return HttpResponse(json.dumps(payload), content_type="application/json")


def cancel_friend_request(request, *args, **kwargs):
    user = request.user
    payload = {}
    if request.method == 'POST' and user.is_authenticated:
        user_id = request.POST["receiver_user_id"]
        if user_id:
            receiver = Account.objects.get(pk=user_id)
            try:
                friend_requests = FriendRequest.objects.filter(sender=user, receiver=receiver, is_active=True)
            except Exception as e:
                payload['response'] = "Unable to cancel this request, request does not exist"
            # There should only be a single active friend request at any given time. Cancel them all just in case.
            if len(friend_requests) > 1:
                for request in friend_requests:
                    request.cancel()
                payload['response'] = "Friend request cancelled."
            else:
                # found the request, now cancel
                friend_requests.first().cancel()
                payload['response'] = "Friend request cancelled."
        else:
            payload['response'] = "Unable to cancel the request."
    else:
        payload['response'] = "You must be authenticated to cancel a request."
    return HttpResponse(json.dumps(payload), content_type="application/json")

def view_friends(request, *args, **kwargs):
    user = request.user
    context = {}
    if request.method == 'GET' and user.is_authenticated:
        user_id = kwargs.get("friend_id")
        if user_id:
            try:
                account = Account.objects.get(pk=user_id)
                friend_list = FriendList.objects.get(user=account)
                context['friends'] = friend_list.friends.all()
            except FriendList.DoesNotExist:
                return HttpResponse("Account/Friend list does not exixt")
        else:
            return HttpResponse("Invalid User")
    else:
        return redirect('users:must_authenticate')
    return render(request, "friend/friend_list.html", context)

