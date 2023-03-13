from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import login as dj_login, authenticate, logout
from users.forms import RegistrationForm, AccountAuthenticationForm, AccountUpdateForm, ServerRegistrationForm
from django.contrib import messages
from django.template import loader
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Account, Server
from friend.models import FriendList, FriendRequest
from django.urls import reverse
from blog.models import BlogPost
from django.conf import settings
from friend.friend_request_status import FriendRequestStatus
from friend.utils import get_friend_request_or_false
# Create your views here.

def index(request):
    context = {}
    context['is_home'] = True
    all_users = Account.objects.all()
    context['users'] = all_users
    template = loader.get_template('users/home.html')
    return HttpResponse(template.render(context, request))

def registration_view(request):
    context = {}
    if not request.user.is_authenticated:
        if request.method == "POST":
            form = RegistrationForm(request.POST)
            if form.is_valid():
                form.save()
                email = form.cleaned_data.get('email')
                raw_password = form.cleaned_data.get('password1')
                account = authenticate(email=email, password=raw_password)
                dj_login(request, account)
                return HttpResponseRedirect(reverse('home'))
            else:
                context['registration_form'] = form
        else:
            form = RegistrationForm()
            context['registration_form'] = form
        return render(request=request, template_name="users/register.html", context={"registration_form":form})
    else:
        return redirect('home')

def login_view(request):
    user = request.user
    if user.is_authenticated:
        return redirect('home')
    
    if request.POST:
        form = AccountAuthenticationForm(request.POST)
        if form.is_valid():
            email = request.POST['email']
            email.lower()
            password = request.POST['password']
            user = authenticate(email=email, password=password)

            if user:
                dj_login(request, user)
                return redirect('home')
    
    else:
        form = AccountAuthenticationForm()
    return render(request, 'users/login.html', context={'form':form})

def logout_view(request):
    logout(request)
    return redirect('home')


@login_required
def account_view(request, username):
    acct = get_object_or_404(Account, username=username)
    blog_posts = BlogPost.objects.filter(author=acct)
    server_list = Server.objects.filter(account=acct)

    # Friend list
    friend_list, created = FriendList.objects.get_or_create(user=acct)

    # Define template variables
    friends = friend_list.friends.all()
    is_self = request.user == acct
    is_friend = friends.filter(pk=request.user.pk).exists()
    request_sent = FriendRequestStatus.NO_REQUEST_SENT.value
    friend_requests = None

    if not is_self:
        if is_friend:
            request_sent = FriendRequestStatus.ALREADY_FRIENDS.value
        elif get_friend_request_or_false(sender=acct, receiver=request.user):
            request_sent = FriendRequestStatus.THEM_SENT_TO_YOU.value
            pending_friend_request_id = get_friend_request_or_false(sender=acct, receiver=request.user).id
        elif get_friend_request_or_false(sender=request.user, receiver=acct):
            request_sent = FriendRequestStatus.YOU_SENT_TO_THEM.value
        else:
            request_sent = FriendRequestStatus.NO_REQUEST_SENT.value

    if is_self:
        try:
            friend_requests = FriendRequest.objects.filter(receiver=request.user, is_active=True)
        except FriendRequest.DoesNotExist:
            pass

    context = {
        'id': acct.id,
        'is_self': is_self,
        'is_friend': is_friend,
        'friends': friends,
        'request_sent': request_sent,
        'friend_requests': friend_requests,
        'account': acct,
        'blog_posts': blog_posts,
        'server_list': server_list
    }

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'send_request':
            FriendRequest.objects.create(sender=request.user, receiver=acct)
            messages.success(request, f'Friend request sent to {acct.username}.')
            return render(request, "users/profile.html", context)

        if action == 'cancel_request':
            FriendRequest.objects.filter(sender=request.user, receiver=acct).delete()
            messages.success(request, f'Friend request to {acct.username} has been canceled.')
            return render(request, "users/profile.html", context)

        if action == 'accept_request':
            friend_request = FriendRequest.objects.get(pk=request.POST.get('request_id'))
            friend_list.add(friend_request.sender)
            friend_request.delete()
            messages.success(request, f"You are now friends with {friend_request.sender.username}.")
            return render(request, "users/profile.html", context)

        if action == 'reject_request':
            friend_request = FriendRequest.objects.get(pk=request.POST.get('request_id'))
            friend_request.delete()
            messages.success(request, f"Friend request from {friend_request.sender.username} has been rejected.")
            return render(request, "users/profile.html", context)

    return render(request, "users/profile.html", context)

def must_authenticate_view(request):
    return render(request, "users/must_authenticate.html", context={})

def server_registration_view(request):
    if not request.user.is_authenticated:
        return redirect('users:must_authenicate')

    form = ServerRegistrationForm(request.POST or None)
    context = {}
    if form.is_valid():
        obj = form.save(commit=False)
        account = Account.objects.filter(email=request.user.email).first()
        obj.account = account
        obj.save()
        form = ServerRegistrationForm()
        context["success_message"]= "Server Added"
    
    context['form'] = form
    
    return render(request, 'users/add_server.html', context)

def server_update_view(request, listz_id):
    if not request.user.is_authenticated:
        return redirect('users:must_authenticate')
    server_id = Server.objects.get(pk=listz_id)
    if request.user == server_id.account:
        context = {}
        serverz = get_object_or_404(Server, pk=listz_id)
        context['serverz'] = serverz
        return render(request, 'users/server_update_view.html', context)
    return redirect('users:must_authenticate')


def server_update(request, listz_id):
    if not request.user.is_authenticated:
        return redirect('users:must_authenticate')
    server_id = Server.objects.get(pk=listz_id)
    if request.user == server_id.account:
        context = {}
        if request.method == 'POST':
            serverz = get_object_or_404(Server, pk=listz_id)
            serverz.ip = request.POST['ip']
            serverz.port = request.POST['port']
            serverz.save()
            context['serverz'] = serverz
            context['success_message'] = "Server Updated"
            return render(request, 'users/server_update_view.html', context)
    
    else:
        context['success_message'] = "Update Failure"
        return render(request, 'users/server_update.html', context)
    
def server_delete(request, listz_id):
    if not request.user.is_authenticated:
        return redirect('users:must_authenticate')
    server_id = Server.objects.get(pk=listz_id)
    if request.user == server_id.account:
        context = {}
        serverz = get_object_or_404(Server, pk=listz_id)
        serverz.delete()
        return redirect('users:account')
    return redirect('users:must_authenticate')

def edit_account(request, *args, **kwargs):
	if not request.user.is_authenticated:
		return redirect("users:must_authenticate")
	user_id = kwargs.get("user_id")
	account = Account.objects.get(pk=user_id)
	if account.pk != request.user.pk:
		return HttpResponse("You cannot edit someone elses profile.")
	context = {}
	if request.POST:
		form = AccountUpdateForm(request.POST, request.FILES, instance=request.user)
		if form.is_valid():
			form.save()
			return redirect("users:profile", user_id=account.pk)
		else:
			form = AccountUpdateForm(request.POST, instance=request.user,
				initial={
					"user_id": account.pk,
					"email": account.email, 
					"username": account.username,
                    "first_name": account.first_name,
                    "last_name": account.last_name,
                    "bio": account.bio,
                    "role": account.role,
					"profile_image": account.profile_image,
					"hide_email": account.hide_email,
				}
			)
			context['form'] = form
	else:
		form = AccountUpdateForm(
			initial={
					"user_id": account.pk,
					"email": account.email, 
					"username": account.username,
                    "first_name": account.first_name,
                    "last_name": account.last_name,
                    "bio": account.bio,
                    "role": account.role,
					"profile_image": account.profile_image,
					"hide_email": account.hide_email,
				}
			)
		context['form'] = form
	return render(request, "users/account.html", context)


def account_search_view(request, *args, **kwargs):
    context = {}

    if request.method == 'GET':
        search_query = request.GET.get("q")
        if len(search_query) > 0:
            search_results = Account.objects.filter(
			Q(email__contains=search_query)|
			Q(username__icontains=search_query)
			).distinct()
            accounts = []
            for account in search_results:
                if request.user in account.user.friends.all():
                    accounts.append((account, True))
                else:
                    accounts.append((account, False))
            context['accounts'] = accounts
        

    return render(request, "users/search_results.html", context)
