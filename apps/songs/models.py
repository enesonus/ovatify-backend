from django.db import models

from OVTF_Backend.models import CoreModel


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
    name = models.CharField(max_length=100)
    img_url = models.URLField(max_length=300, blank=True)

    def __str__(self):
        return str(self.name)


class Song(CoreModel):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200)
    release_year = models.PositiveIntegerField()
    duration = models.DurationField()
    tempo = models.CharField(max_length=1, choices=Tempo.choices)
    mood = models.CharField(max_length=2, choices=Mood.choices)
    recorded_environment = models.CharField(
                              max_length=1,
                              choices=RecordedEnvironment.choices)
    replay_count = models.PositiveIntegerField(default=0)
    version = models.CharField(max_length=50, blank=True)
    img_url = models.URLField(max_length=300, blank=True)

    def __str__(self):
        return str(self.name)


class Artist(CoreModel):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200)
    bio = models.TextField()
    img_url = models.URLField(max_length=300, blank=True)

    def __str__(self):
        return str(self.name)


class Album(CoreModel):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=200)
    release_date = models.DateField()
    img_url = models.URLField(max_length=300, blank=True)

    def __str__(self):
        return str(self.title)


class Instrument(CoreModel):
    id = models.AutoField(primary_key=True)
    type = models.CharField(max_length=100)
    name = models.CharField(max_length=100)

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
