from django.db import IntegrityError
from django.test import TestCase
from songs.models import Playlist, Song, Genre, Artist, Album, Instrument, Tempo, Mood, RecordedEnvironment
from users.models import FriendGroup, User, UserSongRating
import uuid
from datetime import timedelta
from django.utils import timezone
from rest_framework.test import APIClient
from django.urls import reverse
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

    def setUp(self):
        # Setup run before every test method.
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer e5e28a48-8080-11ee-b962-0242ac120002')

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

    def test_export_by_genre(self):
        song1 = Song.objects.create(id="song1",
                                   name="Fark Ettim - 1",
                                   duration=timedelta(minutes=3, seconds=30),
                                   tempo=Tempo.MEDIUM,
                                   mood=Mood.HAPPY,
                                   recorded_environment=RecordedEnvironment.STUDIO,
                                   release_year=2020,)
        song2 = Song.objects.create(id="song2",
                                   name="Fark Ettim - 2",
                                   duration=timedelta(minutes=3, seconds=30),
                                   tempo=Tempo.MEDIUM,
                                   mood=Mood.HAPPY,
                                   recorded_environment=RecordedEnvironment.STUDIO,
                                   release_year=2020,)
        song3 = Song.objects.create(id="song3",
                                   name="Fark Etti - 3",
                                   duration=timedelta(minutes=3, seconds=30),
                                   tempo=Tempo.MEDIUM,
                                   mood=Mood.HAPPY,
                                   recorded_environment=RecordedEnvironment.STUDIO,
                                   release_year=2020,)
        artist = Artist.objects.create(id="artist1", name="testartist")

        user1 = User.objects.create(id="e5e28a48-8080-11ee-b962-0242ac120002", username='testuser1',
                                        email='test1@example.com',
                                        last_login=timezone.now())
        
        song1.genres.add(GenreModelTest.genre)
        song1.artists.add(artist)
        song2.genres.add(GenreModelTest.genre)
        song2.artists.add(artist)
        song3.genres.add(GenreModelTest.genre)
        song3.artists.add(artist)

        UserSongRating.objects.create(user=user1, song= song1, rating=5)
        UserSongRating.objects.create(user=user1, song= song2, rating=5)
        UserSongRating.objects.create(user=user1, song= song3, rating=5)

        url = reverse('export-by-genre')
        response = self.client.get(url, {'genre': 'Jazz'})

        # Test if the response is as expected
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Disposition'], 'attachment; filename="songs_data.json"')

        # Check if the exported data contains the expected song information
        exported_data = response.json()
        self.assertEqual(len(exported_data), 3)  # Assuming all three songs are exported

    def test_get_library_genre_names(self):
        url = reverse('get-library-genre-names')

        song1 = Song.objects.create(id="song1",
                                   name="Fark Ettim - 1",
                                   duration=timedelta(minutes=3, seconds=30),
                                   tempo=Tempo.MEDIUM,
                                   mood=Mood.HAPPY,
                                   recorded_environment=RecordedEnvironment.STUDIO,
                                   release_year=2020,)
        song2 = Song.objects.create(id="song2",
                                   name="Fark Ettim - 2",
                                   duration=timedelta(minutes=3, seconds=30),
                                   tempo=Tempo.MEDIUM,
                                   mood=Mood.HAPPY,
                                   recorded_environment=RecordedEnvironment.STUDIO,
                                   release_year=2020,)
        song3 = Song.objects.create(id="song3",
                                   name="Fark Etti - 3",
                                   duration=timedelta(minutes=3, seconds=30),
                                   tempo=Tempo.MEDIUM,
                                   mood=Mood.HAPPY,
                                   recorded_environment=RecordedEnvironment.STUDIO,
                                   release_year=2020,)
        artist2 = Artist.objects.create(id="artist2", name="testartist2")

        gen = Genre.objects.create(name="Pop")

        user1 = User.objects.create(id="e5e28a48-8080-11ee-b962-0242ac120002", username='testuser1',
                                        email='test1@example.com',
                                        last_login=timezone.now())
        
        song1.genres.add(gen)
        song1.artists.add(artist2)
        song2.genres.add(GenreModelTest.genre)
        song2.artists.add(artist2)
        song3.genres.add(gen)
        song3.artists.add(artist2)

        UserSongRating.objects.create(user=user1, song= song1, rating=5)
        UserSongRating.objects.create(user=user1, song= song2, rating=5)
        UserSongRating.objects.create(user=user1, song= song3, rating=5)
        
        response = self.client.get(url)
        data = response.json()

        # Test if the response status code is as expected
        self.assertEqual(response.status_code, 200)

        # Test if the response contains the correct artists
        self.assertIn('genres', data)
        genres = data['genres']
        self.assertIn(self.genre.name, genres)
        self.assertIn(gen.name, genres)
        self.assertEqual(len(genres), 2)

class ArtistModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.artist = Artist.objects.create(id="artist1", name="Artist 1", bio="Another Artist Bio")
    
    def setUp(self):
        # Setup run before every test method.
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer e5e28a48-8080-11ee-b962-0242ac120002')

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
    
    def test_export_by_artist(self):

        song1 = Song.objects.create(id="song1",
                                   name="Fark Ettim - 1",
                                   duration=timedelta(minutes=3, seconds=30),
                                   tempo=Tempo.MEDIUM,
                                   mood=Mood.HAPPY,
                                   recorded_environment=RecordedEnvironment.STUDIO,
                                   release_year=2020,)
        song2 = Song.objects.create(id="song2",
                                   name="Fark Ettim - 2",
                                   duration=timedelta(minutes=3, seconds=30),
                                   tempo=Tempo.MEDIUM,
                                   mood=Mood.HAPPY,
                                   recorded_environment=RecordedEnvironment.STUDIO,
                                   release_year=2020,)
        song3 = Song.objects.create(id="song3",
                                   name="Fark Etti - 3",
                                   duration=timedelta(minutes=3, seconds=30),
                                   tempo=Tempo.MEDIUM,
                                   mood=Mood.HAPPY,
                                   recorded_environment=RecordedEnvironment.STUDIO,
                                   release_year=2020,)
        artist2 = Artist.objects.create(id="artist2", name="testartist2")

        gen = Genre.objects.create(name="Jazz")

        user1 = User.objects.create(id="e5e28a48-8080-11ee-b962-0242ac120002", username='testuser1',
                                        email='test1@example.com',
                                        last_login=timezone.now())
        
        song1.genres.add(gen)
        song1.artists.add(ArtistModelTest.artist)
        song2.genres.add(gen)
        song2.artists.add(artist2)
        song3.genres.add(gen)
        song3.artists.add(artist2)

        UserSongRating.objects.create(user=user1, song= song1, rating=5)
        UserSongRating.objects.create(user=user1, song= song2, rating=5)
        UserSongRating.objects.create(user=user1, song= song3, rating=5)

        url = reverse('export-by-artist')
        response = self.client.get(url, {'artist': artist2.name})

        # Test if the response is as expected
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Disposition'], 'attachment; filename="songs_data.json"')

        # Check if the exported data contains the expected song information
        exported_data = response.json()
        self.assertEqual(len(exported_data), 2)  # Assuming all two songs are exported

    def test_get_library_artist_names(self):
        url = reverse('get-library-artist-names')

        song1 = Song.objects.create(id="song1",
                                   name="Fark Ettim - 1",
                                   duration=timedelta(minutes=3, seconds=30),
                                   tempo=Tempo.MEDIUM,
                                   mood=Mood.HAPPY,
                                   recorded_environment=RecordedEnvironment.STUDIO,
                                   release_year=2020,)
        song2 = Song.objects.create(id="song2",
                                   name="Fark Ettim - 2",
                                   duration=timedelta(minutes=3, seconds=30),
                                   tempo=Tempo.MEDIUM,
                                   mood=Mood.HAPPY,
                                   recorded_environment=RecordedEnvironment.STUDIO,
                                   release_year=2020,)
        song3 = Song.objects.create(id="song3",
                                   name="Fark Etti - 3",
                                   duration=timedelta(minutes=3, seconds=30),
                                   tempo=Tempo.MEDIUM,
                                   mood=Mood.HAPPY,
                                   recorded_environment=RecordedEnvironment.STUDIO,
                                   release_year=2020,)
        artist2 = Artist.objects.create(id="artist2", name="testartist2")

        gen = Genre.objects.create(name="Jazz")

        user1 = User.objects.create(id="e5e28a48-8080-11ee-b962-0242ac120002", username='testuser1',
                                        email='test1@example.com',
                                        last_login=timezone.now())
        
        song1.genres.add(gen)
        song1.artists.add(ArtistModelTest.artist)
        song2.genres.add(gen)
        song2.artists.add(artist2)
        song3.genres.add(gen)
        song3.artists.add(artist2)

        UserSongRating.objects.create(user=user1, song= song1, rating=5)
        UserSongRating.objects.create(user=user1, song= song2, rating=5)
        UserSongRating.objects.create(user=user1, song= song3, rating=5)
        
        response = self.client.get(url)
        data = response.json()

        # Test if the response status code is as expected
        self.assertEqual(response.status_code, 200)

        # Test if the response contains the correct artists
        self.assertIn('artists', data)
        artists = data['artists']
        self.assertIn(self.artist.name, artists)
        self.assertIn(artist2.name, artists)
        self.assertEqual(len(artists), 2)


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

class PlaylistModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Set up non-modified objects used by all test methods
        cls.user1 = User.objects.create(id="e5e28a48-8080-11ee-b962-0242ac120002", username='testuser1',
                                        email='test1@example.com',
                                        last_login=timezone.now())
        cls.user2 = User.objects.create(id="second", username='testuser2',
                                        email='test2@example.com',
                                        last_login=timezone.now())
        cls.friend_group = FriendGroup.objects.create(name='Test Group', created_by=cls.user1)
        cls.friend_group.friends.add(cls.user1, cls.user2)

        # Create songs
        cls.song1 = Song.objects.create(id="song1",
                                   name="Fark Ettim - 1",
                                   duration=timedelta(minutes=3, seconds=30),
                                   tempo=Tempo.MEDIUM,
                                   mood=Mood.HAPPY,
                                   recorded_environment=RecordedEnvironment.STUDIO,
                                   release_year=2020,)
        cls.song2 = Song.objects.create(id="song2",
                                   name="Fark Ettim - 2",
                                   duration=timedelta(minutes=3, seconds=30),
                                   tempo=Tempo.MEDIUM,
                                   mood=Mood.HAPPY,
                                   recorded_environment=RecordedEnvironment.STUDIO,
                                   release_year=2020,)

        # Create playlists and add them to the friend group
        cls.playlist1 = Playlist.objects.create(name='Playlist 1', user=cls.user1, friend_group=cls.friend_group)
        cls.playlist1.songs.add(cls.song1, cls.song2)

        cls.playlist2 = Playlist.objects.create(name='Playlist 2', user=cls.user1, friend_group=cls.friend_group)
        cls.playlist2.songs.add(cls.song1)
      

    def setUp(self):
        # Setup run before every test method.
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer e5e28a48-8080-11ee-b962-0242ac120002')

    def test_get_playlists_of_group(self):
        url = reverse('get-playlists-of-group')  # Replace with your actual endpoint name
        response = self.client.get(url, {'group_id': self.friend_group.id})

        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertEqual(response_data['count'], 2)  # Assuming there are 2 playlists in the group

        # Optionally, check for specific playlist details in the response
        playlist_names = [item['name'] for item in response_data['items']]
        self.assertIn(self.playlist1.name, playlist_names)
        self.assertIn(self.playlist2.name, playlist_names)

    def test_create_empty_playlist(self):
        url = reverse('create-empty-playlist-in-group')  # Replace with your actual endpoint name
        data = {'playlist_name': 'My Playlist New', 'playlist_description': 'A new playlist', 'group_id': self.friend_group.id}

        response = self.client.post(url, json.dumps(data), content_type='application/json')
        print(response)
        self.assertEqual(response.status_code, 201)
        self.assertIn('Playlist created successfully', response.json().get('message'))

        # Verify the playlist was created in the database
        playlist = Playlist.objects.filter(name='My Playlist New').first()
        self.assertIsNotNone(playlist)
        self.assertEqual(playlist.description, 'A new playlist')

        # Test creating a playlist without specifying a name
        data = {'playlist_name': 'My Playlist New 2', 'group_id': self.friend_group.id}
        response_default_name = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(response_default_name.status_code, 201)
        default_playlist_name = "My Playlist New 2"
        self.assertIn('Playlist created successfully', response_default_name.json().get('message'))

        # Verify the default-named playlist was created
        default_playlist = Playlist.objects.filter(name=default_playlist_name).first()
        self.assertIsNotNone(default_playlist)
    '''
    def test_delete_playlist_from_group(self):

        url = reverse('delete-playlist-from-group') + f'?playlist_id={self.playlist1.id}'

        response = self.client.delete(url)

        print(self.playlist1.id)
        print(response.json())

        self.assertEqual(response.status_code, 204)

        # Verify the playlist was deleted from the database
        self.assertFalse(Playlist.objects.filter(id=self.playlist1.id).exists())

        # Test with non-existent playlist
        url = reverse('delete-playlist-from-group') + f'?playlist_id=999'
        response_nonexistent = self.client.delete(url)
        self.assertEqual(response_nonexistent.status_code, 404)
        '''

class SearchSongsTest(TestCase):
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
        # Setup run before every test method.
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer e5e28a48-8080-11ee-b962-0242ac120002')

    def test_get_song_by_id(self):

        url = reverse('get-song-by-id')  # Replace with your actual endpoint name
        response = self.client.get(url, {'song_id': str(self.song.id)})

        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIn('song_info', response_data)
        self.assertEqual(response_data['song_info']['name'], 'Test Song')

    def test_add_song(self):
        url = reverse('add-song')  # Replace with your actual endpoint name
        data = {
            'spotify_id': '4rbXJipz3CaSQwtG3xXzzT',  # Semicenk Fark Ettim
            'rating': 4
        }
        response = self.client.post(url, json.dumps(data), content_type='application/json')

        self.assertIn(response.status_code, [200])
        response_data = response.json()
        self.assertIn('message', response_data)

        data = {
            'spotify_id': '3Gpffv3gaD1UxQPeElIjCp',  # Semicenk Batık Gemi
            'rating': 0
        }
        response = self.client.post(url, json.dumps(data), content_type='application/json')

        self.assertIn(response.status_code, [201])
        response_data = response.json()
        self.assertIn('message', response_data)

    def test_search_spotify(self):
        url = reverse('search-spotify')  # Replace with your actual endpoint name
        response = self.client.get(url, {'search_string': 'Batık Gemi'})

        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIn('results', response_data)
    '''
    def test_search_db(self):
        url = reverse('search-db')  # Replace with your actual endpoint name
        response = self.client.get(url, {'search_string': 'Test'})

        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIn('songs_info', response_data)
        self.assertTrue(any(song['track_name'] == 'Test Song' for song in response_data['songs_info']))
    '''
    