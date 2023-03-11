from django.shortcuts import render
from django.template import loader
from django.http import HttpResponse
# Create your views here.

def chatroom(request, chat_box_name):
    
    return render(request, 'chat/chat.html', context={'chat_box_name': chat_box_name})
    