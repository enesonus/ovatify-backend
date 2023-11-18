from django.urls import path

from apps.songs import views

urlpatterns = [
 path('get-all/', view=views.get_all_songs, name='get-all-songs'),
 path('api/get/', views.get_songs, name='get-songs'),
 path('api/fetch/', views.get_song, name='get-song'),
 path('api/add/', views.add_song, name='add-song'),
 path('api/search/', views.search_songs, name='search-songs'),
 path('get-all-genres/', views.get_all_genres, name='get-all-genres'),
 path('create-genre/', views.create_genre, name='create-genre'),
 path('upload-file/', views.import_song_JSON, name='import-song-json'),
 path('get-average-rating/', views.average_song_rating, name='get-average-rating'),
]
