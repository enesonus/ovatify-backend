from django.db import models

from OVTF_Backend.models import CoreModel

import uuid


# Enum Choices
class Tempo(models.TextChoices):
    SLOW = 'S', ('Slow')
    MEDIUM = 'M', ('Medium')
    FAST = 'F', ('Fast')


class Mood(models.TextChoices):
    HAPPY = 'H', ('Happy')
    SAD = 'SA', ('Sad')
    EXCITED = 'E', ('Excited')
    RELAXED = 'R', ('Relaxed')


class RecordedEnvironment(models.TextChoices):
    INDOOR = 'I', ('Indoor')
    OUTDOOR = 'O', ('Outdoor')
    STUDIO = 'S', ('Studio')
    LIVE = 'L', ('Live')


# Models
class Genre(CoreModel):
    id = models.AutoField(primary_key=True)
    name = models.CharField(unique=True,
                            max_length=100)
    img_url = models.URLField(max_length=1000, blank=True, null=True)

    def __str__(self):
        return str(self.name)


class Song(CoreModel):
    id = models.CharField(default=uuid.uuid4,
                          primary_key=True, max_length=200)
    name = models.CharField(max_length=200)
    genres = models.ManyToManyField('Genre', through='GenreSong')
    artists = models.ManyToManyField('Artist', through='ArtistSong')
    albums = models.ManyToManyField('Album', through='AlbumSong')
    instruments = models.ManyToManyField('Instrument',
                                         through='InstrumentSong')
    release_year = models.PositiveIntegerField(blank=True)
    duration = models.DurationField()
    tempo = models.CharField(max_length=1, choices=Tempo.choices)
    mood = models.CharField(max_length=2, choices=Mood.choices)
    recorded_environment = models.CharField(
                              max_length=1,
                              choices=RecordedEnvironment.choices)
    replay_count = models.PositiveIntegerField(default=0)
    version = models.CharField(max_length=50,
                               blank=True, null=True,)
    img_url = models.URLField(max_length=1000, blank=True, null=True)

    def __str__(self):
        return str(self.name)


class Artist(CoreModel):
    id = models.CharField(max_length=1000,
                          primary_key=True)
    name = models.CharField(max_length=200)
    bio = models.TextField()
    img_url = models.URLField(max_length=1000, blank=True, null=True)

    def __str__(self):
        return str(self.name)


class Album(CoreModel):
    id = models.CharField(max_length=1000, primary_key=True)
    name = models.CharField(max_length=200)
    release_year = models.PositiveIntegerField(blank=True)
    img_url = models.URLField(max_length=1000, blank=True, null=True)

    def __str__(self):
        return str(self.name)


class Instrument(CoreModel):
    id = models.AutoField(primary_key=True)
    type = models.CharField(max_length=100)
    name = models.CharField(max_length=100)

    def __str__(self):
        return str(self.name)


class Playlist(CoreModel):
    from users.models import FriendGroup, User

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    description = models.TextField()
    songs = models.ManyToManyField('Song', through='PlaylistSong')
    user = models.ForeignKey('users.User',
                             on_delete=models.CASCADE,
                             related_name='playlists',
                             null=True, blank=True)
    friend_group = models.ForeignKey('users.FriendGroup',
                                     on_delete=models.CASCADE,
                                     related_name='playlists',
                                     null=True, blank=True)

    def __str__(self):
        return str(self.name)


# Many-to-Many Relationship Tables
class ArtistSong(CoreModel):
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE)

    class Meta:
        unique_together = (('song', 'artist'),)


class AlbumSong(CoreModel):
    album = models.ForeignKey(Album, on_delete=models.CASCADE)
    song = models.ForeignKey(Song, on_delete=models.CASCADE)

    class Meta:
        unique_together = (('album', 'song'),)


class GenreSong(CoreModel):
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE)
    song = models.ForeignKey(Song, on_delete=models.CASCADE)

    class Meta:
        unique_together = (('genre', 'song'),)


class InstrumentSong(CoreModel):
    instrument = models.ForeignKey(Instrument, on_delete=models.CASCADE)
    song = models.ForeignKey(Song, on_delete=models.CASCADE)

    class Meta:
        unique_together = (('instrument', 'song'),)


class PlaylistSong(CoreModel):
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE)
    song = models.ForeignKey(Song, on_delete=models.CASCADE)

    class Meta:
        unique_together = (('playlist', 'song'),)
