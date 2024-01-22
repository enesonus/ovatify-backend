import json
from datetime import timedelta
import os
import logging
import random
from django.http import JsonResponse, HttpResponse
from django.db.models import Count, Sum, Q
from django.views.decorators.csrf import csrf_exempt
import spotipy
from OVTF_Backend.firebase_auth import token_required
from apps.songs.utils import bulk_get_or_create, flush_database, get_artist_bio, get_genres_and_artist_info, \
    getFirstRelatedSong, serializeSongMinimum
from songs.models import (Instrument, Mood, RecordedEnvironment,
                          Song, Artist, Album, ArtistSong,
                          AlbumSong, Genre, GenreSong, Tempo, Playlist, PlaylistSong)
from spotipy.oauth2 import SpotifyClientCredentials
from users.models import User, UserSongRating
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank, TrigramSimilarity


# Create your views here.

@csrf_exempt
@token_required
def get_all_songs(request, userid):
    songs = Song.objects.all().values().order_by('-created_at')
    context = {
        "users": list(songs)
    }
    return JsonResponse(context, status=200)

@csrf_exempt
@token_required
def search_db(request, userid):
    if request.method == 'GET':
        data = request.GET
        search_string = data.get('search_string', '')

        search_fields = ['name', 'albums', 'artists']

        if not search_string or not search_fields:
            return JsonResponse({'error': 'Missing parameters'}, status=400)

        # Prepare the search query and vector
        search_query = SearchQuery(search_string)
        search_vector = SearchVector('name', 'albums__name', 'artists__name')

        # Annotate each song with its search rank and trigram similarity
        songs = Song.objects.annotate(
            rank=SearchRank(search_vector, search_query),
            similarity=TrigramSimilarity('name', search_string) +
                       TrigramSimilarity('albums__name', search_string) +
                       TrigramSimilarity('artists__name', search_string)
        ).filter(
            Q(rank__gte=0.4) | 
            Q(similarity__gt=0.4)
        ).distinct('id')

        # Sort the results in Python to maintain the desired order
        sorted_songs = sorted(songs, key=lambda x: (-x.rank, -x.similarity))

        # Convert the sorted list to a list of song dictionaries for JsonResponse
        songs_info = []
        for song in sorted_songs:
            song_info = {
                'spotify_id': song.id,
                'track_name': song.name,
                'release_year': song.release_year,
                'album_name': [album.name for album in song.albums.all()],
                'artist': [artist.name for artist in song.artists.all()],
                'album_url': song.img_url,
            }
            songs_info.append(song_info)

        return JsonResponse({'message': 'Songs found', 'songs_info': songs_info}, status=200)

    else:
        return JsonResponse({'error': 'Invalid method'}, status=400)


@csrf_exempt
@token_required
def get_song_by_id(request, userid):
    if request.method != 'GET':
        return JsonResponse({'error': 'Invalid method'}, status=400)

    data = request.GET
    track_id = data.get('song_id')
    if track_id is None:
        return JsonResponse({'error': 'Missing parameter'}, status=400)

    try:
        song = Song.objects.get(id=track_id)
    except Song.DoesNotExist:
        return JsonResponse({'error': 'Song not found'}, status=404)

    # Convert the song object to a dictionary for JsonResponse
    genres = song.genres.all()
    genre_names = [genre.name for genre in genres]

    artists = song.artists.all()
    artist_names = [artist.name for artist in artists]

    albums = song.albums.all()
    album_names = [album.name for album in albums]

    instruments = song.instruments.all()
    instrument_names = [instrument.name for instrument in instruments]
    tempo_long_form = dict(Tempo.choices)[song.tempo]
    mood_long_form = dict(Mood.choices)[song.mood]
    recorded_environment_long_form = dict(RecordedEnvironment.choices)[song.recorded_environment]

    try:
        user = User.objects.get(id=userid)  # Assuming you have a User model
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)

    try:
        rating_aggregation = UserSongRating.objects.filter(song=song).aggregate(
            total_ratings=Count('rating'),
            sum_ratings=Sum('rating')
        )
        total_ratings = rating_aggregation['total_ratings']
        sum_ratings = rating_aggregation['sum_ratings']

        if total_ratings > 0:
            average_rating = sum_ratings / total_ratings
        else:
            average_rating = 0

        try:
            user_rating = UserSongRating.objects.get(user=user, song=song).rating
        except UserSongRating.DoesNotExist:
            user_rating = 0
    except UserSongRating.DoesNotExist:
        average_rating = 0
        user_rating = 0

    song_info = {
        'id': song.id,
        'name': song.name,
        'genres': genre_names,
        'artists': artist_names,
        'albums': album_names,
        'instruments': instrument_names,
        'release_year': song.release_year,
        'duration': song.duration.total_seconds(),
        'tempo': tempo_long_form,
        'mood': mood_long_form,
        'recorded_environment': recorded_environment_long_form,
        'replay_count': song.replay_count,
        'version': song.version,
        'img_url': song.img_url,
        'average_rating': round(average_rating,2),
        'user_rating': round(user_rating,2),
    }
    return JsonResponse({'message': 'song found', 'song_info': song_info}, status=200)



@csrf_exempt
@token_required
def add_song(request, userid):
    try:
        if request.method != 'POST':
            return JsonResponse({'error': 'Invalid method'}, status=400)
        else:
            data = json.loads(request.body, encoding='utf-8')
            spotify_id = data.get('spotify_id')  # Add this line to get Spotify ID from the request
            rating = float(data.get('rating'))

            if not spotify_id:
                return JsonResponse({'error': 'Spotify ID is required'}, status=400)

            client_credentials = SpotifyClientCredentials(client_id=os.getenv('SPOTIPY_CLIENT_ID'), client_secret=os.getenv('SPOTIPY_CLIENT_SECRET'))
            sp = spotipy.Spotify(client_credentials_manager=client_credentials)

            # Use the provided Spotify ID to get track information directly
            track = sp.track(spotify_id)

            if track is None:
                return JsonResponse({'error': 'Song not found'}, status=400)
            else:
                audio_features = sp.audio_features([track['id']])
                genres, artist_img = get_genres_and_artist_info(track, sp)

                if audio_features is None:
                    return JsonResponse({'error': 'No audio features found for the song'}, status=400)
                else:
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
                        id=spotify_id,
                        name=track['name'].title(),
                        release_year=track['album']['release_date'][:4],
                        tempo=tempo,
                        duration=str(timedelta(seconds=int(track['duration_ms']/1000))),
                        recorded_environment=recorded_environment,
                        mood=mood,
                        img_url=track['album']['images'][0]['url'],
                        version=track['album']['release_date'],
                    )
                    if created:
                        for genre_name in genres:
                            if genre_name:
                                genre, genre_created = Genre.objects.get_or_create(name=genre_name)
                                new_song.genres.add(genre)
                        
                        for artist in track['artists']:
                            artist_name = artist['name'].title()
                            artist_bio = get_artist_bio(artist_name)
                            artist_img_url = artist_img if artist_img is not None else None

                            db_artist = Artist.objects.filter(id=artist['id']).first()
                            if db_artist is None:
                                artist = Artist.objects.create(
                                                id=artist['id'],
                                                name=artist_name.title(),
                                                img_url=artist_img_url,
                                                bio=artist_bio)
                                db_artist = artist
                            if (db_artist.bio != artist_bio or
                                    db_artist.img_url != artist_img_url):
                                db_artist.bio = artist_bio
                                db_artist.img_url = artist_img_url
                                db_artist.save()
                            new_song.artists.add(db_artist)

                        album_name = track['album']['name'].title() if 'album' in track and 'name' in track['album'] else track['name'].title() + ' - Single'
                        album_instance, album_created = Album.objects.get_or_create(id = track['album']['id'] ,name=album_name, release_year=track['album']['release_date'][:4], img_url=track['album']['images'][0]['url'])
                        new_song.albums.add(album_instance)

                    if rating > 0 and rating <= 5:
                        try:
                            user = User.objects.get(id=userid)

                            existing_rating = UserSongRating.objects.filter(user=user, song=new_song)

                            if created and existing_rating.count() == 0:
                                user_song_rating, rating_created = \
                                UserSongRating.objects.get_or_create(user=user, song=new_song, rating=rating)
                                return JsonResponse({'message': f'Rating & song is added successfully'}, status=200)
                            elif not created and existing_rating.count() == 0:
                                UserSongRating.objects.get_or_create(user=user, song=new_song, rating=rating)
                                return JsonResponse({'message': f'Rating is added successfully'}, status=200)
                            else:
                                return JsonResponse({'message': f'You have already added this song, please update your rating via your library'}, status=400)
                        except User.DoesNotExist:
                            return JsonResponse({'error': 'User not found'}, status=404)
                    else:
                        if created:
                            return JsonResponse({'message': f'Song added successfully'}, status=201)
                        else:
                            return JsonResponse({'message': f'You have already added this song'}, status=400)
    except KeyError as e:
        logging.error(f"A KeyError occurred: {str(e)}")
        return JsonResponse({'error': f"A KeyError occurred: {str(e)}"}, status=500)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {str(e)}")
        return JsonResponse({'error': f'An unexpected error occurred: {str(e)}'}, status=500)
    
@csrf_exempt
@token_required
def search_spotify(request, userid):
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


@csrf_exempt
@token_required
def get_demanded_genres(request, userid):
    if request.method != 'GET':
        return HttpResponse(status=405)
    try:
        data = request.GET
        number_of_genres = data.get('number_of_genres')
        if not number_of_genres:
            return JsonResponse({'error': 'Missing number of genres'}, status=400)
        number_of_genres = int(number_of_genres)
        if number_of_genres < -1 or number_of_genres == 0:
            return JsonResponse({'error': 'Invalid number of genres'}, status=400)
        if number_of_genres == -1:
            genres = Genre.objects.all().values().order_by('-updated_at')
        else:
            genres = Genre.objects.all().values().order_by('-updated_at')[:number_of_genres]
        serialized_genres = [
            {
                'id': genre['id'],
                'name': genre['name'],
            }
            for genre in genres

        ]
        return JsonResponse({'genres': serialized_genres}, status=200)
    except ValueError:
        return JsonResponse({'error': 'Invalid number of genres'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@token_required
def get_songs_by_genre(request, userid):
    if request.method != 'GET':
        return HttpResponse(status=405)
    try:
        data = request.GET
        number_of_songs = data.get('number_of_songs')
        if not number_of_songs:
            return JsonResponse({'error': 'Missing number of songs'}, status=400)
        number_of_songs = int(number_of_songs)
        if number_of_songs < -1 or number_of_songs == 0:
            return JsonResponse({'error': 'Invalid number of songs'}, status=400)
        genre_name: str = data.get('genre_name')
        if not genre_name:  # if Genre Name is not provided
            return JsonResponse({'error': 'Missing genre name'}, status=400)
        genre_name = genre_name.title()
        if number_of_songs == -1:
            songs = Song.objects.filter(genres__name=genre_name).order_by('-created_at').all()
        else:
            songs = Song.objects.filter(genres__name=genre_name).order_by('-created_at')[:number_of_songs]
        serialized_songs = [
            {
                'id': song.id,
                'name': song.name,
                'release_year': song.release_year,
                'main_artist': song.artists.first().name if song.artists.exists() else "Unknown",
                'img_url': song.img_url
            }
            for song in songs
        ]
        return JsonResponse({'songs': serialized_songs}, status=200)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User does not exist'}, status=404)
    except ValueError:
        return JsonResponse({'error': 'Invalid number of songs'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@token_required
def get_genres_of_a_song(request, userid):
    if request.method != 'GET':
        return HttpResponse(status=405)
    try:
        data = request.GET
        song_id = data.get('song_id')
        if song_id is None:
            return JsonResponse({'error': 'Missing song id'}, status=400)
        try:
            song = Song.objects.get(id=song_id)
        except Song.DoesNotExist:
            return JsonResponse({'error': 'Song not found'}, status=404)
        genres = song.genres.all().values()
        serialized_genres = [
            {
                'id': genre['id'],
                'name': genre['name'],
            }
            for genre in genres
        ]
        return JsonResponse({'genres': serialized_genres}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@token_required
def get_random_genres(request, userid):
    if request.method != 'GET':
        return HttpResponse(status=405)
    try:
        data = request.GET
        number_of_genres = data.get('number_of_genres', 10)
        number_of_genres = int(number_of_genres)
        if number_of_genres <= 0:
            return JsonResponse({'error': 'Invalid number of genres'}, status=400)
        genres = Genre.objects.annotate(num_songs=Count('genresong'))\
                              .order_by('-num_songs')[:number_of_genres]
        serialized_genres = [
            {
                'id': genre.id,
                'name': genre.name,
                'img_url': getFirstRelatedSong(genre.id)
            }
            for genre in genres
        ]
        return JsonResponse({'genres': serialized_genres}, status=200)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User does not exist'}, status=404)
    except ValueError:
        return JsonResponse({'error': 'Invalid number of genres'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@token_required
def search_artists(request, userid):
    if request.method == 'GET':
        data = request.GET
        search_text = data.get('search_text')
        number_of_artists = data.get('number_of_artists', 10)
        if search_text:
            # Prepare the search query and vector
            search_query = SearchQuery(search_text)
            search_vector = SearchVector('name')

            # Annotate each song with its search rank and trigram similarity
            artists = Artist.objects.annotate(
                rank=SearchRank(search_vector, search_query),
                similarity=TrigramSimilarity('name', search_text)
            ).filter(
                Q(rank__gte=0.2) |
                Q(similarity__gt=0.2))\
             .order_by("-similarity")[:number_of_artists]

        else:
            return JsonResponse({'error': 'Missing search text'},
                                status=400)

        artists_info = [
            {
                'name': artist.name,
            }
            for artist in artists
        ]

        return JsonResponse({'message': 'Artists found', 'artists_info': artists_info}, status=200)

    else:
        return JsonResponse({'error': 'Invalid method'}, status=400)


@csrf_exempt
@token_required
def search_genres(request, userid):
    if request.method == 'GET':
        data = request.GET
        search_text = data.get('search_text')
        number_of_genres = data.get('number_of_genres', 10)
        if search_text:
            # Prepare the search query and vector
            search_query = SearchQuery(search_text)
            search_vector = SearchVector('name')

            # Annotate each song with its search rank and trigram similarity
            genres = Genre.objects.annotate(
                rank=SearchRank(search_vector, search_query),
                similarity=TrigramSimilarity('name', search_text)
            ).filter(
                Q(rank__gte=0.2) |
                Q(similarity__gt=0.2))\
             .order_by("-similarity")[:number_of_genres]
        else:
            return JsonResponse({'error': 'Missing search text'},
                                status=400)
        genres_info = [
            {
                'name': genre.name,
            }
            for genre in genres
        ]

        return JsonResponse({'message': 'Genres found',
                             'genres_info': genres_info},
                            status=200)

    else:
        return JsonResponse({'error': 'Invalid method'},
                            status=400)


@csrf_exempt
@token_required
def get_all_moods(request, userid):
    if request.method == 'GET':
        moods = [{'value': mood[0], 'label': mood[1]}
                 for mood in Mood.choices]
        return JsonResponse({'message': 'All moods',
                             'moods': moods},
                            status=200)
    else:
        return JsonResponse({'error': 'Invalid method'},
                            status=400)


@csrf_exempt
@token_required
def get_all_tempos(request, userid):
    if request.method == 'GET':
        tempos = [{'value': tempo[0], 'label': tempo[1]}
                  for tempo in Tempo.choices]
        return JsonResponse({'message': 'All tempos', 'tempos': tempos}, status=200)
    else:
        return JsonResponse({'error': 'Invalid method'}, status=400)


@csrf_exempt
@token_required
def get_banger_songs(request, userid):
    if request.method == 'GET':
        data = request.GET  # Use GET instead of POST for query parameters

        artist_name = data.get('artist')
        genre_name = data.get('genre')
        mood = data.get('mood')
        tempo = data.get('tempo')
        
        valid_params = {"artist_name": artist_name,
                        "genre_name": genre_name,
                        "mood": mood,
                        "tempo": tempo}

        for key in list(valid_params):
            if valid_params[key] is None:
                del valid_params[key]

        if len(valid_params) == 0:
            return JsonResponse({'error': 'No filters provided'}, status=400)

        songs = None

        if "artist_name" in valid_params and artist_name != "":
            if songs is None:
                songs = Song.objects.filter(artists__name__iexact=artist_name)
            else:
                songs = songs.filter(artists__name__iexact=artist_name)

        if "genre_name" in valid_params and genre_name != "":
            if songs is None:
                songs = Song.objects.filter(genres__name__iexact=genre_name)
            else:
                songs = songs.filter(genres__name__iexact=genre_name)

        if "mood" in valid_params and mood != "":
            if songs is None:
                songs = Song.objects.filter(mood=mood)
            else:
                songs = songs.filter(mood=mood)

        if "tempo" in valid_params and tempo != "":
            if songs is None:
                songs = Song.objects.filter(tempo=tempo)
            else:
                songs = songs.filter(tempo=tempo)

        # Randomize the order and retrieve one song
        if songs.exists():
            ids = songs.values_list('id', flat=True)
            random_id = random.sample(list(ids), 1)[0]
            random_song = songs.get(id=random_id)

            song_info = serializeSongMinimum(random_song)

            return JsonResponse({'message': 'Random Banger song found', 'song_info': song_info}, status=200)
        else:
            return JsonResponse({'message': 'No Banger songs found with the given filters'}, status=404)

    else:
        return JsonResponse({'error': 'Invalid method'}, status=400)


@csrf_exempt
@token_required
def save_playlist(request, userid):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            user = User.objects.get(id=userid)

            playlist = Playlist.objects.create(
                name=data['name'],
                description=data['description'],
                user=user
            )

            songs_data = data.get('songs', [])
            for song_id in songs_data:
                song = Song.objects.get(id=song_id)

                playlist_song = PlaylistSong.objects.create(playlist=playlist, song=song)
                playlist.songs.add(playlist_song)

            playlist.save()

            return JsonResponse({'playlist_id': playlist.id}, status=201)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)

        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)

        except Song.DoesNotExist:
            return JsonResponse({'error': 'One or more songs not found'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=405)
