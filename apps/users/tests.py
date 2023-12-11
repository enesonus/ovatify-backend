import json
from django.test import Client, TestCase

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


class UserApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = Client()
        cls.client.defaults['AUTHORIZATION'] = 'Bearer e5e28a48-8080-11ee-b962-0242ac120002'
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

    # path('user-preferences/', view=views.user_preferences_create, name='user_preferences_create'),
    # path('user-songs/', view=views.user_songs_view, name='user-songs-view'),
    # path('hello-github/', view=views.hello_github, name='hello-github'),
    # path('add-song-rating/', view=views.add_song_rating, name='add-song-rating'),
    # path('remove-friend/', view=views.remove_friend, name = 'remove-friend'),
    # path('add-friend/', view=views.add_friend, name='add_friend'),
    # path('edit-song-rating/', view=views.edit_song_rating, name='edit-song-rating'),
    # path('delete-song-rating/', view=views.delete_song_rating, name='delete-song-rating'),
    # path('get-songs-by-genre/', view=views.user_songs_with_genre, name='get-songs-genre'),
    # path('get-songs-by-tempo/', view=views.user_songs_with_tempo, name='get-songs-tempo'),
    # path('get-songs-by-artist/', view=views.user_songs_with_artist, name='get-songs-artist'),
    # path('get-songs-by-mood/', view=views.user_songs_with_mood, name='get-songs-mood'),
    # path('get-recently-added-songs/', view=views.get_recently_added_songs, name='get-recently-added-songs'),
    # path('get-favorite-songs/', view=views.get_favorite_songs, name='get-favorite-songs'),
    # path('get-favorite-genres/', view=views.get_favorite_genres, name='get-favorite-genres'),
    # path('get-favorite-artists/', view=views.get_favorite_artists, name='get-favorite-artists'),
    # path('get-favorite-moods/', view=views.get_favorite_moods, name='get-favorite-moods'),
    # path('get-favorite-tempos/', view=views.get_favorite_tempos, name='get-favorite-tempo'),
    # path('get-all-recent/', view=views.get_all_recent_songs, name='get-all-recent'),
    # path('send-friend-request/', view=views.send_friend_request, name='send-friend-request'),
    # path('get-all-incoming-requests/', view=views.get_all_incoming_requests, name='get-all-incoming-requests'),
    # path('accept-friend-request/', view=views.accept_friend_request, name='accept-friend-request'),
    # path('reject-friend-request/', view=views.reject_friend_request, name='reject-friend-request'),
    # path('get-all-outgoing-requests/', view=views.get_all_outgoing_requests, name='get-all-outgoing-requests'),
    # path('get-incoming-request-count/', view=views.get_incoming_requests_count, name='get-incoming-count'),
    # path('cancel-friend-request/', view=views.cancel_friend_request, name='cancel-friend-request'),
    # path('get-all-friends/', view=views.get_all_friends, name='get-all-friends'),
    # path('get-all-global-requests/', view=views.get_all_global_requests, name='get-all-requests'),
    # path('delete-request/', view=views.delete_request, name='delete-request'),
    # path('edit-user-preferences/', view = views.edit_user_preferences, name= 'edit_user_preferences'),
    # path('recommend-you-might-like/', view = views.recommend_you_might_like, name='recommend-you-might-like'),
    # path('get-user-profile/', view = views.get_user_profile, name= 'get-user-profile'),
    # path('get-recent-addition-counts/', view=views.get_recent_addition_by_count, name='get-recent-addition-count'),
    # path('get-profile-stats/', view=views.get_profile_stats, name='get-profile-stats'),
    # path('recommend-since-you-like/', view=views.recommend_since_you_like, name='recommend-since-you-like'),
    # path('recommend-friend-mix/', view=views.recommend_friend_mix, name='recommend-friend-mix'),
    # path('recommend-friend-listen/', view=views.recommend_friend_listen, name='recommend-friend-listen'),
    # path('export-by-genre/', views.export_by_genre, name='export-by-genre'),
    # path('export-by-artist/', views.export_by_artist, name='export-by-artist'),
    # path('get-library-artist-names/', views.get_library_artist_names, name='get-library-artist-names'),
    # path('get-library-genre-names/', views.get_library_genre_names, name='get-library-genre-names'),
    # path('upload-file/', views.import_song_JSON, name='import-song-json'),