from django.db import IntegrityError
from django.test import TestCase
from songs.models import Song, Genre, Artist, Album, Instrument, Tempo, Mood, RecordedEnvironment
import uuid
from datetime import timedelta


class SongModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Set up non-modified objects used by all test methods
        cls.genre = Genre.objects.create(name="Rock")
        cls.artist = Artist.objects.create(id="artist1", name="Artist 1", bio="Artist Bio")
        cls.album = Album.objects.create(id="album1", name="Album 1", release_year=2020)
        cls.instrument = Instrument.objects.create(type="String", name="Guitar")
        cls.song = Song.objects.create(
            id=uuid.uuid4(),
            name="Test Song",
            release_year=2020,
            duration=timedelta(minutes=3, seconds=30),
            tempo=Tempo.MEDIUM,
            mood=Mood.HAPPY,
            recorded_environment=RecordedEnvironment.STUDIO,
            replay_count=100,
            version="1.0"
        )

        # Creating Many-to-Many relationships
        cls.song.genres.add(cls.genre)
        cls.song.artists.add(cls.artist)
        cls.song.albums.add(cls.album)
        cls.song.instruments.add(cls.instrument)

    def test_song_creation(self):
        self.assertEqual(self.song.name, "Test Song")
        self.assertEqual(self.song.release_year, 2020)
        self.assertEqual(self.song.duration, timedelta(minutes=3, seconds=30))
        self.assertEqual(self.song.tempo, Tempo.MEDIUM)
        self.assertEqual(self.song.mood, Mood.HAPPY)
        self.assertEqual(self.song.recorded_environment, RecordedEnvironment.STUDIO)
        self.assertEqual(self.song.replay_count, 100)
        self.assertEqual(self.song.version, "1.0")

    def test_song_genre_relationship(self):
        self.assertIn(self.genre, self.song.genres.all())

    def test_song_artist_relationship(self):
        self.assertIn(self.artist, self.song.artists.all())

    def test_song_album_relationship(self):
        self.assertIn(self.album, self.song.albums.all())

    def test_song_instrument_relationship(self):
        self.assertIn(self.instrument, self.song.instruments.all())

    def test_song_string_representation(self):
        self.assertEqual(str(self.song), self.song.name)

# Additional tests can be added for other models in a similar manner.


class GenreModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.genre = Genre.objects.create(name="Jazz")

    def test_genre_creation(self):
        self.assertEqual(self.genre.name, "Jazz")

    def test_genre_string_representation(self):
        self.assertEqual(str(self.genre), "Jazz")

    def test_unique_genre_name(self):
        with self.assertRaises(IntegrityError):
            Genre.objects.create(name="Jazz")

    def test_update_genre(self):
        self.genre.name = "Pop"
        self.genre.save()
        self.genre.refresh_from_db()
        self.assertEqual(self.genre.name, "Pop")

    def test_delete_genre(self):
        genre_id = self.genre.id
        Genre.objects.filter(id=genre_id).delete()
        self.assertFalse(Genre.objects.filter(id=genre_id).exists())


class ArtistModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.artist = Artist.objects.create(id="artist1", name="Artist 1", bio="Another Artist Bio")

    def test_artist_creation(self):
        self.assertEqual(self.artist.name, "Artist 1")
        self.assertEqual(self.artist.bio, "Another Artist Bio")

    def test_artist_string_representation(self):
        self.assertEqual(str(self.artist), "Artist 1")

    def test_update_artist(self):
        self.artist.name = "Updated Artist 1"
        self.artist.save()
        self.artist.refresh_from_db()
        self.assertEqual(self.artist.name, "Updated Artist 1")

    def test_delete_artist(self):
        artist_id = self.artist.id
        Artist.objects.filter(id=artist_id).delete()
        self.assertFalse(Artist.objects.filter(id=artist_id).exists())

class AlbumModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.album = Album.objects.create(id="album1", name="Album 1", release_year=2021)

    def test_album_creation(self):
        self.assertEqual(self.album.name, "Album 1")
        self.assertEqual(self.album.release_year, 2021)

    def test_album_string_representation(self):
        self.assertEqual(str(self.album), "Album 1")

    def test_update_album(self):
        self.album.name = "Updated Album 1"
        self.album.save()
        self.album.refresh_from_db()
        self.assertEqual(self.album.name, "Updated Album 1")

    def test_delete_album(self):
        album_id = self.album.id
        Album.objects.filter(id=album_id).delete()
        self.assertFalse(Album.objects.filter(id=album_id).exists())


class InstrumentModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.instrument = Instrument.objects.create(type="Wind", name="Saxophone")

    def test_instrument_creation(self):
        self.assertEqual(self.instrument.type, "Wind")
        self.assertEqual(self.instrument.name, "Saxophone")

    def test_instrument_string_representation(self):
        self.assertEqual(str(self.instrument), "Saxophone")

    def test_update_instrument(self):
        self.instrument.name = "Electric Drums"
        self.instrument.type = "Percussion"
        self.instrument.save()
        self.instrument.refresh_from_db()
        self.assertEqual(self.instrument.name, "Electric Drums")

    def test_delete_instrument(self):
        instrument_id = self.instrument.id
        Instrument.objects.filter(id=instrument_id).delete()
        self.assertFalse(Instrument.objects.filter(id=instrument_id).exists())
