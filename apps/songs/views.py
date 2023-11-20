import json
from datetime import datetime, timedelta
import os
import logging
from django.http import JsonResponse, HttpResponse
from django.db.models import Count, Sum
from django.core.exceptions import ValidationError
from django.views.decorators.csrf import csrf_exempt
import spotipy
from OVTF_Backend.firebase_auth import token_required
from apps.songs.utils import bulk_get_or_create, get_artist_bio, clean_html_tags
from songs.models import (Instrument, Mood, RecordedEnvironment,
                          Song, Artist, Album, ArtistSong,
                          AlbumSong, Genre, GenreSong, Tempo)
from spotipy.oauth2 import SpotifyClientCredentials
from users.models import User, UserSongRating


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
        song_name = data.get('song_name')

        if song_name is None:
            return JsonResponse({'error': 'Missing parameters'}, status=400)
        try:
            # Use filter instead of get to retrieve multiple songs with the same track name
            songs = Song.objects.filter(name=song_name)

            # Convert the list of song objects to a list of dictionaries for JsonResponse
            songs_info = []
            for song in songs:
                song_info = {
                    'song_id': song.id,
                    'song_name': song.name,
                    'release_year': song.release_year,
                    'duration': song.duration.total_seconds(),
                    'tempo': song.tempo,
                    'mood': song.mood,
                    'recorded_environment': song.recorded_environment,
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
            song = Song.objects.get(id=track_id)
            # Convert the song object to a dictionary for JsonResponse
            song_info = {
                'id': song.id,
                'song_name': song.name,
                'release_year': song.release_year,
                'duration': song.duration.total_seconds(),
                'tempo': song.tempo,
                'mood': song.mood,
                'recorded_environment': song.recorded_environment,
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
            data = json.loads(request.body, encoding='utf-8')
            spotify_id = data.get('spotify_id')  # Add this line to get Spotify ID from the request
            rating = data.get('rating')

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
                    recorded_environment = RecordedEnvironment.LIVE if audio_features['liveness'] >= 0.8 else RecordedEnvironment.STUDIO
                    tempo = Tempo.FAST if audio_features['tempo'] >= 120 else (Tempo.MEDIUM if 76 <= audio_features['tempo'] < 120 else Tempo.SLOW)
                    energy = audio_features['energy']
                    if 0 <= energy < 0.25:
                        mood = Mood.SAD
                    elif 0.25 <= energy < 0.5:
                        mood = Mood.RELAXED
                    elif 0.5 <= energy < 0.75:
                        mood = Mood.HAPPY
                    else:
                        mood = Mood.EXCITED
                    # Create necessary objects in the database
                    new_song, created = Song.objects.get_or_create(
                        name=track['name'],
                        release_year=track['album']['release_date'][:4],
                        tempo=tempo,
                        duration=str(timedelta(seconds=int(track['duration_ms']/1000))),
                        recorded_environment=recorded_environment,
                        mood=mood,
                        img_url=track['album']['images'][0]['url'],
                        version=track['album']['release_date'],
                        img_url=track['album']['images'][0]['url']
                    )

                    if not created:
                        return JsonResponse({'message': 'Song already exists'}, status=403)
                    for artist in track['artists']:
                        if 'genres' in artist and artist['genres']:
                            for genre_name in artist['genres']:
                                if genre_name:
                                    genre, created = Genre.objects.get_or_create(name=genre_name)
                                    new_song.genres.add(genre)

                    for artist in track['artists']:
                        artist_name = artist['name']
                        artist_bio = get_artist_bio(artist_name)
                        artist_instance, created = Artist.objects.get_or_create(name=artist_name, img_url=artist['images'][0]['url'], bio=artist_bio)
                        new_song.artists.add(artist_instance)

                    album_name= track['album']['name']
                    album_instance, created = Album.objects.get_or_create(name=album_name, release_year=track['album']['release_date'][:4], img_url=track['album']['images'][0]['url'])
                    new_song.albums.add(album_instance)

                    if rating > 0 and rating <= 5:
                        try:
                            user = User.objects.get(id=userid)
                            user_song_rating, created = UserSongRating.objects.get_or_create(user=user, song=new_song, rating=rating)
                        except User.DoesNotExist:
                            return JsonResponse({'error': 'User not found'}, status=404)

                    return JsonResponse({'message': 'Song details added successfully'}, status=201)
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
                    'album_url' : track['album']['images'][0]['url'],
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
        required_fields = ['name', 'release_year', 'duration',
                           'tempo', 'mood', 'replay_count']
        for song_data in data:
            if not all(field in song_data for field in required_fields):
                return HttpResponse(status=400)
            recorded_environment = song_data.get('recorded_environment', None)
            replay_count = song_data.get('replay_count', None)
            img_url = song_data.get('img_url', None)
            genre_names = song_data.get('genres', None)
            artist_names = song_data.get('artists', None)
            album_names = song_data.get('albums', None)
            instrument_names = song_data.get('instruments', None)
            genres, artists, albums, instruments = [], [], [], []

            if img_url:
                song_data['img_url'] = img_url
            if recorded_environment:
                song_data['recorded_environment'] = recorded_environment
            if replay_count:
                song_data['replay_count'] = int(replay_count)
            if genre_names:
                existing_genres, new_genres = bulk_get_or_create(Genre, genre_names, 'name')
                genres.extend(existing_genres)
                genres.extend(new_genres)
                song_data.pop('genres', None)

            if artist_names:
                existing_artists, new_artists = bulk_get_or_create(Artist, artist_names, 'name')
                artists.extend(existing_artists)
                artists.extend(new_artists)
                song_data.pop('artists', None)

            if album_names:
                for album_name in album_names:
                    album, created = Album.objects.get_or_create(name=album_name, release_year=song_data['release_year'])
                    albums.append(album)
                song_data.pop('albums', None)

            if instrument_names:
                existing_instruments, new_instruments = bulk_get_or_create(Instrument, instrument_names, 'name')
                instruments.extend(existing_instruments)
                instruments.extend(new_instruments)
                song_data.pop('instruments', None)

            hours, minutes, seconds = map(int, song_data['duration'].split(':'))
            duration_timedelta = timedelta(hours=hours, minutes=minutes, seconds=seconds)
            song_data['duration'] = duration_timedelta

            song = Song(**song_data)
            song.save()

            song.genres.set(genres)
            song.artists.set(artists)
            song.albums.set(albums)
            song.instruments.set(instruments)

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
        genre = Genre(name=genre_name)
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
                song = Song.objects.get(id=song_id)
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
