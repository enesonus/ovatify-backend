from django.urls import path

from songs import views

urlpatterns = [
 path('get-all/', view=views.get_all_songs, name='get-all-songs'),
 path('search-db/', views.search_db, name='search-db'),
 path('get-song-by-id/', views.get_song_by_id, name='get-song-by-id'),
 path('add-song/', views.add_song, name='add-song'),
 path('search-spotify/', views.search_spotify, name='search-spotify'),
 path('get-all-genres/', views.get_all_genres, name='get-all-genres'),
 path('create-genre/', views.create_genre, name='create-genre'),
 path('get-average-rating/', views.average_song_rating, name='get-average-rating'),
 path('get-genres/', views.get_demanded_genres, name='get-genres'),
 path('get-songs-by-genre/', views.get_songs_by_genre, name='get-songs-by-genre'),
 path('get-song-genres/', views.get_genres_of_a_song, name='get-song-genres'),
 path('get-random-genres/', views.get_random_genres, name='get-random-genres'),
 path('search-artists/', views.search_artists, name='search-artists'),
 path('search-genres/', views.search_genres, name='search_genres'),
 path('get-all-moods/', views.get_all_moods, name='get_all_moods'),
 path('get-all-tempos/', views.get_all_tempos, name='get_all_tempos'),
 path('get-banger-songs/', views.get_banger_songs, name='get_banger_songs')

]
