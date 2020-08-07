from django.contrib import admin
from .models import DraftPosition, PickedPlayers, NflPlayerPositions, NflTeams

admin.site.register(DraftPosition)
admin.site.register(PickedPlayers)
admin.site.register(NflPlayerPositions)
admin.site.register(NflTeams)
