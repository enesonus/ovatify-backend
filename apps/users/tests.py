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
        group = FriendGroup.objects.create(name="Test Group")
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
                                   tempo=Tempo.MEDIUM,
                                   mood=Mood.HAPPY,
                                   recorded_environment=RecordedEnvironment.STUDIO,
                                   release_year=2020,
                                   )
        cls.song2 = Song.objects.create(id="song2",
                                      name="Canima minnet",
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
        # Setup the mock
        mock_filter.return_value.exists.return_value = True

        # Test for existing user
        data = {"email": "existing@example.com"}
        data = json.dumps(data)
        response = self.client.post(reverse("create-user"),
                                    data=data,
                                    content_type='application/json')
        self.assertEqual(response.status_code, 400)
        mock_create.assert_not_called()



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
