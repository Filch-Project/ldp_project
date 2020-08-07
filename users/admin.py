from django.contrib import admin
from .models import Profile, NflPlayers, UsersNflPlayers

admin.site.register(Profile)

admin.site.register(NflPlayers)

admin.site.register(UsersNflPlayers)
