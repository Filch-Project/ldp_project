from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from users.models import Profile
import datetime

now = datetime.datetime.now()

class DraftPosition(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    draftposition = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1,message="Enter A Greater than or Equal to 1"), MaxValueValidator(40,message="Enter A Number Equal To or Less Than 40")])

class NflPlayerPositions(models.Model):
    position = models.CharField(max_length=2)

    #this makes the name appear in the admin panel
    def __str__(self):
        return self.position

class NflTeams(models.Model):
    nflteams = models.CharField(max_length=3)

    def __str__(self):
        return self.nflteams

class PickedPlayers(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    draftround = models.IntegerField()
    season = models.IntegerField(default=now.year)
    rosterteam = models.IntegerField() #keep track of what players are assigned to what team
    name = models.CharField(max_length=100)
    team = models.CharField(max_length=3)
    position =models.CharField(max_length=3)
    points = models.DecimalField(default=000.000, max_digits=6, decimal_places=3)

    def __str__(self):
        return str("User: ") + str(self.user) + str("  |Draft Round: ") + str(self.draftround) + str("  |Draftee: ") + str(self.team)
