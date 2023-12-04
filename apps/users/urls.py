from django.urls import path

from users import views

urlpatterns = [
    path('get-all/', view=views.get_all_users, name='get-all-users'),
    path('return-post-body/', view=views.return_post_body, name='return-post-body'),
    path('create-user/', view=views.create_user, name='create-user'),
    path('login/', view=views.login, name='login'),
    path('delete-user/', view=views.delete_user, name='delete-user'),
    path('update-user/', view=views.update_user, name='update-user'),
    path('user-preferences/', view=views.user_preferences_create, name='user_preferences_create'),
    path('user-songs/', view=views.user_songs_view, name='user-songs-view'),
    path('hello-github/', view=views.hello_github, name='hello-github'),
    path('add-song-rating/', view=views.add_song_rating, name='add-song-rating'),
    path('remove-friend/', view=views.remove_friend, name = 'remove-friend'),
    path('add-friend/', view=views.add_friend, name='add_friend'),
    path('edit-song-rating/', view=views.edit_song_rating, name='edit-song-rating'),
    path('delete-song-rating/', view=views.delete_song_rating, name='delete-song-rating'),
    path('get-songs-by-genre/', view=views.user_songs_with_genre, name='get-songs-genre'),
    path('get-songs-by-tempo/', view=views.user_songs_with_tempo, name='get-songs-tempo'),
    path('get-songs-by-artist/', view=views.user_songs_with_artist, name='get-songs-artist'),
    path('get-songs-by-mood/', view=views.user_songs_with_mood, name='get-songs-mood'),
    path('get-recently-added-songs/', view=views.get_recently_added_songs, name='get-recently-added-songs'),
    path('get-favorite-songs/', view=views.get_favorite_songs, name='get-favorite-songs'),
    path('get-favorite-genres/', view=views.get_favorite_genres, name='get-favorite-genres'),
    path('get-favorite-artists/', view=views.get_favorite_artists, name='get-favorite-artists'),
    path('get-favorite-moods/', view=views.get_favorite_moods, name='get-favorite-moods'),
    path('get-favorite-tempos/', view=views.get_favorite_tempos, name='get-favorite-tempo'),
    path('get-all-recent/', view=views.get_all_recent_songs, name='get-all-recent'),
    path('send-friend-request/', view=views.send_friend_request, name='send-friend-request'),
    path('get-all-incoming-requests/', view=views.get_all_incoming_requests, name='get-all-incoming-requests'),
    path('accept-friend-request/', view=views.accept_friend_request, name='accept-friend-request'),
    path('reject-friend-request/', view=views.reject_friend_request, name='reject-friend-request'),
    path('get-all-outgoing-requests/', view=views.get_all_outgoing_requests, name='get-all-outgoing-requests'),
    path('get-incoming-request-count/', view=views.get_incoming_requests_count, name='get-incoming-count'),
    path('cancel-friend-request/', view=views.cancel_friend_request, name='cancel-friend-request'),
    path('get-all-friends/', view=views.get_all_friends, name='get-all-friends'),
    path('get-all-global-requests/', view=views.get_all_global_requests, name='get-all-requests'),
    path('delete-request/', view=views.delete_request, name='delete-request'),
    path('edit-user-preferences/', view = views.edit_user_preferences, name= 'edit_user_preferences'),
    path('recommend-songs/', view = views.recommend_songs, name='recommend-songs'),
    path('get-user-profile/', view = views.get_user_profile, name= 'get-user-profile'),
    path('get-recent-addition-counts/', view=views.get_recent_addition_by_count, name='get-recent-addition-count'),
    path('get-profile-stats/', view=views.get_profile_stats, name='get-profile-stats'),
    path('recommend-since-you-like/', view=views.recommend_since_you_like, name='recommend-since-you-like'),
]
