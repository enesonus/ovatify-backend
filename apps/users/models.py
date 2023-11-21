from django.db import models
from django.utils import timezone
from OVTF_Backend.models import CoreModel

from songs.models import Song


# Models
class User(CoreModel):
    id = models.CharField(max_length=200, primary_key=True)

    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    img_url = models.URLField(max_length=300, blank=True, null=True)
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField()
    user_preferences = models.OneToOneField("UserPreferences",
                                            related_name='preferences',
                                            on_delete=models.CASCADE,
                                            null=True,)
    friends = models.ManyToManyField("self", through="Friend",
                                     symmetrical=True,
                                     through_fields=("user", "friend"))

    def __str__(self):
        return str(self.username)


class UserSongRating(CoreModel):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    rating = models.DecimalField(max_digits=4, decimal_places=2)

    def __str__(self):
        return f"{self.user.__str__()} - {self.song.__str__()}"


class UserPreferences(CoreModel):
    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    data_processing_consent = models.BooleanField()
    data_sharing_consent = models.BooleanField()

    def __str__(self):
        return f"Preferences of {self.user.__str__()}"


# Many-to-Many Relationship Tables
class Friend(CoreModel):
    user = models.ForeignKey(User, related_name="user", on_delete=models.CASCADE)
    friend = models.ForeignKey(User, related_name="friend", on_delete=models.CASCADE)

    class Meta:
        unique_together = (("user", "friend"),)


class FriendGroup(CoreModel):
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=500,
                                   blank=True, null=True)
    img_url = models.URLField(max_length=300,
                              blank=True, null=True)
    friends = models.ManyToManyField(User, related_name='friend_groups')
    # Do not forget to add created_by(this field is in CoreModel) to this model while creating it 

    def __str__(self):
        return self.name
