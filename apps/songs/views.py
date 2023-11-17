import json
from datetime import timedelta
from django.db.models import Count, Sum
from django.http import JsonResponse, HttpResponse
from django.core.exceptions import ValidationError
from django.views.decorators.csrf import csrf_exempt
import spotipy
from OVTF_Backend.firebase_auth import token_required
from apps.songs.models import Song, Artist, Album, SongArtist, AlbumSong, Genre, GenreSong
from users.models import UserSongRating
from spotipy.oauth2 import SpotifyClientCredentials
import os
import logging


# Create your views here.

@csrf_exempt
@token_required
def get_all_songs(request, userid):
    songs = Song.objects.all().values()
    context = {
        "users": list(songs)
    }
    return JsonResponse(context, status=200)


@csrf_exempt
@token_required
def get_songs(request, userid):
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
def get_song(request, userid):
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
            return JsonResponse({'message': 'song found', 'song_info': song_info}, status=200)
        except Song.DoesNotExist:
            return JsonResponse({'error': 'Song not found'}, status=404)
    else:
        return JsonResponse({'error': 'Invalid method'}, status=400)


@csrf_exempt
@token_required
def add_song(request, userid):
    try:
        if request.method == 'POST':
            data = request.POST
            spotify_id = data.get('spotify_id')  # Add this line to get Spotify ID from the request

            if not spotify_id:
                return JsonResponse({'error': 'Spotify ID is required'}, status=400)

            client_credentials = SpotifyClientCredentials(client_id=os.getenv('SPOTIPY_CLIENT_ID'),
                                                          client_secret=os.getenv('SPOTIPY_CLIENT_SECRET'))
            sp = spotipy.Spotify(client_credentials_manager=client_credentials)

            # Use the provided Spotify ID to get track information directly
            track = sp.track(spotify_id)

            if track:
                audio_features = sp.audio_features([track['id']])

                if audio_features:
                    audio_features = audio_features[0]
                    recommended_environment = 'L' if audio_features['liveness'] >= 0.8 else 'S'
                    tempo = 'F' if audio_features['tempo'] >= 120 else (
                        'M' if 76 <= audio_features['tempo'] < 120 else 'S')
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
def search_songs(request, userid):
    try:
        if request.method == 'GET':
            data = request.GET
            search_string = data.get('search_string')

            if search_string is None:
                return JsonResponse({'error': 'Missing search string'}, status=400)

            client_credentials = SpotifyClientCredentials(client_id=os.getenv('SPOTIPY_CLIENT_ID'),
                                                          client_secret=os.getenv('SPOTIPY_CLIENT_SECRET'))
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


@csrf_exempt
@token_required
def import_song_JSON(request, userid):
    if request.method != 'POST':
        return HttpResponse(status=405)
    try:
        if 'file' in request.FILES:
            file = request.FILES['file']
            data = json.load(file)
        else:
            return JsonResponse({'error': 'No file provided'}, status=400)
        if isinstance(data, dict):
            data = [data]
        required_fields = ['track_name', 'release_year', 'length',
                           'tempo', 'genre', 'mood',
                           'recommended_environment', 'duration', 'replay_count', 'version']
        for song_data in data:
            # Assuming genre_id is provided in song_data to link Song with Genre
            # return JsonResponse(song_data, safe=False, status=200)
            if not all(field in song_data for field in required_fields):
                return HttpResponse(status=400)
            genre_name = song_data.get('genre', None)
            genre, created = Genre.objects.get_or_create(genre_name=genre_name)
            song_data['genre'] = genre
            hours, minutes, seconds = map(int, song_data['length'].split(':'))
            length_timedelta = timedelta(hours=hours, minutes=minutes, seconds=seconds)
            song_data['length'] = length_timedelta
            song = Song(**song_data)
            song.full_clean()
            song.save()

        return HttpResponse(status=201)
    except json.JSONDecodeError as e:
        logging.error(f"JSON decode error: {e}")
        return HttpResponse(status=400)
    except ValidationError as e:
        return JsonResponse({'errors': e.message_dict}, status=400)
    except Genre.DoesNotExist:
        return HttpResponse("Genre not found.", status=400)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return HttpResponse(status=500)


@csrf_exempt
def create_genre(request):
    if request.method != 'POST':
        return HttpResponse(status=405)
    try:
        data = json.loads(request.body.decode('utf-8'))
        genre_name = data.get('genre_name')
        if genre_name is None:
            return HttpResponse(status=400)
        genre = Genre(genre_name=genre_name)
        genre.save()
        return HttpResponse(status=201)
    except Exception as e:
        # TODO logging.("create_user: " + str(e))
        return HttpResponse(status=500)


@csrf_exempt
def get_all_genres(request):
    if request.method != 'GET':
        return HttpResponse(status=405)
    try:
        genres = Genre.objects.all().values()
    except Exception as e:
        return JsonResponse({"error": "Database error"}, status=500)

    context = {
        "genres": list(genres)
    }
    return JsonResponse(context, status=200)

@csrf_exempt
def average_song_rating(request):
    try:
        if request.method == 'GET':
            data = request.GET
            song_id = data.get('song_id')

            if song_id is None:
                return JsonResponse({'error': 'Missing song id'}, status=400)
            
            try:
                song = Song.objects.get(song_id=song_id)
            except Song.DoesNotExist:
                return JsonResponse({'error': 'Song not found'}, status=404)
            
            try:
                rating_aggregation = UserSongRating.objects.filter(song=song).aggregate(
                    total_ratings=Count('rating'),
                    sum_ratings=Sum('rating')
                )

                total_ratings = rating_aggregation['total_ratings']
                sum_ratings = rating_aggregation['sum_ratings']

                if total_ratings > 0:
                    average_rating = sum_ratings / total_ratings
                    return JsonResponse({'average_rating': average_rating}, status=200)
                else:
                    return JsonResponse({'error': 'No ratings available for this song'}, status=404)
            except UserSongRating.DoesNotExist:
                return JsonResponse({'error': 'No ratings available for this song'}, status=404)
    except KeyError as e:
        logging.error(f"A KeyError occurred: {str(e)}")
        return JsonResponse({'error': 'KeyError occurred'}, status=500)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {str(e)}")
        return JsonResponse({'error': 'An unexpected error occurred'}, status=500)