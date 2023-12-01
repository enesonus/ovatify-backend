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
 path('upload-file/', views.import_song_JSON, name='import-song-json'),
 path('get-average-rating/', views.average_song_rating, name='get-average-rating'),
 path('get-genres/', views.get_demanded_genres, name='get-genres'),
]
