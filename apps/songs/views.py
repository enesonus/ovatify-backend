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
def add_song(request):
    try:
        if request.method == 'POST':
            data = request.POST
            spotify_id = data.get('spotify_id')  # Add this line to get Spotify ID from the request

            if not spotify_id:
                return JsonResponse({'error': 'Spotify ID is required'}, status=400)

            client_credentials = SpotifyClientCredentials(client_id=os.getenv('SPOTIPY_CLIENT_ID'), client_secret=os.getenv('SPOTIPY_CLIENT_SECRET'))
            sp = spotipy.Spotify(client_credentials_manager=client_credentials)

            # Use the provided Spotify ID to get track information directly
            track = sp.track(spotify_id)

            if track:
                audio_features = sp.audio_features([track['id']])

                if audio_features:
                    audio_features = audio_features[0]
                    recommended_environment = 'L' if audio_features['liveness'] >= 0.8 else 'S'
                    tempo = 'F' if audio_features['tempo'] >= 120 else ('M' if 76 <= audio_features['tempo'] < 120 else 'S')
                    energy = audio_features['energy']
                    if 0 <= energy < 0.25:
                        mood = 'SA'  # Sad
                    elif 0.25 <= energy < 0.5:
                        mood = 'R'  # Relaxed
                    elif 0.5 <= energy < 0.75:
                        mood = 'H'  # Happy
                    else:
                        mood = 'E'
                    # Create necessary objects in the database
                    new_song = Song.objects.create(
                        track_name=track['name'],
                        release_year=track['album']['release_date'][:4],
                        length=track['duration_ms'],
                        replay_count=0,
                        tempo=tempo,
                        duration=track['duration_ms'],
                        recommended_environment=recommended_environment,
                        genre=track['artists'][0]['genres'][0] if track['artists'][0]['genres'] else '',
                        mood=mood,
                        version=track['album']['release_date'],
                    )

                    for artist in track['artists']:
                        if 'genres' in artist and artist['genres']:
                            for genre_name in artist['genres']:
                                if genre_name:
                                    genre, created = Genre.objects.get_or_create(genre_name=genre_name)
                                    genre_song, created = GenreSong.objects.get_or_create(genre=genre, song=new_song)

                    for artist in track['artists']:
                        artist_name = artist['name']
                        artist_instance, created = Artist.objects.get_or_create(name=artist_name)
                        song_artist, created = SongArtist.objects.get_or_create(artist=artist_instance, song=new_song)

                    return JsonResponse({'message': 'Song details fetched successfully'}, status=200)
                else:
                    return JsonResponse({'error': 'No audio features found for the song'}, status=400)
            else:
                return JsonResponse({'error': 'Song not found'}, status=400)
        else:
            return JsonResponse({'error': 'Invalid method'}, status=400)
    except KeyError as e:
        logging.error(f"A KeyError occurred: {str(e)}")
        return JsonResponse({'error': 'KeyError occurred'}, status=500)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {str(e)}")
        return JsonResponse({'error': 'An unexpected error occurred'}, status=500)
    
@csrf_exempt
@token_required
def search_songs(request):
    try:
        if request.method == 'GET':
            data = request.GET
            search_string = data.get('search_string')

            if search_string is None:
                return JsonResponse({'error': 'Missing search string'}, status=400)
            
            client_credentials = SpotifyClientCredentials(client_id=os.getenv('SPOTIPY_CLIENT_ID'), client_secret=os.getenv('SPOTIPY_CLIENT_SECRET'))
            sp = spotipy.Spotify(client_credentials_manager=client_credentials)

            results = sp.search(q=search_string, type='track', limit=10)

            search_list = []

            for track in results['tracks']['items']:
                song_info = {
                    'track_name': track['name'],
                    'album_name': track['album']['name'],
                    'artist': ', '.join([artist['name'] for artist in track['artists']]),
                    'release_year': track['album']['release_date'][:4],
                    'spotify_id': track['id'],                    
                }
                search_list.append(song_info)
            return JsonResponse({'message': 'Search successful', 'results': search_list}, status=200)
        else:
            return JsonResponse({'error': 'Invalid method'}, status=400)
            
    except KeyError as e:
        logging.error(f"A KeyError occurred: {str(e)}")
        return JsonResponse({'error': 'KeyError occurred'}, status=500)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {str(e)}")
        return JsonResponse({'error': 'An unexpected error occurred'}, status=500) 
      
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

