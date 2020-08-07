from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import MaxValueValidator, MinValueValidator
from django.core.exceptions import ValidationError
from .models import DraftPosition, PickedPlayers
from users.models import NflPlayers, UsersNflPlayers
import datetime

now = datetime.datetime.now()


class DraftForm(forms.ModelForm):

    class Meta:
        model = DraftPosition
        fields = ['draftposition']
        labels = {'draftposition':'What is your draft position?'}

# class DraftPosition(forms.Form):
#     draftposition = forms.CharField(label='What is your draft position?', required=True, widget=forms.Select(choices=POSITION_CHOICES))


class AutoPickPlayer(forms.Form):
    name = forms.CharField(max_length=65)
    team = forms.CharField(max_length=50)
    position = forms.CharField(max_length=2)



class ManualEnterPlayer(forms.ModelForm):

    name = forms.ModelChoiceField(queryset=UsersNflPlayers.objects.all().values_list('name', flat=True).order_by('name').distinct(), empty_label="Player")

    def __init__(self, user, *args, **kwargs):
        super(ManualEnterPlayer, self).__init__(*args, **kwargs)
        #self.fields['name'].queryset = UsersNflPlayers.objects.all().order_by('name').distinct()
        self.fields['name'].queryset = UsersNflPlayers.objects.filter(user=user).order_by('name').distinct()

    class Meta:
        model = PickedPlayers
        fields = ['name']
        labels = {'name':'Players Name'}


class SubmitPickedPlayer(forms.ModelForm):
    class Meta:
        model = PickedPlayers
        fields = ['user','draftround','rosterteam','name','team','position','points']
