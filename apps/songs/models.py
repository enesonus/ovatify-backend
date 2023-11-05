from django.db import models


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


class RecommendedEnvironment(models.TextChoices):
    INDOOR = 'I', ('Indoor')
    OUTDOOR = 'O', ('Outdoor')
    STUDIO = 'S', ('Studio')
    LIVE = 'L', ('Live')


# Models
class Genre(models.Model):
    genre_id = models.AutoField(primary_key=True)
    genre_name = models.CharField(max_length=100)

    def __str__(self):
        return str(self.genre_name)


class Song(models.Model):
    song_id = models.AutoField(primary_key=True)
    track_name = models.CharField(max_length=200)
    release_year = models.PositiveIntegerField()
    length = models.DurationField()
    tempo = models.CharField(max_length=1, choices=Tempo.choices)
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE)
    mood = models.CharField(max_length=2, choices=Mood.choices)
    recommended_environment = models.CharField(
                              max_length=1,
                              choices=RecommendedEnvironment.choices)
    duration = models.PositiveIntegerField()
    replay_count = models.PositiveIntegerField(default=0)
    version = models.CharField(max_length=50)

    def __str__(self):
        return str(self.track_name)


class Artist(models.Model):
    artist_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200)
    bio = models.TextField()

    def __str__(self):
        return str(self.name)


class Album(models.Model):
    album_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=200)
    release_date = models.DateField()

    def __str__(self):
        return str(self.title)


class Instrument(models.Model):
    instrument_id = models.AutoField(primary_key=True)
    instrument_type = models.CharField(max_length=100)
    instrument_name = models.CharField(max_length=100)

    def __str__(self):
        return str(self.instrument_name)


# Many-to-Many Relationship Tables
class SongArtist(models.Model):
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE)

    class Meta:
        unique_together = (('song', 'artist'),)


class AlbumSong(models.Model):
    album = models.ForeignKey(Album, on_delete=models.CASCADE)
    song = models.ForeignKey(Song, on_delete=models.CASCADE)

    class Meta:
        unique_together = (('album', 'song'),)


class GenreSong(models.Model):
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE)
    song = models.ForeignKey(Song, on_delete=models.CASCADE)

    class Meta:
        unique_together = (('genre', 'song'),)


class InstrumentSong(models.Model):
    instrument = models.ForeignKey(Instrument, on_delete=models.CASCADE)
    song = models.ForeignKey(Song, on_delete=models.CASCADE)

    class Meta:
        unique_together = (('instrument', 'song'),)
