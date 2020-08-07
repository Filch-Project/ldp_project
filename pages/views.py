from django.shortcuts import render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponse
from django.views.generic import ListView, DetailView
from django.contrib.auth.models import User
from draft.models import DraftPosition, PickedPlayers
from users.models import Profile, NflPlayers, UsersNflPlayers
from . import views

import datetime
now = datetime.datetime.now()

def home(request):
    if request.user.is_authenticated:
        if DraftPosition.objects.filter(user = request.user).exists():
            players_draft_position = DraftPosition.objects.values_list('draftposition',flat=True).filter(user = request.user)
            players_draft_position = players_draft_position[0] #add default position
            myteam = PickedPlayers.objects.all().filter(user = request.user, rosterteam = players_draft_position, season=now.year)
            return render(request, 'home.html', {'title':'Home','myteam':myteam})
        else:
            return render(request, 'home.html', {'title':'Home'})
    else:
        return render(request, 'home.html', {'title':'Home'})

def about(request):
    if request.user.is_authenticated:
        if DraftPosition.objects.filter(user = request.user).exists():
            players_draft_position = DraftPosition.objects.values_list('draftposition',flat=True).filter(user = request.user)
            players_draft_position = players_draft_position[0] #add default position
            myteam = PickedPlayers.objects.all().filter(user = request.user, rosterteam = players_draft_position, season=now.year)
            return render(request, 'about.html', {'title':'About','myteam':myteam})
        else:
            return render(request, 'about.html', {'title':'About'})
    else:
        return render(request, 'about.html', {'title':'About'})

def terms(request):
    return render(request, 'terms.html', {'title':'Terms of Service'})

def privacy(request):
    return render(request, 'privacy.html', {'title':'Privacy Policy'})
