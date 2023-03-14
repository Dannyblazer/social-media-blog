from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.conf import settings
from itertools import chain
from chat.models import PrivateChatRoom, RoomChatMessage
# Create your views here.

DEBUG = True

@login_required
def private_chat_room(request, *args, **kwargs):
    context = {}
    context['debug_mode'] = settings.DEBUG
    context['debug'] = DEBUG
    user = request.user

    #1 Find all the rooms this user is a part of
    rooms1 = PrivateChatRoom.objects.filter(user1=user, is_active = True)
    rooms2 = PrivateChatRoom.objects.filter(user2=user, is_active = True)

    #2. Merge the lists
    rooms = list(chain(rooms1, rooms2))

    """m_and_f ::: [{"message": "hey", "friend": "Blaxe"}, {"message": "what's up?", "friend": "cruz"},]"""
    m_and_f = []
    for room in rooms:
        # Figure out which user is which
        if room.user1 == user:
            friend = room.user2
        else:
            friend = room.user1
        m_and_f.append({
            "message": "", "friend": friend
        })
    context['m_and_f'] = m_and_f

    return render(request, 'chat/chat.html', context)
    