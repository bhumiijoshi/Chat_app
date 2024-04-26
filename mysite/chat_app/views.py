from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from chat_app.models import Room

@login_required
def index(request):
    return render(request, "chat_app/index.html",{
        'rooms': Room.objects.all(),
    })

@login_required
def room(request, room_name):
    if Room.objects.filter(name=room_name).exists():
        chat_room = Room.objects.get(name=room_name)
    else:
        chat_room= Room.objects.create(name=room_name)
 
    return render(request, "chat_app/room.html", {
        'room': chat_room,
    })
