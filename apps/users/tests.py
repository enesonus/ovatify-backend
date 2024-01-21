import json
from django.test import Client, TestCase
from django.urls import reverse

from songs.models import (Song, Tempo,
                          Mood, RecordedEnvironment,
                          Genre, Artist,
                          Album, Instrument,
                          GenreSong, ArtistSong,
                          AlbumSong, InstrumentSong)


from users.models import (FriendGroup, FriendRequest,
                          RequestStatus, User,
                          UserPreferences, UserSongRating)
from django.utils import timezone
from unittest.mock import patch, MagicMock
from rest_framework.test import APIClient
from datetime import timedelta

from rest_framework.test import APIClient
import uuid
from django.utils import timezone
from datetime import timedelta
<<<<<<< Updated upstream
=======


>>>>>>> Stashed changes
class UserModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Setup initial data for the models
        cls.user1 = User.objects.create(id="first", username='testuser1',
                                        email='test1@example.com',
                                        last_login=timezone.now())  # Adapt field names and values
        cls.user2 = User.objects.create(id="second", username='testuser2',
                                        email='test2@example.com',
                                        last_login=timezone.now())  # Adapt field names and values

    def test_user_field_labels(self):
        user = UserModelTest.user1
        # Test field labels
        self.assertEqual(user._meta.get_field('username').verbose_name,
                         'username')  # Adapt field names and expected labels
        self.assertEqual(user._meta.get_field('email').verbose_name,
                         'email')  # Adapt field names and expected labels

    def test_user_string_representation(self):
        user = UserModelTest.user1
        # Test string representation of user model (if implemented)
        self.assertEqual(str(user), 'testuser1')  # Adapt expected string representation

    def test_friend_request_creation(self):
        request = FriendRequest.objects.create(sender=UserModelTest.user1,
                                               receiver=UserModelTest.user2,
                                               status=RequestStatus.PENDING)
        # Test creation and attributes of FriendRequest
        self.assertEqual(request.status, RequestStatus.PENDING)
        self.assertEqual(request.sender, UserModelTest.user1)
        self.assertEqual(request.receiver, UserModelTest.user2)

    def test_accept_friend_request(self):
        # Add friend
        req = FriendRequest.objects.create(sender=UserModelTest.user1,
                                           receiver=UserModelTest.user2,
                                           status=RequestStatus.PENDING)

        UserModelTest.user1.friends.add(UserModelTest.user2)
        req = FriendRequest.objects.get(sender=UserModelTest.user1,
                                        receiver=UserModelTest.user2)
        req.status = RequestStatus.ACCEPTED
        req.save()
        req = FriendRequest.objects.get(sender=UserModelTest.user1,
                                        receiver=UserModelTest.user2)
        self.assertEqual(req.status, RequestStatus.ACCEPTED)
        # Test if friend is added
        self.assertIn(UserModelTest.user2, UserModelTest.user1.friends.all())
        self.assertIn(UserModelTest.user1, UserModelTest.user2.friends.all())

    def test_reject_friend_request(self):
        req = FriendRequest.objects.create(sender=UserModelTest.user1,
                                           receiver=UserModelTest.user2,
                                           status=RequestStatus.PENDING)
        req = FriendRequest.objects.get(sender=UserModelTest.user1,
                                        receiver=UserModelTest.user2)
        req.status = RequestStatus.REJECTED
        req.save()
        req = FriendRequest.objects.get(sender=UserModelTest.user1,
                                        receiver=UserModelTest.user2)
        self.assertEqual(req.status, RequestStatus.REJECTED)
        # Test if friend is not added
        self.assertNotIn(UserModelTest.user2,
                         UserModelTest.user1.friends.all())
        self.assertNotIn(UserModelTest.user1,
                         UserModelTest.user2.friends.all())

    def test_add_user_preferences(self):
        pref = UserPreferences.objects.create(user=UserModelTest.user1,
                                              data_processing_consent=True,
                                              data_sharing_consent=True)
        pref = UserPreferences.objects.get(user=UserModelTest.user1)
        # Test creation and attributes of UserPreferences
        self.assertEqual(pref.user, UserModelTest.user1)
        self.assertEqual(pref.data_processing_consent, True)
        self.assertEqual(pref.data_sharing_consent, True)

    def test_update_user_preferences(self):
        pref = UserPreferences.objects.create(user=UserModelTest.user1,
                                              data_processing_consent=True,
                                              data_sharing_consent=True)
        pref = UserPreferences.objects.get(user=UserModelTest.user1)
        pref.data_processing_consent = False
        pref.data_sharing_consent = False
        pref.save()
        pref = UserPreferences.objects.get(user=UserModelTest.user1)
        # Test creation and attributes of UserPreferences
        self.assertEqual(pref.user, UserModelTest.user1)
        self.assertEqual(pref.data_processing_consent, False)
        self.assertEqual(pref.data_sharing_consent, False)

    def test_create_friend_group(self):
        group = FriendGroup.objects.create(name="Test Group", created_by=UserModelTest.user1)
        # Add members to the group
        group.friends.add(UserModelTest.user1, UserModelTest.user2)
        # Test creation and attributes of FriendGroup
        self.assertEqual(group.name, "Test Group")
        self.assertIn(UserModelTest.user1, group.friends.all())
        self.assertIn(UserModelTest.user2, group.friends.all())

class UserSongRatingModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Setup initial data for the models
        cls.user1 = User.objects.create(id="first", username='testuser1',
                                        email='test1@example.com',
                                        last_login=timezone.now())
        cls.user2 = User.objects.create(id="second", username='testuser2',
                                        email='test2@example.com',
                                        last_login=timezone.now())
        cls.song1 = Song.objects.create(id="song1",
                                   name="Fark Ettim",
                                   duration=timedelta(minutes=3, seconds=30),
                                   tempo=Tempo.MEDIUM,
                                   mood=Mood.HAPPY,
                                   recorded_environment=RecordedEnvironment.STUDIO,
                                   release_year=2020,
                                   )
        cls.song2 = Song.objects.create(id="song2",
                                      name="Canima minnet",
                                      duration=timedelta(minutes=3, seconds=30),
                                      tempo=Tempo.MEDIUM,
                                      mood=Mood.HAPPY,
                                      recorded_environment=RecordedEnvironment.STUDIO,
                                      release_year=2020,
                                      )

    def test_user_song_rating_creation(self):
        rating = UserSongRating.objects.create(user=UserSongRatingModelTest.user1,
                                               song=UserSongRatingModelTest.song1,
                                               rating=4.5)
        # Test creation and attributes of UserSongRating
        self.assertEqual(rating.user, UserSongRatingModelTest.user1)
        self.assertEqual(rating.song, UserSongRatingModelTest.song1)
        self.assertEqual(rating.rating, 4.5)

    def test_update_user_song_rating(self):
        rating = UserSongRating.objects.create(user=UserSongRatingModelTest.user1,
                                              song=UserSongRatingModelTest.song1,
                                              rating=4.5)
        rating.rating = 3.5
        rating.save()
        rating = UserSongRating.objects.get(user=UserSongRatingModelTest.user1,
                                            song=UserSongRatingModelTest.song1)
        # Test creation and attributes of UserSongRating
        self.assertEqual(rating.user, UserSongRatingModelTest.user1)
        self.assertEqual(rating.song, UserSongRatingModelTest.song1)
        self.assertEqual(rating.rating, 3.5)

    def test_delete_user_song_rating(self):
        rating = UserSongRating.objects.create(user=UserSongRatingModelTest.user1,
                                               song=UserSongRatingModelTest.song1,
                                               rating=4.5)
        rating.delete()
        # Test if rating is deleted
        self.assertFalse(UserSongRating.objects.filter(user=UserSongRatingModelTest.user1,
                                                       song=UserSongRatingModelTest.song1).exists())


class CreateUserViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Setup any initial data the tests might rely on
        cls.user = User.objects.create(id="testuser", username='existinguser',
                                       email='existing@example.com',
                                       last_login=timezone.now())

    def setUp(self):
        # Setup run before every test method.
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer e5e28a48-8080-11ee-b962-0242ac120002')

    def test_create_user_no_email(self):
        # Test for the scenario where email is not provided in the request(400 Bad Request)
        response = self.client.post(reverse('create-user'),
                                    {},
                                    content_type='application/json')
        self.assertEqual(response.status_code, 400)

    @patch('users.views.User.objects.filter')
    @patch('users.views.User.objects.create')
    def test_create_user_existing_email(self, mock_create, mock_filter):
        # Setup the mock to return a response with an OK status code to imitate the behavior of database query
        mock_filter.return_value.exists.return_value = True

        # Test for existing user
        data = {"email": "existing@example.com"}
        data = json.dumps(data)
        response = self.client.post(reverse("create-user"),
                                    data=data,
                                    content_type='application/json')
        self.assertEqual(response.status_code, 400)
        mock_create.assert_not_called()  # Assert that the create method was not called because the user already exists


class DeleteUserViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        pass  # No initial data needed

    def setUp(self):
        # Setup run before every test method.
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer e5e28a48-8080-11ee-b962-0242ac120002')

    @patch('users.views.User.objects.get')
    def test_delete_nonexistent_user(self, mock_get):
        # Setup the mock to return a response with an OK status code to imitate the behavior of database query
        mock_get.side_effect = User.DoesNotExist
        # Test if a user with the given id does not exist (404 Not Found)
        response = self.client.delete(reverse("delete-user"))
        self.assertEqual(response.status_code, 404)


class UserPreferencesCreateTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Nothing to set up
        pass

    def setUp(self):
        # Setup run before every test method.
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer e5e28a48-8080-11ee-b962-0242ac120002')

    @patch('users.views.UserPreferences.objects.get_or_create')
    @patch('users.views.User.objects.get')
    def test_user_preferences_user_not_exist(self, mock_get, mock_preferences_get_or_create):
        mock_get.side_effect = User.DoesNotExist
        data = {"user": "nonexistinguser"}
        response = self.client.post(reverse('user-preferences-create'), json.dumps(data),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 404)
        # assert that preferences are not created
        self.assertFalse(mock_preferences_get_or_create.called)

    @patch('users.views.UserPreferences.objects.get_or_create')
    @patch('users.views.User.objects.get')
    def test_user_preferences_create_new(self, mock_user_get, mock_preferences_get_or_create):
        mock_user = MagicMock(spec=User)  # Create a mock user
        mock_user_get.return_value = mock_user  # Return the mock user when User.objects.get is called
        mock_preferences_get_or_create.return_value = (MagicMock(spec=UserPreferences), True)
        # Return a mock UserPreferences object
        # and True to indicate that the object was created

        data = {"user": "existinguser"}
        response = self.client.post(reverse('user-preferences-create'), json.dumps(data),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 201)

    @patch('users.views.UserPreferences.objects.get_or_create')
    @patch('users.views.User.objects.get')
    def test_user_preferences_update_existing(self, mock_user_get, mock_preferences_get_or_create):
        mock_user = MagicMock(spec=User)  # Create a mock user
        mock_user_get.return_value = mock_user  # Return the mock user when User.objects.get is called
        mock_preferences_get_or_create.return_value = (MagicMock(spec=UserPreferences), False)
        # Return a mock UserPreferences object and False to indicate that the object
        # already exists (which is the implementation of get_or_create)
        data = {"user": "existinguser", "data_processing_consent": False, "data_sharing_consent": False}
        response = self.client.post(reverse('user-preferences-create'), json.dumps(data),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 200)


class DeleteSongRatingTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Nothing to set up
        pass

    def setUp(self):
        # Setup run before every test method.
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer e5e28a48-8080-11ee-b962-0242ac120002')

    @patch('users.views.User.objects.get')
    def test_user_does_not_exist(self, mock_user_get):
        mock_user_get.side_effect = User.DoesNotExist
        data = {"userid": "nonexistinguser", "song_id": "123"}
        response = self.client.delete(reverse('delete-song-rating'), json.dumps(data),
                                      content_type='application/json')
        self.assertEqual(response.status_code, 404)

    @patch('users.views.Song.objects.get')
    @patch('users.views.User.objects.get')
    def test_song_does_not_exist(self, mock_user_get, mock_song_get):
        mock_user_get.return_value = MagicMock(spec=User)
        mock_song_get.side_effect = Song.DoesNotExist
        data = {"userid": "existinguser", "song_id": "nonexistingsong"}
        response = self.client.delete(reverse('delete-song-rating'), json.dumps(data),
                                      content_type='application/json')
        self.assertEqual(response.status_code, 404)

    @patch('users.views.UserSongRating.objects.get')
    @patch('users.views.Song.objects.get')
    @patch('users.views.User.objects.get')
    def test_user_song_rating_does_not_exist(self, mock_user_get, mock_song_get, mock_user_song_rating_get):
        mock_user_get.return_value = MagicMock(spec=User)
        mock_song_get.return_value = MagicMock(spec=Song)
        mock_user_song_rating_get.side_effect = UserSongRating.DoesNotExist
        data = {"userid": "existinguser", "song_id": "existingsong"}
        response = self.client.delete(reverse('delete-song-rating'), json.dumps(data),
                                      content_type='application/json')
        self.assertEqual(response.status_code, 404)

    @patch('users.views.UserSongRating.objects.get')
    @patch('users.views.Song.objects.get')
    @patch('users.views.User.objects.get')
    def test_delete_rating_successfully(self, mock_user_get, mock_song_get, mock_user_song_rating_get):
        mock_user_get.return_value = MagicMock(spec=User)
        mock_song_get.return_value = MagicMock(spec=Song)
        mock_user_song_rating = MagicMock(spec=UserSongRating)
        mock_user_song_rating_get.return_value = mock_user_song_rating
        data = {"userid": "existinguser", "song_id": "existingsong"}
        response = self.client.delete(reverse('delete-song-rating'), json.dumps(data),
                                      content_type='application/json')
        self.assertEqual(response.status_code, 204)
        mock_user_song_rating.delete.assert_called_once()


class UserSongsWithGenreTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Set up data for the whole TestCase
        newUser = User.objects.create(id="testuserID", username='testusername',
                                      email='user@example.com', last_login=timezone.now())
        newGenre = Genre.objects.create(name='TestGenre')
        newSong = Song.objects.create(id="song1",
                                      name="Test Song 1",
                                      duration=timedelta(minutes=3, seconds=30),
                                      tempo=Tempo.MEDIUM,
                                      mood=Mood.HAPPY,
                                      recorded_environment=RecordedEnvironment.STUDIO,
                                      release_year=2020,
                                      )
        newSong.genres.set([newGenre])
        cls.song = newSong
        cls.user = newUser
        UserSongRating.objects.create(user=newUser, song=newSong, rating=5)

    def setUp(self):
        # Setup run before every test method.
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer e5e28a48-8080-11ee-b962-0242ac120002')

    def test_invalid_number_of_songs_type(self):
        data = {"userid": "testuserID", "number_of_songs": "invalid", "genre_name": "TestGenre"}
        response = self.client.get(reverse('get-songs-genre'), json.dumps(data),
                                   content_type='application/json')
        self.assertEqual(response.status_code, 400)


# class UserApiTest(TestCase):
#     @classmethod
#     def setUpTestData(cls):
#         cls.headers={"authorization": "Bearer e5e28a48-8080-11ee-b962-0242ac120002"}
#         cls.client = Client()

#         # cls.client.credentials(HTTP_AUTHORIZATION='Bearer e5e28a48-8080-11ee-b962-0242ac120002')
#         # Setup initial data for the models
#         cls.user1 = User.objects.create(id="first", username='testuser1',
#                                         email='test1@example.com',
#                                         last_login=timezone.now())
#         cls.user2 = User.objects.create(id="second", username='testuser2',
#                                         email='test2@example.com',
#                                         last_login=timezone.now())
#         cls.song1 = Song.objects.create(id="song1",
#                                         name="Fark Ettim",
#                                         tempo=Tempo.MEDIUM,
#                                         mood=Mood.HAPPY,
#                                         duration=timezone.timedelta(seconds=100),
#                                         recorded_environment=RecordedEnvironment.STUDIO,
#                                         release_year=2020,
#                                         )
#         cls.song2 = Song.objects.create(id="song2",
#                                         name="Canima minnet",
#                                         tempo=Tempo.MEDIUM,
#                                         mood=Mood.HAPPY,
#                                         duration=timezone.timedelta(seconds=100),
#                                         recorded_environment=RecordedEnvironment.STUDIO,
#                                         release_year=2020,
#                                         )

#     def test_get_songs_by_tempo(self):
#         self.song1.tempo = Tempo.FAST
#         self.song1.save()
#         self.song2.tempo = Tempo.FAST
#         self.song2.save()

#         response = self.client.get(reverse('get-songs-tempo'), {'userid': self.user1.id, 'tempo_name': 'Fast'},
#                                    headers=self.headers)
#         self.assertEqual(response.status_code, 200)
#         self.assertIn('songs', response.json())

#     def test_get_songs_by_genre(self):
#         genre = Genre.objects.create(name="Rock")
#         GenreSong.objects.create(song=self.song1, genre=genre)
#         GenreSong.objects.create(song=self.song2, genre=genre)

#         response = self.client.get(reverse('get-songs-genre'), {'genre_name': 'Rock'},
#                                    headers=self.headers)
#         self.assertEqual(response.status_code, 200)
#         self.assertIn('songs', response.json())

#     def test_get_songs_by_artist(self):
#         artist = Artist.objects.create(name="Artist1")
#         ArtistSong.objects.create(song=self.song1, artist=artist)
#         ArtistSong.objects.create(song=self.song2, artist=artist)

#         response = self.client.get(reverse('get-songs-artist'), {'userid': self.user1.id, 'artist_name': 'Artist1'},
#                                    headers=self.headers)
#         self.assertEqual(response.status_code, 200)
#         self.assertIn('songs', response.json())

#     def test_get_songs_by_mood(self):
#         self.song1.mood = Mood.HAPPY
#         self.song1.save()
#         self.song2.mood = Mood.HAPPY
#         self.song2.save()

#         response = self.client.get(reverse('get-songs-mood'), {'userid': self.user1.id, 'mood_name': 'Happy'},
#                                    headers=self.headers)
#         self.assertEqual(response.status_code, 200)
#         self.assertIn('songs', response.json())

#     def test_get_recently_added_songs(self):
#         # Assuming songs are already created and rated in setUp
#         response = self.client.get(reverse('get-recently-added-songs'), {'userid': self.user1.id},
#                                    headers=self.headers)
#         self.assertEqual(response.status_code, 200)
#         self.assertIn('songs', response.json())

#     def test_get_favorite_songs(self):
#         # Assuming songs are already created and rated in setUp
#         response = self.client.get(reverse('get-favorite-songs'), {'userid': self.user1.id},
#                                    headers=self.headers)
#         self.assertEqual(response.status_code, 200)
#         self.assertIn('songs', response.json())

class SavePlaylistTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Setup any initial data the tests might rely on
        cls.user = User.objects.create(id="testuser", username='existinguser',
                                       email='existing@example.com',
                                       last_login=timezone.now())
        cls.genre = Genre.objects.create(name="Rock")
        cls.artist = Artist.objects.create(id="artist1", name="Artist 1", bio="Artist Bio")
        cls.album = Album.objects.create(id="album1", name="Album 1", release_year=2020)
        cls.instrument = Instrument.objects.create(type="String", name="Guitar")
        cls.song = Song.objects.create(
            id="song1",
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

<<<<<<< Updated upstream

=======
>>>>>>> Stashed changes
    def test_save_playlist_invalid_json_format(self):
        invalid_data = 'Invalid JSON format'

        response = self.client.post(reverse('save_playlist'),
                                    data=invalid_data,
                                    content_type='application/json')

        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())
        self.assertEqual(response.json()['error'], 'Invalid JSON format')

    def test_save_playlist_user_not_found(self):
        invalid_user_id = 'invalid_user_id'

        response = self.client.post(reverse('save_playlist'),
                                    data=json.dumps({}),
                                    content_type='application/json')

        self.assertEqual(response.status_code, 404)
        self.assertIn('error', response.json())
        self.assertEqual(response.json()['error'], 'User not found')

<<<<<<< Updated upstream

=======
>>>>>>> Stashed changes
    def test_save_playlist_unexpected_error(self):
        playlist_data = {
            'name': 'My Playlist',
            'description': 'A playlist description',
            'songs': [self.song.id]
        }
        with self.assertRaises(Exception):
<<<<<<< Updated upstream
            response = self.client.post(reverse('save_playlist',kwargs={'userid': self.user.id}),
                                        data=json.dumps(playlist_data),
                                        content_type='application/json')
=======
            response = self.client.post(reverse('save_playlist', kwargs={'userid': self.user.id}),
                                        data=json.dumps(playlist_data),
                                        content_type='application/json')
>>>>>>> Stashed changes
