from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import spotipy
from OVTF_Backend.firebase_auth import token_required
from apps.songs.models import Song, Artist, Album, SongArtist, AlbumSong, Genre, GenreSong
from spotipy.oauth2 import SpotifyClientCredentials
import os
import logging

# Create your views here.

@csrf_exempt
@token_required
def get_all_songs(request):
    users = Song.objects.all()
    context = {
        "users": list(users)
    }
    return JsonResponse(context, status=200)

@csrf_exempt
@token_required
def get_songs(request):
    if request.method == 'GET':
        data = request.GET
        track_name = data.get('song_name')

        if track_name is None:
            return JsonResponse({'error': 'Missing parameters'}, status=400)
        try:
            # Use filter instead of get to retrieve multiple songs with the same track name
            songs = Song.objects.filter(track_name=track_name)

            # Convert the list of song objects to a list of dictionaries for JsonResponse
            songs_info = []
            for song in songs:
                song_info = {
                    'song_id': song.song_id,
                    'track_name': song.track_name,
                    'release_year': song.release_year,
                    'length': song.length.total_seconds(),
                    'tempo': song.tempo,
                    'genre': song.genre,
                    'mood': song.mood,
                    'recommended_environment': song.recommended_environment,
                    'replay_count': song.replay_count,
                    'version': song.version,
                    # Add other fields as needed
                }
                songs_info.append(song_info)

            if songs_info:
                return JsonResponse({'message': 'Songs found', 'songs_info': songs_info}, status=200)
            else:
                return JsonResponse({'error': 'Songs not found'}, status=404)

        except Exception as e:
            logging.error(f"An unexpected error occurred: {str(e)}")
            return JsonResponse({'error': 'An unexpected error occurred'}, status=500)
    else:
        return JsonResponse({'error': 'Invalid method'}, status=400)
    
@csrf_exempt
@token_required
def get_song(request):
    if request.method == 'GET':
        data = request.GET
        track_id = data.get('song_id')
        if track_id is None:
            return JsonResponse({'error': 'Missing parameter'}, status=400)
        try:
            song = Song.objects.get(song_id=track_id)
            # Convert the song object to a dictionary for JsonResponse
            song_info = {
                'song_id': song.song_id,
                'track_name': song.track_name,
                'release_year': song.release_year,
                'length': song.length.total_seconds(),
                'tempo': song.tempo,
                'genre': song.genre,
                'mood': song.mood,
                'recommended_environment': song.recommended_environment,
                'replay_count': song.replay_count,
                'version': song.version,
            }
            return JsonResponse({'message': 'song found','song_info': song_info}, status=200)
        except Song.DoesNotExist:
            return JsonResponse({'error': 'Song not found'}, status=404)
    else:
        return JsonResponse({'error': 'Invalid method'}, status=400)
    
