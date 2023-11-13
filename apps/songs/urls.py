from django.urls import path

from apps.songs import views

urlpatterns = [
 path('get-all/', view=views.get_all_songs, name='get-all-songs'),
 path('api/add', views.add_song, name='add-song'),
 path('api/search', views.search_songs, name='search-songs'),
 path('api/get', views.get_songs, name='get-songs'),
 path('api/fetch', views.get_song, name='get-song'), 
]
