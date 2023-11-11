from django.db import models
from django.utils import timezone

from apps.songs.models import Song


# Enum Choices
class TempoChoices(models.TextChoices):
    SLOW = "S", ("Slow")
    MEDIUM = "M", ("Medium")
    FAST = "F", ("Fast")


class MoodChoices(models.TextChoices):
    HAPPY = "H", ("Happy")
    SAD = "SA", ("Sad")
    EXCITED = "E", ("Excited")
    RELAXED = "R", ("Relaxed")


class RecommendedEnvironmentChoices(models.TextChoices):
    INDOOR = "I", ("Indoor")
    OUTDOOR = "O", ("Outdoor")
    STUDIO = "S", ("Studio")
    LIVE = "L", ("Live")


# Models
class User(models.Model):
    firebase_uid = models.CharField(max_length=200, primary_key=True)

    username = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField()

    def __str__(self):
        return str(self.username)


class UserSongRating(models.Model):
    rating_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    rating = models.DecimalField(max_digits=4, decimal_places=2)
    date_rated = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.__str__()} - {self.song.__str__()}"


class UserPreferences(models.Model):
    preference_id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    data_processing_consent = models.BooleanField()
    data_sharing_consent = models.BooleanField()

    def __str__(self):
        return f"Preferences of {self.user.__str__()}"


class Instrument(models.Model):
    instrument_id = models.AutoField(primary_key=True)
    instrument_type = models.CharField(max_length=100)
    instrument_name = models.CharField(max_length=100)

    def __str__(self):
        return str(self.instrument_name)


# Many-to-Many Relationship Tables
class Friend(models.Model):
    user = models.ForeignKey(User, related_name="user", on_delete=models.CASCADE)
    friend = models.ForeignKey(User, related_name="friend", on_delete=models.CASCADE)

    class Meta:
        unique_together = (("user", "friend"),)
