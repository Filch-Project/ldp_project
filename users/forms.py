from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Profile, UsersNflPlayers

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'password1','password2']

class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email']

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['image']

class LeagueSettingsForm(forms.ModelForm):

    class Meta:
        model = Profile
        fields = ['numberofteamsinleague','numberofplayersperteam']
        labels = {'numberofteamsinleague':'Number of Teams in League','numberofplayersperteam':'Number of Players Per Team'}

class DraftOptionsForm(forms.ModelForm):

    class Meta:
        model = Profile
        fields = ['qb','rb','wr','te','d','k']
        labels = {'qb':'Quarterbacks','rb':'Running Backs','wr':'Wide Recievers','te':'Tight Ends','d':'Defense','k':'Kickers'}


class UsersNflPlayersForm(forms.ModelForm):

    class Meta:
        model = UsersNflPlayers
        fields = ['user', 'name', 'team', 'position', 'points']
