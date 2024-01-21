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
                          UserPreferences, UserSongRating,
                          Friend)
from django.utils import timezone
from unittest.mock import patch, MagicMock
from rest_framework.test import APIClient
from datetime import timedelta

from rest_framework.test import APIClient
import uuid
from django.utils import timezone
from datetime import timedelta


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



class UserSongsWithGenreTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        pass  # No initial data needed

    def setUp(self):
        # Setup run before every test method.
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer e5e28a48-8080-11ee-b962-0242ac120002')

    def test_invalid_number_of_songs_type(self):
        data = {"number_of_songs": "invalid", "genre_name": "TestGenre"}
        response = self.client.get(reverse('get-songs-genre'), data)
        self.assertEqual(response.status_code, 400)

    def test_negative_number_of_songs(self):
        data = {"number_of_songs": "-1", "genre_name": "TestGenre"}
        response = self.client.get(reverse('get-songs-genre'), data)
        self.assertEqual(response.status_code, 404)

    @patch('users.views.User.objects.get')
    @patch('users.views.UserSongRating.objects.filter')
    def test_valid_request_with_zero_rated_songs(self, mock_user_song_ratings, mock_user_get):
        # Create a mock user and configure the return value of .get()
        mock_user = MagicMock()
        mock_user.id = 'testuserID'
        mock_user_get.return_value = mock_user

        # Mock the song ratings queryset and its chain methods
        mock_song_rating = MagicMock()
        mock_song = MagicMock()
        mock_song.id = 'song1'
        # Set other necessary attributes on the mock song object

        # Mock the queryset behavior
        mock_song_rating.song = mock_song
        mock_user_song_ratings.return_value.all.return_value = [mock_song_rating]

        # Call your endpoint with valid parameters
        params = {"number_of_songs": "5", "genre_name": "TestGenre"}
        response = self.client.get(reverse('get-songs-genre'), params)

        # Check that the response is OK
        self.assertEqual(response.status_code, 200)

        # Optionally, check that the mock was called with the expected arguments
        mock_user_get.assert_called_once_with(id='e5e28a48-8080-11ee-b962-0242ac120002')
        # assert that the response contains zero songs since the current user has no songs rated
        self.assertIn('songs', response.json())
        self.assertEqual(len(response.json()['songs']), 0)


class UserSongsWithTempoTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        pass  # No initial data needed

    def setUp(self):
        # Setup run before every test method.
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer e5e28a48-8080-11ee-b962-0242ac120002')

    def test_missing_tempo_name(self):
        data = {"number_of_songs": "5"}
        response = self.client.get(reverse('get-songs-tempo'), data, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_invalid_number_of_songs_type(self):
        data = {"number_of_songs": "invalid", "tempo_name": "TestTempo"}
        response = self.client.get(reverse('get-songs-tempo'), data)
        self.assertEqual(response.status_code, 400)

    def test_negative_number_of_songs(self):
        data = {"number_of_songs": "-1", "tempo_name": "TestTempo"}
        response = self.client.get(reverse('get-songs-tempo'), data)
        self.assertEqual(response.status_code, 404)

    @patch('users.views.User.objects.get')
    @patch('users.views.UserSongRating.objects.filter')
    def test_valid_request_with_zero_rated_songs(self, mock_user_song_ratings, mock_user_get):
        # Create a mock user and configure the return value of .get()
        mock_user = MagicMock()
        mock_user.id = 'testuserID'
        mock_user_get.return_value = mock_user

        # Mock the song ratings queryset and its chain methods
        mock_song_rating = MagicMock()
        mock_song = MagicMock()
        mock_song.id = 'song1'
        # Set other necessary attributes on the mock song object

        # Mock the queryset behavior
        mock_song_rating.song = mock_song
        mock_user_song_ratings.return_value.all.return_value = [mock_song_rating]

        # Call your endpoint with valid parameters
        params = {"number_of_songs": "5", "tempo_name": "TestTempo"}
        response = self.client.get(reverse('get-songs-tempo'), params)

        # Check that the response is OK
        self.assertEqual(response.status_code, 200)

        # Optionally, check that the mock was called with the expected arguments
        mock_user_get.assert_called_once_with(id='e5e28a48-8080-11ee-b962-0242ac120002')
        # assert that the response contains zero songs since the current user has no songs rated
        self.assertIn('songs', response.json())
        self.assertEqual(len(response.json()['songs']), 0)


class UserSongsWithArtistTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        pass  # No initial data needed

    def setUp(self):
        # Setup run before every test method.
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer e5e28a48-8080-11ee-b962-0242ac120002')

    def test_missing_tempo_name(self):
        data = {"number_of_songs": "5"}
        response = self.client.get(reverse('get-songs-artist'), data, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    @patch('users.views.User.objects.get')
    @patch('users.views.UserSongRating.objects.filter')
    def test_valid_request_with_irrelevant_artist(self, mock_user_song_ratings, mock_user_get):
        # Set up the mocks
        mock_user = MagicMock(spec=User)
        mock_user_get.return_value = mock_user

        mock_song_rating = MagicMock(spec=UserSongRating)
        mock_song = MagicMock(spec=Song)
        mock_song.id = 'song1'
        # Set other necessary attributes on the mock song object

        mock_song_rating.song = mock_song
        mock_user.usersongrating_set.prefetch_related.return_value.all.return_value = [mock_song_rating]

        # Mock ArtistSong association
        mock_artist_song = MagicMock()
        mock_artist = MagicMock()
        mock_artist.name = 'TestArtist'
        mock_artist_song.artist = mock_artist
        mock_song.artistsong_set.prefetch_related.return_value.all.return_value = [mock_artist_song]

        # Call the endpoint
        params = {"number_of_songs": "5", "artist_name": "NonExistingArtist"}
        response = self.client.get(reverse('get-songs-artist'), params)

        # Assert the response
        self.assertEqual(response.status_code, 200)
        self.assertIn('songs', response.json())
        self.assertEqual(len(response.json()['songs']), 0)


class UserRecentlyAddedSongTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        user1 = User.objects.create(id="e5e28a48-8080-11ee-b962-0242ac120002", username='testuser1',
                                    email='test1@example.com',
                                    last_login=timezone.now())  # Adapt field names and values

    def setUp(self):
        # Setup run before every test method.
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer e5e28a48-8080-11ee-b962-0242ac120002')

    @patch('users.views.User.objects.get')
    def test_missing_number_of_songs(self, mock_user_get):
        mock_user = MagicMock(spec=User)
        data = {}
        response = self.client.get(reverse('get-recently-added-songs'))
        self.assertEqual(response.status_code, 200)  # Assert that even if the
        # number of songs is not provided, the endpoint returns 200 with all of the songs
        self.assertIn('songs', response.json())
        self.assertGreaterEqual(len(response.json()['songs']), 0)

    def test_invalid_number_of_songs_type(self):
        data = {"number_of_songs": "invalid"}
        response = self.client.get(reverse('get-recently-added-songs'), data)
        self.assertEqual(response.status_code,
                         400)  # Assert that if the number is noninteger type, we return 400 Bad Request

    def test_negative_number_of_songs(self):
        data = {"number_of_songs": "-1", "tempo_name": "TestTempo"}
        response = self.client.get(reverse('get-recently-added-songs'), data)
        self.assertEqual(response.status_code, 400)  # Assert that if the number is negative, we return 400 Bad Request


class UserFavoriteSongsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        user1 = User.objects.create(id="e5e28a48-8080-11ee-b962-0242ac120002", username='testuser1',
                                    email='test1@example.com',
                                    last_login=timezone.now())  # Adapt field names and values
        song1 = Song.objects.create(id="song1",
                                    name="Fark Ettim",
                                    duration=timedelta(minutes=3, seconds=30),
                                    tempo=Tempo.MEDIUM,
                                    mood=Mood.HAPPY,
                                    recorded_environment=RecordedEnvironment.STUDIO,
                                    release_year=2020,
                                    )
        song1.genres.set([Genre.objects.create(name="TestGenre")])
        song2 = Song.objects.create(id="song2",
                                    name="Canima minnet",
                                    duration=timedelta(minutes=3, seconds=30),
                                    tempo=Tempo.MEDIUM,
                                    mood=Mood.HAPPY,
                                    recorded_environment=RecordedEnvironment.STUDIO,
                                    release_year=2020,
                                    )
        song2.genres.set([Genre.objects.create(name="TestGenre2")])
        UserSongRating.objects.create(user=user1, song=song1, rating=5)
        UserSongRating.objects.create(user=user1, song=song2, rating=2)

    def setUp(self):
        # Setup run before every test method.
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer e5e28a48-8080-11ee-b962-0242ac120002')

    # Test that we return both of the songs in order according to their ratings
    def test_multiple_songs(self):
        data = {"number_of_songs": "2"}
        response = self.client.get(reverse('get-favorite-songs'), data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['songs']), 2)  # Assert that the number of songs returned is 2
        self.assertEqual(response.json()['songs'][0]['id'],
                         'song1')  # Assert that the first song is song1 since it has higher rating
        self.assertEqual(response.json()['songs'][1]['id'],
                         'song2')  # Assert that the second song is song2 since it has lower rating

    # Test that if there are more songs than the number requested, the endpoint returns the number requested
    def test_more_songs_exist_than_wanted(self):
        data = {"number_of_songs": "1"}
        response = self.client.get(reverse('get-favorite-songs'), data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['songs']),
                         1)  # Assert that the number of songs returned is 1 since we requested 1
        self.assertEqual(response.json()['songs'][0]['id'],
                         'song1')  # Assert that the song having higher rating is returned which is song1


class UserFavoriteGenresTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        user1 = User.objects.create(id="e5e28a48-8080-11ee-b962-0242ac120002", username='testuser1',
                                    email='test1@example.com',
                                    last_login=timezone.now())  # Adapt field names and values
        song1 = Song.objects.create(id="song1",
                                    name="Fark Ettim",
                                    duration=timedelta(minutes=3, seconds=30),
                                    tempo=Tempo.MEDIUM,
                                    mood=Mood.HAPPY,
                                    recorded_environment=RecordedEnvironment.STUDIO,
                                    release_year=2020,
                                    )
        genre1 = Genre.objects.create(name="TestGenre")
        genre2 = Genre.objects.create(name="TestGenre2")
        song1.genres.set([genre1])
        song2 = Song.objects.create(id="song2",
                                    name="Canima minnet",
                                    duration=timedelta(minutes=3, seconds=30),
                                    tempo=Tempo.MEDIUM,
                                    mood=Mood.HAPPY,
                                    recorded_environment=RecordedEnvironment.STUDIO,
                                    release_year=2020,
                                    )
        song2.genres.set([genre2])
        song3 = Song.objects.create(id="song3",
                                    name="Canin sagolsun",
                                    duration=timedelta(minutes=3, seconds=30),
                                    tempo=Tempo.MEDIUM,
                                    mood=Mood.HAPPY,
                                    recorded_environment=RecordedEnvironment.STUDIO,
                                    release_year=2020,
                                    )
        song3.genres.set([genre1])
        UserSongRating.objects.create(user=user1, song=song1, rating=5)
        UserSongRating.objects.create(user=user1, song=song2, rating=2)
        UserSongRating.objects.create(user=user1, song=song3, rating=3)

    def setUp(self):
        # Setup run before every test method.
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer e5e28a48-8080-11ee-b962-0242ac120002')

    def test_multiple_songs_with_different_genre(self):
        data = {"number_of_songs": "5"}
        response = self.client.get(reverse('get-favorite-genres'), data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response.content)
        self.assertEqual(response_json.get('TestGenre'), 2)  # Must be 2 since we have 2 songs of this genre
        self.assertEqual(response_json.get('TestGenre2'), 1)  # Must be 1 since we only have 1 song of this genre

    def test_limited_songs_with_different_genre_one_for_each(self):
        data = {"number_of_songs": "2"}
        response = self.client.get(reverse('get-favorite-genres'), data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response.content)
        self.assertEqual(response_json.get('TestGenre'), 2)  # Must be 2 according to our setup
        self.assertEqual(response_json.get('TestGenre2'),
                         None)  # Must be 0 since the song with genre 2 has the lowest rating
        # genres in order of their ratings, TestGenre2 must be the second one


class UserFavoriteArtistsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        user1 = User.objects.create(id="e5e28a48-8080-11ee-b962-0242ac120002", username='testuser1',
                                    email='test1@example.com',
                                    last_login=timezone.now())  # Adapt field names and values
        song1 = Song.objects.create(id="song1",
                                    name="Canin sagolsun",
                                    duration=timedelta(minutes=3, seconds=30),
                                    tempo=Tempo.MEDIUM,
                                    mood=Mood.HAPPY,
                                    recorded_environment=RecordedEnvironment.STUDIO,
                                    release_year=2020,
                                    )
        artist1 = Artist.objects.create(id="1", name="Semicenk")
        artist2 = Artist.objects.create(id="2", name="Sagopa Kajmer")
        artist3 = Artist.objects.create(id="3", name="Ceza")
        artist4 = Artist.objects.create(id="4", name="Tarkan")
        artist5 = Artist.objects.create(id="5", name="Rast")
        song1.artists.set([artist1, artist5])
        song2 = Song.objects.create(id="song2",
                                    name="Neyim Var Ki",
                                    duration=timedelta(minutes=3, seconds=30),
                                    tempo=Tempo.MEDIUM,
                                    mood=Mood.HAPPY,
                                    recorded_environment=RecordedEnvironment.STUDIO,
                                    release_year=2020,
                                    )
        song2.artists.set([artist2, artist3])
        song3 = Song.objects.create(id="song3",
                                    name="Dudu",
                                    duration=timedelta(minutes=3, seconds=30),
                                    tempo=Tempo.MEDIUM,
                                    mood=Mood.HAPPY,
                                    recorded_environment=RecordedEnvironment.STUDIO,
                                    release_year=2020,
                                    )
        song3.artists.set([artist4])
        UserSongRating.objects.create(user=user1, song=song1, rating=2)
        UserSongRating.objects.create(user=user1, song=song2, rating=5)
        UserSongRating.objects.create(user=user1, song=song3, rating=3)

    def setUp(self):
        # Setup run before every test method.
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer e5e28a48-8080-11ee-b962-0242ac120002')

    def test_multiple_songs_with_multiple_artists(self):
        data = {"number_of_songs": "5"}
        response = self.client.get(reverse('get-favorite-artists'), data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response.content)
        self.assertEqual(response_json.get('Semicenk'), 1)  # Must be 1 since we have 1 song of this artist
        self.assertEqual(response_json.get('Rast'),
                         1)  # Must be 1 since we have 1 song of this artist, even though the song has multiple artists

    def test_limited_songs_with_different_genre_one_for_each(self):
        data = {"number_of_songs": "2"}
        response = self.client.get(reverse('get-favorite-artists'), data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response.content)
        self.assertEqual(response_json.get('Semicenk'),
                         None)  # Must be 0 since the song of Semicenk is not in the highest rated 2 songs
        self.assertEqual(response_json.get('Ceza'),
                         1)  # Must be 1 since Ceza has a song that is included in highest rated 2 songs


class GetAllRatedSongsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        user1 = User.objects.create(id="e5e28a48-8080-11ee-b962-0242ac120002", username='testuser1',
                                    email='test1user@example.com',
                                    last_login=timezone.now())  # Adapt field names and values
        user2 = User.objects.create(id="seconduserid", username='testuser2',
                                    email='test2user@example.com',
                                    last_login=timezone.now())  # Adapt field names and values
        song1 = Song.objects.create(id="song1",
                                    name="Canin Sagolsun",
                                    duration=timedelta(minutes=3, seconds=30),
                                    tempo=Tempo.MEDIUM,
                                    mood=Mood.HAPPY,
                                    recorded_environment=RecordedEnvironment.STUDIO,
                                    release_year=2020,
                                    )
        song2 = Song.objects.create(id="song2",
                                    name="Neyim Var Ki",
                                    duration=timedelta(minutes=3, seconds=30),
                                    tempo=Tempo.FAST,
                                    mood=Mood.RELAXED,
                                    recorded_environment=RecordedEnvironment.STUDIO,
                                    release_year=2020,
                                    )
        UserSongRating.objects.create(user=user1, song=song1, rating=2)
        UserSongRating.objects.create(user=user2, song=song2, rating=5)

    def setUp(self):
        # Setup run before every test method.
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer e5e28a48-8080-11ee-b962-0242ac120002')

    def test_invalid_number_of_songs(self):
        data = {"number_of_songs": "invalid"}
        response = self.client.get(reverse('get-all-recent'), data, content_type='application/json')
        self.assertEqual(response.status_code, 400)
    def test_get_different_users_rated_songs(self):
        data = {"number_of_songs": "2"}
        response = self.client.get(reverse('get-all-recent'), data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response.content)
        self.assertEqual(len(response_json['songs']), 2)  # Must be 2 since we have 2 ratings even if they are rated by different users
        self.assertEqual(response_json['songs'][0]['name'], 'Neyim Var Ki')  # Must be this song since it has higher rating
        self.assertEqual(response_json['songs'][1]['name'], 'Canin Sagolsun')  # Must be this song since it has higher rating


class SendFriendRequestTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        user1 = User.objects.create(id="e5e28a48-8080-11ee-b962-0242ac120002", username='testuser1',
                                    email='test1user@example.com',
                                    last_login=timezone.now())  # Adapt field names and values
        user2 = User.objects.create(id="seconduserid", username='testuser2',
                                    email='test2user@example.com',
                                    last_login=timezone.now())  # Adapt field names and values
        user3 = User.objects.create(id="thirduserid", username='testuser3',
                                    email='test3user@example.com',
                                    last_login=timezone.now())  # Adapt field names and values
        Friend.objects.create(user=user1, friend=user2)
    def setUp(self):
        # Setup run before every test method.
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer e5e28a48-8080-11ee-b962-0242ac120002')

    def test_wrong_method(self):
        data = {"username": "dummy_username"}
        response = self.client.get(reverse('send-friend-request'), data, content_type='application/json')
        self.assertEqual(response.status_code, 405)

    def test_friend_request_to_already_friend(self):
        data = json.dumps({"username": "testuser2"})

        response = self.client.post(reverse('send-friend-request'), data, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['error'], 'User is already a friend')

    def test_successful_request(self):
        data = json.dumps({"username": "testuser3"})
        response = self.client.post(reverse('send-friend-request'), data, content_type='application/json')
        self.assertEqual(response.status_code, 200)

class GetIncomingAndOutgoingRequestsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        user1 = User.objects.create(id="e5e28a48-8080-11ee-b962-0242ac120002", username='testuser1',
                                    email='test1user@example.com',
                                    last_login=timezone.now())  # Adapt field names and values
        user2 = User.objects.create(id="seconduserid", username='testuser2',
                                    email='test2user@example.com',
                                    last_login=timezone.now())  # Adapt field names and values
        user3 = User.objects.create(id="thirduserid", username='testuser3',
                                    email='test3user@example.com',
                                    last_login=timezone.now())  # Adapt field names and values
        user4 = User.objects.create(id="fourthuserid", username='testuser4',
                                    email='test4user@example.com',
                                    last_login=timezone.now())  # Adapt field names and values
        FriendRequest.objects.create(sender=user2, receiver=user1, status=RequestStatus.PENDING)
        FriendRequest.objects.create(sender=user3, receiver=user1, status=RequestStatus.REJECTED)
        FriendRequest.objects.create(sender=user1, receiver=user2, status=RequestStatus.PENDING)
        FriendRequest.objects.create(sender=user1, receiver=user4, status=RequestStatus.PENDING)
        FriendRequest.objects.create(sender=user1, receiver=user3, status=RequestStatus.REJECTED)

    def setUp(self):
        # Setup run before every test method.
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer e5e28a48-8080-11ee-b962-0242ac120002')

    def test_get_returns_only_pending_requests(self):
        response = self.client.get(reverse('get-all-incoming-requests'), {}, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(len(response.json()['requests']), 1) #To make sure that only pending requests are returned
        self.assertEqual(response_data['requests'][0]['name'], 'testuser2')

    def test_get_returns_only_pending_outgoing_requests(self):
        response = self.client.get(reverse('get-all-outgoing-requests'), {}, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(len(response.json()['requests']), 2) #To make sure that only pending requests are returned
        self.assertEqual(response_data['requests'][0]['name'], 'testuser2')
        self.assertEqual(response_data['requests'][1]['name'], 'testuser4')

    def test_get_incoming_count(self):
        response = self.client.get(reverse('get-incoming-count'), {}, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['count'], 1) #To make sure that only pending requests are returned

class AcceptIncomingRequestTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        user1 = User.objects.create(id="e5e28a48-8080-11ee-b962-0242ac120002", username='testuser1',
                                    email='test1user@example.com',
                                    last_login=timezone.now())  # Adapt field names and values
        user2 = User.objects.create(id="seconduserid", username='testuser2',
                                    email='test2user@example.com',
                                    last_login=timezone.now())  # Adapt field names and values
        user3 = User.objects.create(id="thirduserid", username='testuser3',
                                    email='test3user@example.com',
                                    last_login=timezone.now())  # Adapt field names and values
        FriendRequest.objects.create(sender=user2, receiver=user1, status=RequestStatus.PENDING)
        FriendRequest.objects.create(sender=user3, receiver=user1, status=RequestStatus.REJECTED)

    def setUp(self):
        # Setup run before every test method.
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer e5e28a48-8080-11ee-b962-0242ac120002')

    def test_accept_request_success(self):
        data = json.dumps({"username": "testuser2"})
        response = self.client.post(reverse('accept-friend-request'), data, content_type='application/json')
        self.assertEqual(response.status_code, 200)

    def test_accept_request_when_it_is_canceled(self):
        data = json.dumps({"username": "testuser3"})
        response = self.client.post(reverse('accept-friend-request'), data, content_type='application/json')
        self.assertEqual(response.status_code, 400)


class RejectIncomingRequestTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        user1 = User.objects.create(id="e5e28a48-8080-11ee-b962-0242ac120002", username='testuser1',
                                    email='test1user@example.com',
                                    last_login=timezone.now())  # Adapt field names and values
        user2 = User.objects.create(id="seconduserid", username='testuser2',
                                    email='test2user@example.com',
                                    last_login=timezone.now())  # Adapt field names and values
        user3 = User.objects.create(id="thirduserid", username='testuser3',
                                    email='test3user@example.com',
                                    last_login=timezone.now())  # Adapt field names and values
        FriendRequest.objects.create(sender=user2, receiver=user1, status=RequestStatus.PENDING)
        FriendRequest.objects.create(sender=user3, receiver=user1, status=RequestStatus.ACCEPTED)

    def setUp(self):
        # Setup run before every test method.
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer e5e28a48-8080-11ee-b962-0242ac120002')

    def test_reject_request_success(self):
        data = json.dumps({"username": "testuser2"})
        response = self.client.post(reverse('reject-friend-request'), data, content_type='application/json')
        self.assertEqual(response.status_code, 200)

    def test_reject_request_when_it_has_already_been_accepted(self):
        data = json.dumps({"username": "testuser3"})
        response = self.client.post(reverse('reject-friend-request'), data, content_type='application/json')
        self.assertEqual(response.status_code, 400)


class CancelOutgoingRequestTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        user1 = User.objects.create(id="e5e28a48-8080-11ee-b962-0242ac120002", username='testuser1',
                                    email='test1user@example.com',
                                    last_login=timezone.now())  # Adapt field names and values
        user2 = User.objects.create(id="seconduserid", username='testuser2',
                                    email='test2user@example.com',
                                    last_login=timezone.now())  # Adapt field names and values
        user3 = User.objects.create(id="thirduserid", username='testuser3',
                                    email='test3user@example.com',
                                    last_login=timezone.now())  # Adapt field names and values
        FriendRequest.objects.create(sender=user1, receiver=user2, status=RequestStatus.PENDING)

    def setUp(self):
        # Setup run before every test method.
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer e5e28a48-8080-11ee-b962-0242ac120002')

    def test_cancel_request_success(self):
        data = json.dumps({"username": "testuser2"})
        response = self.client.post(reverse('cancel-friend-request'), data, content_type='application/json')
        self.assertEqual(response.status_code, 200)

    def test_try_to_cancel_while_no_pending_request(self):
        data = json.dumps({"username": "testuser3"})
        response = self.client.post(reverse('cancel-friend-request'), data, content_type='application/json')
        self.assertEqual(response.status_code, 404)


class GetAllFriendsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        user1 = User.objects.create(id="e5e28a48-8080-11ee-b962-0242ac120002", username='testuser1',
                                    email='test1user@example.com',
                                    last_login=timezone.now())  # Adapt field names and values
        user2 = User.objects.create(id="seconduserid", username='testuser2',
                                    email='test2user@example.com',
                                    last_login=timezone.now())  # Adapt field names and values
        user3 = User.objects.create(id="thirduserid", username='testuser3',
                                    email='test3user@example.com',
                                    last_login=timezone.now())  # Adapt field names and values
        Friend.objects.create(user=user1, friend=user2) #user1 is friend with user2, but not with user3

    def setUp(self):
        # Setup run before every test method.
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer e5e28a48-8080-11ee-b962-0242ac120002')

    def test_get_all_friends(self):
        response = self.client.get(reverse('get-all-friends'), {}, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data['friends']), 1) #Assert that only one friend is returned, which is user2
        self.assertEqual(response_data['friends'][0]['name'], 'testuser2')


class RemoveFriendFromGroupTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        user1 = User.objects.create(id="e5e28a48-8080-11ee-b962-0242ac120002", username='testuser1',
                                    email='test1user@example.com',
                                    last_login=timezone.now())  # Adapt field names and values
        user2 = User.objects.create(id="seconduserid", username='testuser2',
                                    email='test2user@example.com',
                                    last_login=timezone.now())  # Adapt field names and values
        user3 = User.objects.create(id="thirduserid", username='testuser3',
                                    email='test3user@example.com',
                                    last_login=timezone.now())  # Adapt field names and values
        group = FriendGroup.objects.create(id="1", name="TestGroup", description="TestDescription",
                                           created_by=user1)
        group.friends.set([user1, user2])
        group2 = FriendGroup.objects.create(id="2", name="TestGroup2", description="TestDescription2",
                                            created_by=user2)
        group2.friends.set([user1, user2])

    def setUp(self):
        # Setup run before every test method.
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer e5e28a48-8080-11ee-b962-0242ac120002')

    def test_remove_friend_from_group_success(self):
        data = json.dumps({"friend_name": "testuser2", "group_id": 1})
        response = self.client.put(reverse('remove-friend-from-group'), data, content_type='application/json')
        self.assertEqual(response.status_code, 200)

    def test_remove_friend_but_not_authorized(self):
        data = json.dumps({"friend_name": "testuser2", "group_id": 2})
        response = self.client.put(reverse('remove-friend-from-group'), data, content_type='application/json')
        self.assertEqual(response.status_code, 401)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['error'], 'You are not authorized to remove friends from this group')

    def test_remove_friend_but_not_in_group(self):
        data = json.dumps({"friend_name": "testuser3", "group_id": 1})
        response = self.client.put(reverse('remove-friend-from-group'), data, content_type='application/json')
        self.assertEqual(response.status_code, 400)


class DeleteFriendGroupTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        user1 = User.objects.create(id="e5e28a48-8080-11ee-b962-0242ac120002", username='testuser1',
                                    email='test1user@example.com',
                                    last_login=timezone.now())  # Adapt field names and values
        user2 = User.objects.create(id="seconduserid", username='testuser2',
                                    email='test2user@example.com',
                                    last_login=timezone.now())  # Adapt field names and values
        group = FriendGroup.objects.create(id="1", name="TestGroup", description="TestDescription",
                                           created_by=user1)
        group.friends.set([user1, user2])
        group2 = FriendGroup.objects.create(id="2", name="TestGroup", description="TestDescription",
                                           created_by=user2)
        group2.friends.set([user1, user2])
    def setUp(self):
        # Setup run before every test method.
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer e5e28a48-8080-11ee-b962-0242ac120002')

    def test_delete_missing_param(self):
        response = self.client.delete(reverse('delete-friend-group'), {}, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['error'], 'Please check the group id field.')

    def test_delete_friend_group_wrong_method(self):
        data = {"group_id": "1"}
        response = self.client.post(reverse('delete-friend-group'), data, content_type='application/json')
        self.assertEqual(response.status_code, 405)


class GetAllFriendGroupsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        user1 = User.objects.create(id="e5e28a48-8080-11ee-b962-0242ac120002", username='testuser1',
                                    email='test1user@example.com',
                                    last_login=timezone.now())  # Adapt field names and values
        user2 = User.objects.create(id="seconduserid", username='testuser2',
                                    email='test2user@example.com',
                                    last_login=timezone.now())  # Adapt field names and values
        group = FriendGroup.objects.create(id="1", name="TestGroup", description="TestDescription",
                                           created_by=user1)
        group.friends.set([user1, user2])
        group2 = FriendGroup.objects.create(id="2", name="TestGroup", description="TestDescription",
                                           created_by=user2)
        group2.friends.set([user1, user2])

    def setUp(self):
        # Setup run before every test method.
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer e5e28a48-8080-11ee-b962-0242ac120002')

    def test_get_all_friend_groups(self):
        response = self.client.get(reverse('get-all-friend-groups-of-user'), {}, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data['friend_groups']), 2) #Assert that both groups are returned no matter who created them

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

    def test_save_playlist_unexpected_error(self):
        playlist_data = {
            'name': 'My Playlist',
            'description': 'A playlist description',
            'songs': [self.song.id]
        }
        with self.assertRaises(Exception):
            response = self.client.post(reverse('save_playlist', kwargs={'userid': self.user.id}),
                                        data=json.dumps(playlist_data),
                                        content_type='application/json')
