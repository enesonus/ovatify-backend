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
]
