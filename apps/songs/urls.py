from django.urls import path

from apps.songs import views

urlpatterns = [
 path('get-all/', view=views.get_all_songs, name='get-all-songs'),
]
