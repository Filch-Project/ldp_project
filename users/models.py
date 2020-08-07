from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from PIL import Image

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(default='default.jpg', upload_to='profile_pics')
    numberofteamsinleague = models.PositiveIntegerField(default=8, validators=[MinValueValidator(6,message="Enter A Greater than or Equal to 6"), MaxValueValidator(18,message="Enter A Number Equal To or Less Than 18")])
    numberofplayersperteam = models.PositiveIntegerField(default=16, validators=[MinValueValidator(10,message="Enter A Greater than or Equal to 10"), MaxValueValidator(25,message="Enter A Number Equal To or Less Than 25")])
    qb = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1,message="Enter A Greater than 0"), MaxValueValidator(15,message="Enter A Number Equal To or Less Than 15")])
    rb = models.PositiveIntegerField(default=6, validators=[MinValueValidator(1,message="Enter A Greater than 0"), MaxValueValidator(25,message="Enter A Number Equal To or Less Than 25")])
    wr = models.PositiveIntegerField(default=5, validators=[MinValueValidator(1,message="Enter A Greater than 0"), MaxValueValidator(25,message="Enter A Number Equal To or Less Than 25")])
    te = models.PositiveIntegerField(default=2, validators=[MinValueValidator(1,message="Enter A Greater than 0"), MaxValueValidator(25,message="Enter A Number Equal To or Less Than 25")])
    d = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1,message="Enter A Greater than 0"), MaxValueValidator(15,message="Enter A Number Equal To or Less Than 15")])
    k = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1,message="Enter A Greater than 0"), MaxValueValidator(15,message="Enter A Number Equal To or Less Than 15")])


    def __str__(self):
        return f'{self.user.username} Profile'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        img = Image.open(self.image.path)

        if img.height > 300 or img.width > 300:
            output_size = (300, 300)
            img.thumbnail(output_size)
            img.save(self.image.path)


#https://abhishekchhibber.com/django-importing-a-csv-file-to-database-models/
class NflPlayers(models.Model):
    name = models.CharField(max_length=100)
    team = models.CharField(max_length=100)
    position = models.CharField(max_length=100)
    points = models.DecimalField(max_digits=6, decimal_places=3)

    def __str__(self):
        return self.name



class UsersNflPlayers(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    team = models.CharField(max_length=100)
    position = models.CharField(max_length=100)
    points = models.DecimalField(max_digits=6, decimal_places=3)

    def __str__(self):
        return self.name
