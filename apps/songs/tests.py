from django.db import IntegrityError
from django.test import TestCase
from songs.models import Song, Genre, Artist, Album, Instrument, Tempo, Mood, RecordedEnvironment
import uuid
from datetime import timedelta
from django.urls import reverse
from rest_framework.test import APIClient
from users.models import User
from django.utils import timezone
import json
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

class GetAllMoodsTest(TestCase):
    def setUp(cls):
        cls.client = APIClient()
        cls.client.credentials(HTTP_AUTHORIZATION='Bearer e5e28a48-8080-11ee-b962-0242ac120002')

    def test_get_all_moods(self):
        response = self.client.get(reverse('get_all_moods'))

        self.assertEqual(response.status_code, 200)
        self.assertIn('moods', response.json())

        # Ensure that the response contains the correct moods based on Mood.choices
        expected_moods = [{'value': mood[0], 'label': mood[1]} for mood in Mood.choices]
        self.assertEqual(response.json()['moods'], expected_moods)

    def test_get_all_moods_invalid_method(self):
        response = self.client.post(reverse('get_all_moods'))

        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())
        self.assertEqual(response.json()['error'], 'Invalid method')

class GetAllTemposTest(TestCase):
    def setUp(cls):
        cls.client = APIClient()
        cls.client.credentials(HTTP_AUTHORIZATION='Bearer e5e28a48-8080-11ee-b962-0242ac120002')

    def test_get_all_tempos(self):
        response = self.client.get(reverse('get_all_tempos'))

        self.assertEqual(response.status_code, 200)
        self.assertIn('tempos', response.json())

        # Ensure that the response contains the correct tempos based on Tempo.choices
        expected_tempos = [{'value': tempo[0], 'label': tempo[1]} for tempo in Tempo.choices]
        self.assertEqual(response.json()['tempos'], expected_tempos)

    def test_get_all_tempos_invalid_method(self):
        response = self.client.post(reverse('get_all_tempos'))

        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())
        self.assertEqual(response.json()['error'], 'Invalid method')

class GetBangerSongsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user1 = User.objects.create(id="e5e28a48-8080-11ee-b962-0242ac120002", username='testuser1',
                                        email='test1@example.com',
                                        last_login=timezone.now())
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

    def setUp(self):
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer e5e28a48-8080-11ee-b962-0242ac120002')

    def test_get_banger_songs_with_filters(self):
        data = {'genre': 'Rock'}
        response = self.client.get(reverse('get_banger_songs'),data)

        self.assertEqual(response.status_code, 200)
        self.assertIn('song_info', response.json())
        self.assertEqual(response.json()['message'], 'Random Banger song found')

    def test_get_banger_songs_no_filters(self):
        response = self.client.get(reverse('get_banger_songs'))

        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())
        self.assertEqual(response.json()['error'], 'No filters provided')

    def test_get_banger_songs_no_match(self):
        response = self.client.get(reverse('get_banger_songs'),
                                   {'mood': 'SAD', 'tempo': 'FAST'})

        self.assertEqual(response.status_code, 404)
        self.assertIn('message', response.json())
        self.assertEqual(response.json()['message'], 'No Banger songs found with the given filters')

    def test_get_banger_songs_invalid_method(self):
        response = self.client.post(reverse('get_banger_songs'))

        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())
        self.assertEqual(response.json()['error'], 'Invalid method')


class SearchArtistsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user1 = User.objects.create(id="e5e28a48-8080-11ee-b962-0242ac120002", username='testuser1',
                                        email='test1@example.com',
                                        last_login=timezone.now())
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

    def setUp(self):
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer e5e28a48-8080-11ee-b962-0242ac120002')

    def test_search_artists_missing_search_text(self):
        response = self.client.get(reverse('search-artists'))

        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())
        self.assertEqual(response.json()['error'], 'Missing search text')

    def test_search_artists_invalid_method(self):
        response = self.client.post(reverse('search-artists'))

        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())
        self.assertEqual(response.json()['error'], 'Invalid method')

class SearchGenresTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user1 = User.objects.create(id="e5e28a48-8080-11ee-b962-0242ac120002", username='testuser1',
                                        email='test1@example.com',
                                        last_login=timezone.now())
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

    def setUp(self):
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer e5e28a48-8080-11ee-b962-0242ac120002')

    def test_search_genres_missing_search_text(self):
        response = self.client.get(reverse('search_genres'))

        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())
        self.assertEqual(response.json()['error'], 'Missing search text')

    def test_search_genres_invalid_method(self):
        response = self.client.post(reverse('search_genres'))

        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())
        self.assertEqual(response.json()['error'], 'Invalid method')