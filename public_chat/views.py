from django.shortcuts import render
from django.conf import settings

# Create your views here.
DEBUG = False
def room(request):
    context = {}
    context['debug_mode'] = settings.DEBUG
    context['debug'] = DEBUG
    context['room_id'] = 1
    return render(request, "public_chat/room.html", context)
