from django.shortcuts import render
from django.conf import settings

# Create your views here.

def room(request):
    context = {}
    context['debug_mode'] = settings.DEBUG
    return render(request, "public_chat/room.html", context)
