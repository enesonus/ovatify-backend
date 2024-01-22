import json
import logging
import tempfile
from collections import Counter
from datetime import datetime, timedelta
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import Prefetch, DateField, Count, Sum
from django.db.models.functions import TruncDay
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from OVTF_Backend.firebase_auth import token_required
import spotipy
from songs.utils import serializePlaylist, serializePlaylistInfo
from users.utils import recommendation_creator, serializeFriendGroupSimple, serializeFriendGroupExtended
from songs.models import (Playlist, Song,
                          Genre, Mood, Tempo,
                          GenreSong, ArtistSong,
                          Artist, AlbumSong, Album,
                          InstrumentSong,
                          RecordedEnvironment,
                          Instrument, PlaylistSong
                          )
from users.models import (SuggestionNotification, User, UserPreferences,
                          UserSongRating, Friend,
                          FriendRequest,
                          RequestStatus, FriendGroup,
                          )
from users.utils import (get_recommendations,
                         getFavoriteGenres,
                         getFavoriteSongs,
                         getFavoriteArtists,
                         getFavoriteMoods,
                         getFavoriteTempos,
                         )
from spotipy.oauth2 import SpotifyClientCredentials
import os
import random

# Create endpoints

@csrf_exempt
@token_required
def get_all_users(request, userid):
    if request.method != 'GET':
        return HttpResponse(status=405)
    # retrieve all users from database
    try:
        users = User.objects.all().values()
    except Exception as e:
        return JsonResponse({"error": "Database error"}, status=500)

    context = {
        "users": list(users)
    }
    return JsonResponse(context, status=200)


@csrf_exempt
@token_required
def return_post_body(request, userid):
    # Return userid with 200 status code
    return JsonResponse({"userid": userid}, status=200)

    data = json.loads(request.body.decode('utf-8'))
    username = None
    if data.get('username') is not None:
        username = data['username']

    context = {
        "received": True,
        "username": username,
        "data": data
    }
    return JsonResponse(context, status=200)


@csrf_exempt
@token_required
def login(request, userid):
    if request.method != 'PUT':
        return HttpResponse(status=405)
    try:
        #get the user from the database
        user = User.objects.get(id=userid)
        user.last_login = timezone.now()
        user.save()
    except Exception as e:
        return JsonResponse({"error": "Database error"}, status=500)
    return JsonResponse({}, status=200)


@csrf_exempt
@token_required
def create_user(request, userid):
    if request.method != 'POST':
        return HttpResponse(status=405)
    try:
        data = json.loads(request.body.decode('utf-8'))
        email: str = data.get('email')
        #return the email in the response
        if email is None:  # if email is not provided
            return HttpResponse(status=400)
        if User.objects.filter(email=email).exists():  # if user already exists
            return HttpResponse(status=400)
        random_username: str = email.split('@')[0][:6] + str(datetime.now().timestamp()).split('.')[0]
        user = User.objects.create(id=userid, username=random_username, email=email, last_login=timezone.now())
        if not UserPreferences.objects.filter(user=user).exists():
            UserPreferences.objects.create(user=user, data_processing_consent=True, data_sharing_consent=True)
        return HttpResponse(status=201)
    except Exception as e:
        #TODO logging.("create_user: " + str(e))
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@token_required
def delete_user(request, userid):
    if request.method != 'DELETE':
        return HttpResponse(status=405)
    try:
        user = User.objects.get(id=userid)
        user.hard_delete()
        return HttpResponse(status=204)
    except Exception as e:
        return HttpResponse(status=404)


@csrf_exempt
@token_required
def update_user(request, userid):
    if request.method != 'PUT':
        return HttpResponse(status=405)
    try:
        #get the form data from the request and get email field from the form data
        email = request.POST.get('email')
        #TODO update the fields according to what the user wants to update
        return HttpResponse(status=204)
    except Exception as e:
        return HttpResponse(status=404)

@csrf_exempt
@token_required
def user_songs_view(request, user_id):
    try:
        user_ratings = UserSongRating.objects.filter(user=user_id)

        song_ids = user_ratings.values_list('song', flat=True)
        print(song_ids)
        songs = Song.objects.filter(id__in=song_ids)
        if songs is None or len(songs) == 0:
            return JsonResponse({'error': "no song found"},status = 404)
        serialized_songs = [
    {
        'id': song.id,
        'name': song.name,
        'release_year': song.release_year,
        'duration': song.duration.total_seconds(),  # Convert DurationField to seconds
        'tempo': song.tempo, # Assuming Genre has a 'name' attribute
        'mood': song.mood,
        'recorded_environment': song.recorded_environment,
        'duration': song.duration,
        'replay_count': song.replay_count,
        'version': song.version,
    }
    for song in songs
]
        return JsonResponse({'songs': serialized_songs})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@token_required
def user_preferences_create(request,userid):
    try:
        data = json.loads(request.body.decode('utf-8'))
        try:
            user= User.objects.get(username=data.get('user'))
        except User.DoesNotExist:
            return JsonResponse({'error': 'user not found'}, status=404)
        user_preferences,preferences_created= UserPreferences.objects.get_or_create(user=user, data_processing_consent=data.get('data_processing_consent', True),data_sharing_consent = data.get('data_sharing_consent', True))

        if preferences_created:
            return JsonResponse({'message': 'UserPreferences created successfully.'}, status=201)
        else:
            return JsonResponse({'message': 'UserPreferences updated successfully.'}, status=200)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@token_required
def hello_github(request):
    return JsonResponse({'message': 'Congrats from Ovatify Team!'}, status=200)


@csrf_exempt
@token_required
def add_song_rating(request, userid):
    try:
        if request.method == 'POST':
            data = json.loads(request.body, encoding='utf-8')
            song_id = data.get('song_id')
            rating = float(data.get('rating'))

            if userid is None or song_id is None or rating is None:
                return JsonResponse({'error': 'Missing parameter'}, status=400)

            try:
                user = User.objects.get(id=userid)
            except User.DoesNotExist:
                return JsonResponse({'error': 'User not found'}, status=404)

            try:
                song = Song.objects.get(id=song_id)
            except Song.DoesNotExist:
                return JsonResponse({'error': 'Song not found'}, status=404)

            try:
                user_rating, created_rating = UserSongRating.objects.get_or_create(user=user, song=song, rating=rating)

                if not created_rating:
                    return JsonResponse({'error': 'User rating already exists'}, status=400)
                return JsonResponse({'message': 'User rating added successfully'}, status=201)
            except IntegrityError:
                return JsonResponse({'error': 'Integrity Error: Invalid user or song reference'}, status=404)
        else:
            return JsonResponse({'error': 'Invalid method'}, status=400)
    except KeyError as e:
        logging.error(f"A KeyError occurred: {str(e)}")
        return JsonResponse({'error': f'KeyError occurred : {str(e)}'}, status=500)
    except ValueError as e:
        logging.error(f"A ValueError occurred: {str(e)}")
        return JsonResponse({'error': f'Invalid data format: {str(e)}'}, status=400)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {str(e)}")
        return JsonResponse({'error': f'An unexpected error occurred{str(e)}'}, status=500)


@csrf_exempt
@token_required
def remove_friend(request, userid):
    try:
        if request.method != 'DELETE':
            return HttpResponse(status=405)

        data = request.GET
        friend_username = data.get('friend_username')

        user = User.objects.get(id=userid)
        friend = User.objects.get(username=friend_username)

        # Check if the friendship exists
        if not user.friends.filter(id=friend.id).exists():
            return JsonResponse({'detail': 'Friendship does not exist'},
                                status=400)

        # Remove the friend relationship using .remove() method
        user.friends.remove(friend)

        return JsonResponse({'detail': 'Friend removed successfully'},
                            status=200)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@token_required
def add_friend(request, userid):
    try:
        if request.method != 'POST':
            return HttpResponse(status=405)

        data = json.loads(request.body, encoding='utf-8')
        friend_id = data.get('friend_id')

        user = User.objects.get(id=userid)
        friend = User.objects.get(id=friend_id)

        # Check if the friendship already exists
        if Friend.objects.filter(user=user, friend=friend).exists():
            return JsonResponse({'detail': 'Friendship already exists'},
                                status=400)

        # Modify the existing friend relationship by using .add() method
        user.friends.add(friend)

        return JsonResponse({'detail': 'Friend added successfully'},
                            status=200)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@token_required
def edit_song_rating(request, userid):
    try:
        if request.method == 'PUT':
            data = json.loads(request.body, encoding='utf-8')
            song_id = data.get('song_id')
            rating = float(data.get('rating'))

            if userid is None or song_id is None or rating is None:
                return JsonResponse({'error': 'Missing parameter'}, status=400)

            try:
                user = User.objects.get(id=userid)
            except User.DoesNotExist:
                return JsonResponse({'error': 'User not found'}, status=404)

            try:
                song = Song.objects.get(id=song_id)
            except Song.DoesNotExist:
                return JsonResponse({'error': 'Song not found'}, status=404)

            try:
                user_rating = UserSongRating.objects.get(user=user, song=song)
            except UserSongRating.DoesNotExist:
                return JsonResponse({'error': 'User rating not found'}, status=404)

            user_rating.delete()

            new_user_rating = UserSongRating(
                user=user,
                song=song,
                rating=rating,
            )
            new_user_rating.save()

            return JsonResponse({'message': 'User rating updated successfully'}, status=201)
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
def delete_song_rating(request, userid):
    try:
        if request.method == 'DELETE':
            data = request.GET
            song_id = data.get('song_id')

            if userid is None or song_id is None:
                return JsonResponse({'error': 'Missing parameter'}, status=400)

            try:
                user = User.objects.get(id=userid)
            except User.DoesNotExist:
                return JsonResponse({'error': 'User not found'}, status=404)

            try:
                song = Song.objects.get(id=song_id)
            except Song.DoesNotExist:
                return JsonResponse({'error': 'Song not found'}, status=404)

            try:
                user_rating = UserSongRating.objects.get(user=user, song=song)
            except UserSongRating.DoesNotExist:
                return JsonResponse({'error': 'User rating not found'}, status=404)

            user_rating.delete()

            return JsonResponse({'message': 'User rating deleted successfully'}, status=204)
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
def user_songs_with_genre(request, userid):
    if request.method != 'GET':
        return HttpResponse(status=405)
    try:
        data = request.GET
        number_of_songs: int = data.get('number_of_songs', 10)
        number_of_songs = int(number_of_songs)
        genre_name: str = data.get('genre_name')
        if genre_name is None:  # if Genre Name is not provided
            return HttpResponse(status=400)
        genre_name = genre_name.title()
        user = User.objects.get(id=userid)
        user_songs_ratings = user.usersongrating_set.prefetch_related('song').all()[:number_of_songs]
        songs = [song_rating.song for song_rating in user_songs_ratings]  # Get the song objects from the ratings
        matching_songs = []
        for song in songs:
            song_genre_table = song.genresong_set.prefetch_related('genre').all()
            all_genres = [genre_song.genre for genre_song in song_genre_table]
            for genre in all_genres:
                if genre.name == genre_name:
                    matching_songs.append(song)
                    break
        serialized_songs = [
            {
                'id': song.id,
                'name': song.name,
                'release_year': song.release_year,
                'duration': song.duration.total_seconds(),  # Convert DurationField to seconds
                'tempo':  Tempo(song.tempo).label,
                'mood': Mood(song.mood).label,
                'recorded_environment': RecordedEnvironment(song.recorded_environment).label,
                'replay_count': song.replay_count,
                'version': song.version,
                'img_url': song.img_url
            }
            for song in matching_songs
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
def user_songs_with_artist(request, userid):
    if request.method != 'GET':
        return HttpResponse(status=405)
    try:
        data = request.GET
        number_of_songs: int = data.get('number_of_songs', 10)
        number_of_songs = int(number_of_songs)
        artist_name: str = data.get('artist_name')
        if artist_name is None:  # if Artist Name is not provided
            return HttpResponse(status=400)
        artist_name = artist_name.title()
        user = User.objects.get(id=userid)
        user_songs_ratings = user.usersongrating_set.prefetch_related('song').all()[:number_of_songs]
        songs = [song_rating.song for song_rating in user_songs_ratings]  # Get the song objects from the ratings
        matching_songs = []
        for song in songs:
            song_artist_table = song.artistsong_set.prefetch_related('artist').all()
            all_artists = [artist_song.artist for artist_song in song_artist_table]
            for artist in all_artists:
                if artist.name == artist_name:
                    matching_songs.append(song)
                    break
        serialized_songs = [
            {
                'id': song.id,
                'name': song.name,
                'release_year': song.release_year,
                'duration': song.duration.total_seconds(),  # Convert DurationField to seconds
                'tempo':  Tempo(song.tempo).label,
                'mood':  Mood(song.mood).label,
                'recorded_environment': RecordedEnvironment(song.recorded_environment).label,
                'replay_count': song.replay_count,
                'version': song.version,
                'img_url': song.img_url
            }
            for song in matching_songs
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
def user_songs_with_tempo(request, userid):
    if request.method != 'GET':
        return HttpResponse(status=405)
    try:
        data = request.GET
        number_of_songs: int = data.get('number_of_songs', 10)
        number_of_songs = int(number_of_songs)
        tempo_name: str = data.get('tempo_name')
        if tempo_name is None:  # if Tempo Name is not provided
            return HttpResponse(status=400)
        tempo_name = tempo_name.capitalize()
        user = User.objects.get(id=userid)
        user_songs_ratings = user.usersongrating_set.prefetch_related('song').all()[:number_of_songs]
        songs = [song_rating.song for song_rating in user_songs_ratings]  # Get the song objects from the ratings
        matching_songs = []
        for song in songs:
            tempo_label = Tempo(song.tempo).label
            if tempo_label == tempo_name:
                matching_songs.append(song)
        serialized_songs = [
            {
                'id': song.id,
                'name': song.name,
                'release_year': song.release_year,
                'duration': song.duration.total_seconds(),  # Convert DurationField to seconds
                'tempo': Tempo(song.tempo).label,
                'mood': Mood(song.mood).label,
                'recorded_environment': RecordedEnvironment(song.recorded_environment).label,
                'replay_count': song.replay_count,
                'version': song.version,
                'img_url': song.img_url
            }
            for song in matching_songs
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
def user_songs_with_mood(request, userid):
    if request.method != 'GET':
        return HttpResponse(status=405)
    try:
        data = request.GET
        number_of_songs: int = data.get('number_of_songs', 10)
        number_of_songs = int(number_of_songs)
        mood_name: str = data.get('mood_name')
        if mood_name is None:  # if Mood Name is not provided
            return HttpResponse(status=400)
        mood_name = mood_name.capitalize()
        user = User.objects.get(id=userid)
        user_songs_ratings = user.usersongrating_set.prefetch_related('song').all()[:number_of_songs]
        songs = [song_rating.song for song_rating in user_songs_ratings]  # Get the song objects from the ratings
        matching_songs = []
        for song in songs:
            mood_label = Mood(song.mood).label
            if mood_label == mood_name:
                matching_songs.append(song)
        serialized_songs = [
            {
                'id': song.id,
                'name': song.name,
                'release_year': song.release_year,
                'duration': song.duration.total_seconds(),  # Convert DurationField to seconds
                'tempo': Tempo(song.tempo).label,
                'mood':  Mood(song.mood).label,
                'recorded_environment': RecordedEnvironment(song.recorded_environment).label,
                'replay_count': song.replay_count,
                'version': song.version,
                'img_url': song.img_url
            }
            for song in matching_songs
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
def get_all_user_songs(request, userid):
    if request.method != 'GET':
        return HttpResponse(status=405)
    # retrieve all users from database
    try:
        users = UserSongRating.objects.all().values()
    except Exception as e:
        return JsonResponse({"error": "Database error"}, status=500)

    context = {
        "usersongs": list(users)
    }
    return JsonResponse(context, status=200)


@csrf_exempt
@token_required
def get_recently_added_songs(request, userid):
    if request.method != 'GET':
        return HttpResponse(status=405)
    try:
        data = request.GET
        number_of_songs = data.get('number_of_songs')
        user = User.objects.get(id=userid)
        if number_of_songs is None:
            user_songs_ratings = user.usersongrating_set.prefetch_related('song').order_by('-created_at').all()
        else:
            number_of_songs = int(number_of_songs)
            user_songs_ratings = user.usersongrating_set.prefetch_related('song').order_by('-created_at')[:number_of_songs]
        songs = [song_rating.song for song_rating in user_songs_ratings] # Get the song objects from the ratings
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
def get_favorite_songs(request, userid):
    if request.method != 'GET':
        return HttpResponse(status=405)
    try:
        data = request.GET
        number_of_songs = data.get('number_of_songs')
        user = User.objects.get(id=userid)
        if number_of_songs is None:
            user_songs_ratings = user.usersongrating_set.prefetch_related('song')\
                .order_by('-rating', '-updated_at').all()
        else:
            number_of_songs = int(number_of_songs)
            user_songs_ratings = user.usersongrating_set.prefetch_related('song').order_by('-rating', '-updated_at')[:number_of_songs]
        songs = [song_rating.song for song_rating in user_songs_ratings]  # Get the song objects from the ratings
        # ratings = [song_rating.rating for song_rating in user_songs_ratings]  # In case we want to retrieve ratings
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
        return JsonResponse({'songs': serialized_songs},   status=200)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User does not exist'}, status=404)
    except ValueError:
        return JsonResponse({'error': 'Invalid number of songs'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@token_required
def get_favorite_genres(request, userid):
    if request.method != 'GET':
        return HttpResponse(status=405)
    try:
        data = request.GET
        number_of_songs = data.get('number_of_songs')
        limit = data.get('limit')
        if limit:
            limit = int(limit)
        user = User.objects.get(id=userid)
        if number_of_songs is None:
            user_songs_ratings = user.usersongrating_set.prefetch_related('song').order_by('-rating').all()

        else:
            number_of_songs = int(number_of_songs)
            user_songs_ratings = user.usersongrating_set.prefetch_related('song').order_by('-rating')[:number_of_songs]
        songs = [song_rating.song for song_rating in user_songs_ratings]
        genre_counts = Counter()
        for song in songs:
            song_genre_table = song.genresong_set.prefetch_related('genre').all()
            all_genres = [genre_song.genre for genre_song in song_genre_table]
            for genre in all_genres:
                genre_counts[genre.name] += 1
        if not limit:
            return JsonResponse(dict(genre_counts.most_common(10)), status=200)
        else:
            return JsonResponse(dict(genre_counts.most_common(limit)), status=200)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User does not exist'}, status=404)
    except ValueError:
        return JsonResponse({'error': 'Invalid parameters'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@token_required
def get_favorite_artists(request, userid):
    if request.method != 'GET':
        return HttpResponse(status=405)
    try:
        data = request.GET
        number_of_songs = data.get('number_of_songs')
        limit = data.get('limit')
        if limit:
            limit = int(limit)
        user = User.objects.get(id=userid)
        if number_of_songs is None:
            user_songs_ratings = user.usersongrating_set.prefetch_related('song').order_by('-rating').all()
        else:
            number_of_songs = int(number_of_songs)
            user_songs_ratings = user.usersongrating_set.prefetch_related('song').order_by('-rating')[:number_of_songs]
        songs = [song_rating.song for song_rating in user_songs_ratings]
        artist_counts = Counter()
        for song in songs:
            song_artist_table = song.artistsong_set.prefetch_related('artist').all()
            all_artists = [artist_song.artist for artist_song in song_artist_table]
            for artist in all_artists:
                artist_counts[artist.name] += 1
        if not limit:
            return JsonResponse(dict(artist_counts.most_common(10)), status=200)
        else:
            return JsonResponse(dict(artist_counts.most_common(limit)), status=200)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User does not exist'}, status=404)
    except ValueError:
        return JsonResponse({'error': 'Invalid parameters'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@token_required
def get_favorite_moods(request, userid):
    if request.method != 'GET':
        return HttpResponse(status=405)
    try:
        data = request.GET
        number_of_songs = data.get('number_of_songs')
        user = User.objects.get(id=userid)
        if number_of_songs is None:
            user_songs_ratings = user.usersongrating_set.prefetch_related('song').order_by('-rating').all()
        else:
            number_of_songs = int(number_of_songs)
            user_songs_ratings = user.usersongrating_set.prefetch_related('song').order_by('-rating')[:number_of_songs]
        songs = [song_rating.song for song_rating in user_songs_ratings]
        mood_counts = Counter()
        for song in songs:
            mood_label = Mood(song.mood).label
            mood_counts[mood_label] += 1

        return JsonResponse(dict(mood_counts.most_common()), status=200)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User does not exist'}, status=404)
    except ValueError:
        return JsonResponse({'error': 'Invalid number of songs'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@token_required
def get_favorite_tempos(request, userid):
    if request.method != 'GET':
        return HttpResponse(status=405)
    try:
        data = request.GET
        number_of_songs = data.get('number_of_songs')
        user = User.objects.get(id=userid)
        if number_of_songs is None:
            user_songs_ratings = user.usersongrating_set.prefetch_related('song').order_by('-rating').all()
        else:
            number_of_songs = int(number_of_songs)
            user_songs_ratings = user.usersongrating_set.prefetch_related('song').order_by('-rating')[:number_of_songs]
        songs = [song_rating.song for song_rating in user_songs_ratings]
        tempo_counts = Counter()
        for song in songs:
            tempo_label = Tempo(song.tempo).label
            tempo_counts[tempo_label] += 1

        return JsonResponse(dict(tempo_counts.most_common()), status=200)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User does not exist'}, status=404)
    except ValueError:
        return JsonResponse({'error': 'Invalid number of songs'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@token_required
def get_all_song_genres(request, userid):
    if request.method != 'GET':
        return HttpResponse(status=405)
    # retrieve all users from database
    try:
        genresong = ArtistSong.objects.all().values()
    except Exception as e:
        return JsonResponse({"error": "Database error"}, status=500)

    context = {
        "GenreSongRelation": list(genresong)
    }
    return JsonResponse(context, status=200)

@csrf_exempt
@token_required
def get_all_recent_songs(request, userid):
    if request.method != 'GET':
        return HttpResponse(status=405)
    try:
        data = request.GET
        number_of_songs: int = data.get('number_of_songs', 10)
        number_of_songs = int(number_of_songs)
        latest_songs = Song.objects.order_by('-created_at')[:number_of_songs]
        serialized_songs = [
            {
                'id': song.id,
                'name': song.name,
                'release_year': song.release_year,
                'main_artist': song.artists.first().name if song.artists.exists() else "Unknown",
                'img_url': song.img_url
            }
            for song in latest_songs
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
def get_all_incoming_requests(request, userid):
    if request.method != 'GET':
        return HttpResponse(status=405)
    # retrieve all users from database
    try:
        user = User.objects.get(id=userid)
        incoming_requests = FriendRequest.objects.filter(receiver=user,
                                                         status=RequestStatus.PENDING).prefetch_related('sender')
        senders = [single_request.sender for single_request in incoming_requests]
        sender_users = [
            {
                'id': sender.id,
                'name': sender.username,
                'img_url': sender.img_url
            }
            for sender in senders
        ]
        return JsonResponse({'requests': sender_users}, status=200)
    except Exception as e:
        return JsonResponse({"error": "Database error"}, status=500)


@csrf_exempt
@token_required
def get_incoming_requests_count(request, userid):
    if request.method != 'GET':
        return HttpResponse(status=405)
    # retrieve all users from database
    try:
        user = User.objects.get(id=userid)
        incoming_requests = FriendRequest.objects.filter(receiver=user,
                                                         status=RequestStatus.PENDING).prefetch_related('sender')
        request_count = incoming_requests.count()
        return JsonResponse({'count': request_count}, status=200)
    except Exception as e:
        return JsonResponse({"error": "Database error"}, status=500)


@csrf_exempt
@token_required
def get_all_outgoing_requests(request, userid):
    if request.method != 'GET':
        return HttpResponse(status=405)
    # retrieve all users from database
    try:
        user = User.objects.get(id=userid)
        outgoing_requests = FriendRequest.objects.filter(sender=user,
                                                         status=RequestStatus.PENDING).prefetch_related('receiver')
        receivers = [single_request.receiver for single_request in outgoing_requests]
        receiver_users = [
            {
                'id': receiver.id,
                'name': receiver.username,
                'img_url': receiver.img_url
            }
            for receiver in receivers
        ]
        return JsonResponse({'requests': receiver_users}, status=200)
    except Exception as e:
        return JsonResponse({"error": "Database error"}, status=500)


@csrf_exempt
@token_required
def send_friend_request(request, userid):
    if request.method != 'POST':
        return HttpResponse(status=405)
    try:
        user = User.objects.get(id=userid)
        data = json.loads(request.body.decode('utf-8'))
        receiverUser = data.get('username')
        if receiverUser is None or user is None:
            return JsonResponse({'error': 'Missing parameter'}, status=400)
        receiver = User.objects.get(username=receiverUser)
        if receiver is None:
            return JsonResponse({'error': 'Receiver not found'}, status=404)
        if user == receiver:
            return JsonResponse({'error': 'You cannot send a friend request to yourself'}, status=400)
        if user.friends.filter(id=receiver.id).exists():
            return JsonResponse({'error': 'User is already a friend'}, status=400)
        incoming_request = FriendRequest.objects.filter(sender=receiver, receiver=user).first()
        if incoming_request and incoming_request.status == RequestStatus.PENDING:
            return JsonResponse({'error': f'There is already a pending request coming from user {receiverUser}'},
                                status=409)
        existing_friend_request = FriendRequest.objects.filter(sender=user, receiver=receiver).first()
        if existing_friend_request:
            if existing_friend_request.status == RequestStatus.PENDING:
                return JsonResponse({'error': 'There is already a pending request'}, status=400)
            else:
                existing_friend_request.status = RequestStatus.PENDING
                existing_friend_request.save()
                return JsonResponse({'message': 'Friend request sent successfully.'}, status=200)
        FriendRequest.objects.create(sender=user, receiver=receiver)
        return JsonResponse({'message': 'Friend request sent successfully.'}, status=200)
    except User.DoesNotExist:
        return JsonResponse({'error': 'user not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@token_required
def accept_friend_request(request, userid):
    if request.method != 'POST':
        return HttpResponse(status=405)
    try:
        user = User.objects.get(id=userid)
        data = json.loads(request.body.decode('utf-8'))
        requesterName = data.get('username')
        if not requesterName or not user:
            return JsonResponse({'error': 'Missing parameter'}, status=400)
        requesterUser = User.objects.get(username=requesterName)
        if requesterUser is None:
            return JsonResponse({'error': 'Requester not found'}, status=404)
        if user.friends.filter(id=requesterUser.id).exists():
            return JsonResponse({'error': 'User is already a friend'}, status=400)
        pendingRequest = FriendRequest.objects.filter(sender=requesterUser, receiver=user).first()
        if not pendingRequest:
            return JsonResponse({'error': f'There is no request found from the user: {requesterName} '}, status=404)
        if pendingRequest.status == RequestStatus.PENDING:
            pendingRequest.status = RequestStatus.ACCEPTED
            pendingRequest.save()
            user.friends.add(requesterUser)
            user.save()
            return JsonResponse({'message': 'Friend request accepted successfully.'}, status=200)
        elif pendingRequest.status == RequestStatus.ACCEPTED:
            return JsonResponse({'message': f'You are already a friend with {requesterName}'}, status=400)
        elif pendingRequest.status == RequestStatus.REJECTED:
            return JsonResponse({'message': 'This request has been rejected before,'
                                            ' you cannot accept now.'}, status=400)
    except User.DoesNotExist:
        return JsonResponse({'error': 'user not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@token_required
def reject_friend_request(request, userid):
    if request.method != 'POST':
        return HttpResponse(status=405)
    try:
        user = User.objects.get(id=userid)
        data = json.loads(request.body.decode('utf-8'))
        requesterName = data.get('username')
        if not requesterName or not user:
            return JsonResponse({'error': 'Missing parameter'}, status=400)
        requesterUser = User.objects.get(username=requesterName)
        if requesterUser is None:
            return JsonResponse({'error': 'Requester not found'}, status=404)
        if user.friends.filter(id=requesterUser.id).exists():
            return JsonResponse({'error': 'User is already a friend'}, status=400)
        pendingRequest = FriendRequest.objects.filter(sender=requesterUser, receiver=user).first()
        if not pendingRequest:
            return JsonResponse({'error': f'There is no request found from the user: {requesterName} '}, status=404)
        if pendingRequest.status == RequestStatus.PENDING:
            pendingRequest.status = RequestStatus.REJECTED
            pendingRequest.save()
            return JsonResponse({'message': 'Friend request declined.'}, status=200)
        elif pendingRequest.status == RequestStatus.ACCEPTED:
            return JsonResponse({'message': 'This request has already been accepted'}, status=400)
        elif pendingRequest.status == RequestStatus.REJECTED:
            return JsonResponse({'message': 'You have already rejected this request.'}, status=400)
    except User.DoesNotExist:
        return JsonResponse({'error': 'user not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@token_required
def cancel_friend_request(request, userid):
    if request.method != 'POST':
        return HttpResponse(status=405)
    try:
        user = User.objects.get(id=userid)
        data = json.loads(request.body.decode('utf-8'))
        receiverName = data.get('username')
        if not receiverName or not user:
            return JsonResponse({'error': 'Missing parameter'}, status=400)
        receiverUser = User.objects.get(username=receiverName)
        if receiverUser is None:
            return JsonResponse({'error': f'There is no user found with username {receiverName}'}, status=404)
        pendingRequest = FriendRequest.objects.filter(sender=user, receiver=receiverUser).first()
        if not pendingRequest:
            return JsonResponse({'error': f'There is no request found for the user: {receiverName}'}, status=404)
        if pendingRequest.status == RequestStatus.PENDING:
            pendingRequest.hard_delete()
            return JsonResponse({'message': f'You canceled your friend request to {receiverName}.'}, status=200)
        return JsonResponse({'error': 'This request has been deleted.'}, status=404)
    except User.DoesNotExist:
        return JsonResponse({'error': 'user not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@token_required
def get_all_friends(request, userid):
    if request.method != 'GET':
        return HttpResponse(status=405)
    # retrieve all users from database
    try:
        user = User.objects.get(id=userid)
        friends = user.friends.all()
        all_friends = [
            {
                'id': friend.id,
                'name': friend.username,
                'img_url': friend.img_url
            }
            for friend in friends
        ]
        return JsonResponse({'friends': all_friends}, status=200)
    except Exception as e:
        return JsonResponse({"error": "Database error"}, status=500)


@csrf_exempt
def delete_request(request):
    if request.method != 'DELETE':
        return HttpResponse(status=405)
    try:
        req = FriendRequest.objects.get(id=7)
        req.hard_delete()
        return JsonResponse({'response': 'success'}, status=200)
    except Exception as e:
        return JsonResponse({"error": "Database error"}, status=500)


@csrf_exempt
@token_required
def get_all_global_requests(request, userid):
    if request.method != 'GET':
        return HttpResponse(status=405)
    # retrieve all users from database
    try:
        reqs = FriendRequest.objects.all().values()
    except Exception as e:
        return JsonResponse({"error": "Database error"}, status=500)

    context = {
        "reqs": list(reqs)
    }
    return JsonResponse(context, status=200)


@csrf_exempt
@token_required
def edit_user_preferences(request, user_id):
    if request.method != 'PUT':
        return JsonResponse({'error': 'Invalid request method'}, status=405)
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    try:
        data = json.loads(request.body)
        if not data:
            return JsonResponse({'error': 'No fields provided for update'}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)

    # Handle username
    new_username = data.get('username')
    if new_username is not None:
        new_username = new_username.strip()
        if len(new_username) < 6 or len(new_username) > 16:
            return JsonResponse({'error': 'Username must be between 6 and 16 characters long'}, status=400)
        if new_username != user.username and User.objects.filter(username=new_username).exists():
            return JsonResponse({'error': 'Username already in use'}, status=400)
        user.username = new_username

    # Handle email
    new_email = data.get('email')
    if new_email is not None:
        new_email = new_email.strip()
        if new_email != user.email and User.objects.filter(email=new_email).exists():
            return JsonResponse({'error': 'Email already in use'}, status=400)
        user.email = new_email

    # Handle image
    new_img_url = data.get('img_url', user.img_url)
    if new_img_url is not None:
        user.img_url = new_img_url

    # Handle data processing consent
    dpc = data.get('data_processing_consent')
    if dpc is not None:
        if user.userpreferences:
            user.userpreferences.data_processing_consent = dpc
        else:
            user.userpreferences = UserPreferences.objects.create(user=user, data_processing_consent=dpc,
                                                                  data_sharing_consent=True)
        user.userpreferences.save()

    # Handle data sharing consent
    dsc = data.get('data_sharing_consent')
    if dsc is not None:
        if user.userpreferences:
            user.userpreferences.data_sharing_consent = dsc
        else:
            user.userpreferences = UserPreferences.objects.create(user=user, data_sharing_consent=dsc,
                                                                  data_processing_consent=True)
        user.userpreferences.save()
    user.save()
    return JsonResponse(data={}, status=204)


@csrf_exempt
@token_required
def recommend_you_might_like(request, userid):
    try:
        if request.method != 'GET':
            return JsonResponse({'error': 'Invalid method'}, status=400)
        else:
            data = request.GET
            count = int(data.get('count'))
            if count is None or count < 1 or count > 100:
                return JsonResponse({'error': 'Wrong parameter'}, status=400)

            user_songs = UserSongRating.objects.filter(user=userid).order_by('-rating')[:20]

            # if user_songs.exists() is False:
            #     return JsonResponse({'error': 'No songs found for the user, cannot make recommendation'}, status=404)

            # client_credentials = SpotifyClientCredentials(client_id=os.getenv('SPOTIPY_CLIENT_ID'), client_secret=os.getenv('SPOTIPY_CLIENT_SECRET'))
            # sp = spotipy.Spotify(client_credentials_manager=client_credentials)

            track_list = []

            for songs in user_songs:
                track_list.append(songs.song.id)

            list(set(track_list))

            if len(track_list) > 5:
                track_list = random.sample(track_list, 5)

            params = {
                'limit': count,
                'seed_tracks': track_list
            }
            # spotify_recommendations = sp.recommendations(**params)
            recommendations = get_recommendations(**params)

            if recommendations['items'] is None:
                return JsonResponse({'error': 'No recommendations based on track can be made currently, please try again later'}, status=404)
            # tracks_info = recommendation_creator(spotify_recommendations)
            return JsonResponse({'message': 'Recommendation based on track is successful', 'tracks_info': recommendations['items']}, status=200)
    except KeyError as e:
        logging.error(f"A KeyError occurred: {str(e)}")
        return JsonResponse({'error': 'KeyError occurred'}, status=500)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {str(e)}")
        return JsonResponse({'error': 'An unexpected error occurred'}, status=500)


@csrf_exempt
@token_required
def get_user_profile(request, userid):
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed.'}, status=405)
    try:
        user = User.objects.get(id=userid)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found.'}, status=404)
    try:
        user_preferences = user.userpreferences
    except UserPreferences.DoesNotExist:
        user.userpreferences = UserPreferences.objects.create(user=user)
        user_preferences = user.userpreferences
        user.userpreferences.save()
    response_data = {
        'id': user.id,
        'name': user.username,
        'img_url': user.img_url,
        'preferences': {
            'data_processing': user_preferences.data_processing_consent,
            'data_sharing': user_preferences.data_sharing_consent,
        }
    }
    return JsonResponse(response_data)


@csrf_exempt
@token_required
def get_recent_addition_by_count(request, userid):
    if request.method != 'GET':
        return HttpResponse(status=405)
    try:
        user = User.objects.get(id=userid)
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=4)
        start_datetime = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
        song_count_by_day = {start_date + timedelta(days=i): 0 for i in range(5)}
        user_songs_per_day = user.usersongrating_set.filter(created_at__gte=start_datetime).prefetch_related('song').order_by('-created_at')
        for song_rating in user_songs_per_day:
            # Extract just the date part of the 'created_at' datetime
            created_date = song_rating.created_at.date()

            # Check if the created date is within our range
            if start_date <= created_date <= end_date:
                song_count_by_day[created_date] += 1
        formatted_song_count_by_day = {date.strftime("%d-%m"): count for date, count in song_count_by_day.items()}
        song_count_list = [{'date': date, 'count': count} for date, count in formatted_song_count_by_day.items()]
        return JsonResponse({'song_counts': song_count_list}, status=200)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User does not exist'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@token_required
def get_profile_stats(request, userid):
    if request.method != 'GET':
        return HttpResponse(status=405)
    try:
        user = User.objects.get(id=userid)
        friend_count = user.friends.count()
        rating_aggregation = user.usersongrating_set.aggregate(
            total_ratings=Count('rating'),
            sum_ratings=Sum('rating')
        )
        rated_count = rating_aggregation['total_ratings']
        sum_ratings = rating_aggregation['sum_ratings']
        rating_average = 0
        if rated_count > 0:
            rating_average = sum_ratings / rated_count
        return JsonResponse({'rated_count': rated_count, 'friend_count': friend_count,
                             'rating_average': float(round(rating_average, 2))}, status=200)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User does not exist'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@token_required
def recommend_since_you_like(request, userid):
    try:
        if request.method != 'GET':
            return JsonResponse({'error': 'Invalid method'}, status=400)
        else:
            data = request.GET
            count = int(data.get('count'))

            client_credentials = SpotifyClientCredentials(client_id=os.getenv('SPOTIPY_CLIENT_ID'), client_secret=os.getenv('SPOTIPY_CLIENT_SECRET'))
            sp = spotipy.Spotify(client_credentials_manager=client_credentials)

            if count is None or count < 1 or count > 100:
                return JsonResponse({'error': 'Wrong parameter'}, status=404)

            # global available_genre_seeds
            # if available_genre_seeds is None:
            #     available_genre_seeds = sp.recommendation_genre_seeds()['genres']

            ratings = UserSongRating.objects.filter(user=userid).order_by('-rating')[:20]

            user_genre_seeds = []
            user_genre_seeds = getFavoriteGenres(userid,
                                                 number_of_songs=20)
            user_genre_seeds = [seed for seed, _ in user_genre_seeds]
            # for rating in ratings:
            #     song = Song.objects.get(id=rating.song.id)
            #     for genre in song.genres.all():
            #         user_genre_seeds.append(genre.name.lower())
            # list(set(user_genre_seeds))

            # user_genre_seeds = [seed for seed in user_genre_seeds if seed in available_genre_seeds]

            if len(user_genre_seeds) < 2:
                return JsonResponse({'error': 'No genre found for the user, cannot make recommendation'}, status=404)
            user_genre_seeds = user_genre_seeds[:2]

            artist_list = {}
            artist_list = getFavoriteArtists(userid, number_of_songs=20)
            artist_list = [name for name, _ in artist_list]
            # for rating in ratings:
            #     song = Song.objects.get(id=rating.song.id)
            #     for artist in song.artists.all():
            #         artist_list[artist.name] = artist.id

            # if len(artist_list) > 2:
            #     selected_artists = random.sample(artist_list.items(), 2)
            #     artist_list = dict(selected_artists)

            if len(artist_list) < 2:
                return JsonResponse({'error': 'No artist found for the user, cannot make recommendation'}, status=404)
            artist_list = artist_list[:2]

            results = {}
            
            for genre in user_genre_seeds:
                params = {
                    'limit': count,
                    'seed_genres': [genre]
                }
                # spotify_recommendations = sp.recommendations(**params)
                recommendations = get_recommendations(**params)
                if recommendations['items'] is None:
                    return JsonResponse({'error': recommendations['error']}, status=404)
                # results[genre] = recommendation_creator(spotify_recommendations)
                results[genre.title()] = recommendations['items']

            for artist_name in artist_list:
                params = {
                    'limit': count,
                    'seed_artists': [artist_name]
                }
                # spotify_recommendations = sp.recommendations(**params)
                recommendations = get_recommendations(**params)
                if recommendations['items'] is None:
                    return JsonResponse({'error': recommendations['error']}, status=404)
                # results[artist] = recommendation_creator(spotify_recommendations)
                results[artist_name.title()] = recommendations['items']

            return JsonResponse({'message': 'Recommendation based on what you listen is successful', 'tracks_info': results}, status=200)
    except KeyError as e:
        logging.error(f"A KeyError occurred: {str(e)}")
        return JsonResponse({'error': 'KeyError occurred'}, status=500)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {str(e)}")
        return JsonResponse({'error': 'An unexpected error occurred'}, status=500)
    
@csrf_exempt
@token_required
def recommend_friend_mix(request, userid):
    try:
        if request.method != 'GET':
            return JsonResponse({'error': 'Invalid method'}, status=400)
        else:
            data = request.GET
            count = data.get('count')
            count = int(count)

            if count > 100 or count < 1:
                return JsonResponse({'error': 'Invalid count'}, status=400)

            try:
                user = User.objects.get(id=userid)
                friends_list = Friend.objects.filter(user=user)

                available_friends = []
                for friend in friends_list:
                    if UserPreferences.objects.get(user=friend.friend).data_processing_consent is True:
                        available_friends.append(friend)

                if len(available_friends) < 1:
                    return JsonResponse({'error': 'No friends found for the user, cannot make recommendation'}, status=404)
                
                songs_seed = []
                for friend in available_friends:
                    friend_songs = UserSongRating.objects.filter(user=friend.friend).order_by('-rating')
                    for song in friend_songs:
                        songs_seed.append(song.song.id)
                        
                list(set(songs_seed))

                if len(songs_seed) > 5:
                    songs_seed = random.sample(songs_seed, 5)

                elif len(songs_seed) < 1:
                    return JsonResponse({'error': 'No songs found for friends, cannot make recommendation'}, status=404)
                
                params = {
                    'limit': count,
                    'seed_tracks': songs_seed
                }

                # client_credentials = SpotifyClientCredentials(client_id=os.getenv('SPOTIPY_CLIENT_ID'), client_secret=os.getenv('SPOTIPY_CLIENT_SECRET'))
                # sp = spotipy.Spotify(client_credentials_manager=client_credentials)
                # spotify_recommendations = sp.recommendations(**params)
                recommendations = get_recommendations(**params)

                if recommendations['items'] is None:
                    return JsonResponse({'error': 'No recommendations based on friends can be made currently, please try again later'}, status=404)
                # tracks_info = recommendation_creator(spotify_recommendations)
                return JsonResponse({'message': 'Recommendation based on friends is successful', 'tracks_info': recommendations['items']}, status=200)
            except User.DoesNotExist:
                return JsonResponse({'error': 'User not found'}, status=404)
    except KeyError as e:
        logging.error(f"A KeyError occurred: {str(e)}")
        return JsonResponse({'error': 'KeyError occurred'}, status=500)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {str(e)}")
        return JsonResponse({'error': 'An unexpected error occurred'}, status=500)
    
@csrf_exempt
@token_required
def recommend_friend_listen(request, userid):
    try:
        if request.method != 'GET':
            return JsonResponse({'error': 'Invalid method'}, status=400)
        else:
            data = request.GET
            count = data.get('count')

            limit = 1
            
            count = int(count)
            if count < 1:
                return JsonResponse({'error': 'Invalid count'}, status=400)
            friends = Friend.objects.filter(user=userid)

            friends_list = []

            for user in friends:
                if UserPreferences.objects.get(user=user.friend).data_processing_consent is True:
                    friends_list.append(user)

            if len(friends_list) < 1:
                    return JsonResponse({'error': 'No friends found for the user, cannot make recommendation'}, status=404)

            friend_count = len(friends_list)
        
            if count > friend_count:
                limit = count // friend_count
            songs_list = []
            
            for friend in friends_list:
                friend_songs = UserSongRating.objects.filter(user=friend.friend).order_by('-rating')[:10]    
                for rating in friend_songs:
                    song = Song.objects.get(id=rating.song.id)

                    track_info = {
                        'name': song.name,
                        'main_artist': [artist.name for artist in song.artists.all()],
                        'release_year': song.release_year,
                        'id': song.id,
                        'img_url': song.img_url,
                    }
                    songs_list.append(track_info)
            if len(songs_list) > count:
                songs_list = random.sample(songs_list, count)
            elif len(songs_list) < 1:
                return JsonResponse({'error': 'No songs found for friends, cannot make recommendation'}, status=404)

            return JsonResponse({'message': 'Recommendation based on friends is successful', 'tracks_info': songs_list}, status=200)
    except KeyError as e:
        logging.error(f"A KeyError occurred: {str(e)}")
        return JsonResponse({'error': 'KeyError occurred'}, status=500)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {str(e)}")
        return JsonResponse({'error': 'An unexpected error occurred'}, status=500)


@csrf_exempt
@token_required
def export_by_genre(request, userid):
    if request.method != 'GET':
        return HttpResponse(status=405)
    try:
        data = request.GET
        genre_name = data.get('genre')
        user = User.objects.get(id=userid)
        if not genre_name:
            return JsonResponse({'error': 'Missing filter'}, status=400)
        songs_queryset = Song.objects.all()
        genre = Genre.objects.get(name=genre_name)
        songs_queryset = songs_queryset.filter(genres=genre)
        user_songs_ratings = user.usersongrating_set.prefetch_related(
            Prefetch('song', queryset=songs_queryset, to_attr='filtered_songs')
        ).order_by('-rating', '-updated_at').all()

        export_songs = [rating.filtered_songs for rating in user_songs_ratings if rating.filtered_songs]
        serialized_songs = [
            {
                'id': song.id,
                'name': song.name,
                'genres': [genre.name for genre in song.genres.all()],
                'artists': [artist.name for artist in song.artists.all()],
                'albums': [album.name for album in song.albums.all()],
                'instruments': [instrument.name for instrument in song.instruments.all()],
                'release_year': song.release_year,
                'duration': song.duration.total_seconds(),
                'tempo': Tempo(song.tempo).label,
                'mood': Mood(song.mood).label,
                'recorded_environment': RecordedEnvironment(song.recorded_environment).label,
                'replay_count': song.replay_count,
                'version': song.version,
                'img_url': song.img_url
            }
            for song in export_songs
        ]
        data_to_send = json.dumps(serialized_songs, indent=4, ensure_ascii=False)
        # Create a temporary file to write JSON data
        with tempfile.NamedTemporaryFile(delete=False, mode='w+', suffix='.json', encoding='utf-8') as tmp_file:
            tmp_file.write(data_to_send)
            tmp_file_path = tmp_file.name

        # Set up HttpResponse to send it as a file
        with open(tmp_file_path, 'r', encoding='utf-8') as file:
            response = HttpResponse(file, content_type='application/json; charset=utf-8')
            response['Content-Disposition'] = 'attachment; filename="songs_data.json"'

        return response

    except User.DoesNotExist:
        return JsonResponse({'error': 'User does not exist'}, status=404)
    except Genre.DoesNotExist:
        return JsonResponse({'error': 'Genre does not exist'}, status=404)
    except Artist.DoesNotExist:
        return JsonResponse({'error': 'Artist does not exist'}, status=404)
    except ValueError:
        return JsonResponse({'error': 'Invalid input'}, status=400)
    except (IOError, OSError, FileNotFoundError, PermissionError, ValueError, MemoryError) as e:
        return JsonResponse({'error': f'File operation error: {str(e)}'}, status=500)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@token_required
def export_by_artist(request, userid):
    if request.method != 'GET':
        return HttpResponse(status=405)
    try:
        data = request.GET
        artist_name = data.get('artist')
        user = User.objects.get(id=userid)
        if not artist_name:
            return JsonResponse({'error': 'Missing filter'}, status=400)

        songs_queryset = Song.objects.all()
        artist = Artist.objects.get(name=artist_name)
        songs_queryset = songs_queryset.filter(artists=artist)
        user_songs_ratings = user.usersongrating_set.prefetch_related(
            Prefetch('song', queryset=songs_queryset, to_attr='filtered_songs')
        ).order_by('-rating', '-updated_at').all()

        export_songs = [rating.filtered_songs for rating in user_songs_ratings if rating.filtered_songs]
        serialized_songs = [
            {
                'id': song.id,
                'name': song.name,
                'genres': [genre.name for genre in song.genres.all()],
                'artists': [artist.name for artist in song.artists.all()],
                'albums': [album.name for album in song.albums.all()],
                'instruments': [instrument.name for instrument in song.instruments.all()],
                'release_year': song.release_year,
                'duration': song.duration.total_seconds(),
                'tempo': Tempo(song.tempo).label,
                'mood': Mood(song.mood).label,
                'recorded_environment': RecordedEnvironment(song.recorded_environment).label,
                'replay_count': song.replay_count,
                'version': song.version,
                'img_url': song.img_url
            }
            for song in export_songs
        ]
        data_to_send = json.dumps(serialized_songs, indent=4, ensure_ascii=False)
        # Create a temporary file to write JSON data
        with tempfile.NamedTemporaryFile(delete=False, mode='w+', suffix='.json', encoding='utf-8') as tmp_file:
            tmp_file.write(data_to_send)
            tmp_file_path = tmp_file.name

        # Set up HttpResponse to send it as a file
        with open(tmp_file_path, 'r', encoding='utf-8') as file:
            response = HttpResponse(file, content_type='application/json; charset=utf-8')
            response['Content-Disposition'] = 'attachment; filename="songs_data.json"'

        return response

    except User.DoesNotExist:
        return JsonResponse({'error': 'User does not exist'}, status=404)
    except Genre.DoesNotExist:
        return JsonResponse({'error': 'Genre does not exist'}, status=404)
    except Artist.DoesNotExist:
        return JsonResponse({'error': 'Artist does not exist'}, status=404)
    except ValueError:
        return JsonResponse({'error': 'Invalid input'}, status=400)
    except (IOError, OSError, FileNotFoundError, PermissionError, ValueError, MemoryError) as e:
        return JsonResponse({'error': f'File operation error: {str(e)}'}, status=500)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


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
        required_fields = ['name', 'rating']
        return_data = []
        for song_data in data:
            if not all(field in song_data for field in required_fields):
                return_data.append({'error': 'Missing required fields'})
                continue
            rating = float(song_data.get('rating'))
            song_name = song_data.get('name')
            song_name = song_name.title()
            try:
                user = User.objects.get(id=userid)
            except User.DoesNotExist:
                return_data.append({"error": f"User with id {userid} not found"})
                continue

            try:
                song = Song.objects.get(name=song_name)
            except Song.DoesNotExist:
                return_data.append({'error': f'{song_name} does not exist in database, please add it manually'})
                continue

            if rating > 0 and rating <= 5:
                existing_rating = UserSongRating.objects.filter(user=user, song=song)
                if len(existing_rating) == 0:
                    UserSongRating.objects.create(user=user, song=song, rating=rating)
                    return_data.append({'message': f'Rating of {rating} is added to {song_name} successfully'})
                    continue
                else:
                    return_data.append({'error': f'You have already rated {song_name}, please update your rating via your library'})
                    continue
            # recorded_environment = song_data.get('recorded_environment', None)
            # replay_count = song_data.get('replay_count', None)
            # img_url = song_data.get('img_url', None)
            # genre_names = song_data.get('genres', None)
            # artist_names = song_data.get('artists', None)
            # album_names = song_data.get('albums', None)
            # instrument_names = song_data.get('instruments', None)
            # genres, artists, albums, instruments = [], [], [], []

            # if img_url:
            #     song_data['img_url'] = img_url
            # if recorded_environment:
            #     song_data['recorded_environment'] = recorded_environment
            # if replay_count:
            #     song_data['replay_count'] = int(replay_count)
            # if genre_names:
            #     existing_genres, new_genres = bulk_get_or_create(Genre, genre_names, 'name')
            #     genres.extend(existing_genres)
            #     genres.extend(new_genres)
            #     song_data.pop('genres', None)

            # if artist_names:
            #     existing_artists, new_artists = bulk_get_or_create(Artist, artist_names, 'name')
            #     artists.extend(existing_artists)
            #     artists.extend(new_artists)
            #     song_data.pop('artists', None)

            # if album_names:
            #     for album_name in album_names:
            #         album, created = Album.objects.get_or_create(name=album_name, release_year=song_data['release_year'])
            #         albums.append(album)
            #     song_data.pop('albums', None)

            # if instrument_names:
            #     existing_instruments, new_instruments = bulk_get_or_create(Instrument, instrument_names, 'name')
            #     instruments.extend(existing_instruments)
            #     instruments.extend(new_instruments)
            #     song_data.pop('instruments', None)

            # hours, minutes, seconds = map(int, song_data['duration'].split(':'))
            # duration_timedelta = timedelta(hours=hours, minutes=minutes, seconds=seconds)
            # song_data['duration'] = duration_timedelta

            # song = Song(**song_data)
            # song.save()

            # song.genres.set(genres)
            # song.artists.set(artists)
            # song.albums.set(albums)
            # song.instruments.set(instruments)

        return JsonResponse({"items": return_data}, status=201)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return JsonResponse({"error": f"Unexpected error: {e}", "return_data": return_data}, status=500)


@csrf_exempt
@token_required
def get_library_artist_names(request, userid):
    if request.method != 'GET':
        return HttpResponse(status=405)
    try:
        user = User.objects.get(id=userid)
        user_songs_ratings = user.usersongrating_set.prefetch_related('song').all()
        artists = set()
        for rating in user_songs_ratings:
            song = rating.song
            artists.update(artist.name for artist in song.artists.all())
        if not artists:
            return JsonResponse({'error': 'No artist is found for the user'}, status=404)
        return JsonResponse({'artists': list(artists)}, status=200)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User does not exist'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@token_required
def get_library_genre_names(request, userid):
    if request.method != 'GET':
        return HttpResponse(status=405)
    try:
        user = User.objects.get(id=userid)
        user_songs_ratings = user.usersongrating_set.prefetch_related('song').all()
        genres = set()
        for rating in user_songs_ratings:
            song = rating.song
            genres.update(genre.name for genre in song.genres.all())
        if not genres:
            return JsonResponse({'error': 'No genre is found for the user'}, status=404)
        return JsonResponse({'genres': list(genres)}, status=200)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User does not exist'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@token_required
def get_all_data_sharing_friends(request, userid):
    if request.method != 'GET':
        return HttpResponse(status=405)
    # retrieve all users from database
    try:
        user = User.objects.get(id=userid)
        friends = user.friends.all()
        all_friends = [
            {
                'id': friend.id,
                'name': friend.username,
                'img_url': friend.img_url
            }
            for friend in friends if friend.userpreferences.data_sharing_consent
        ]
        return JsonResponse({'friends': all_friends}, status=200)
    except Exception as e:
        return JsonResponse({"error": "Database error"}, status=500)


@csrf_exempt
@token_required
def get_friends_favorite_genres(request, userid):
    if request.method != 'GET':
        return HttpResponse(status=405)
    try:
        data = request.GET
        number_of_songs = data.get('number_of_songs')
        friend_id = data.get('friend_id')
        limit = data.get('limit')
        if limit:
            limit = int(limit)
        user = User.objects.get(id=friend_id)
        user_preferences = user.userpreferences
        if user_preferences.data_sharing_consent is False:
            return JsonResponse({'error': 'User does not share data'}, status=400)
        if number_of_songs is None:
            user_songs_ratings = user.usersongrating_set.prefetch_related('song').order_by('-rating').all()
        else:
            number_of_songs = int(number_of_songs)
            user_songs_ratings = user.usersongrating_set.prefetch_related('song').order_by('-rating')[:number_of_songs]
        songs = [song_rating.song for song_rating in user_songs_ratings]
        genre_counts = Counter()
        for song in songs:
            song_genre_table = song.genresong_set.prefetch_related('genre').all()
            all_genres = [genre_song.genre for genre_song in song_genre_table]
            for genre in all_genres:
                genre_counts[genre.name] += 1
        if not limit:
            return JsonResponse(dict(genre_counts.most_common(10)), status=200)
        else:
            return JsonResponse(dict(genre_counts.most_common(limit)), status=200)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User does not exist'}, status=404)
    except ValueError:
        return JsonResponse({'error': 'Invalid parameters'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@token_required
def get_friends_favorite_artists(request, userid):
    if request.method != 'GET':
        return HttpResponse(status=405)
    try:
        data = request.GET
        number_of_songs = data.get('number_of_songs')
        friend_id = data.get('friend_id')
        limit = data.get('limit')
        if limit:
            limit = int(limit)
        user = User.objects.get(id=friend_id)
        user_preferences = user.userpreferences
        if user_preferences.data_sharing_consent is False:
            return JsonResponse({'error': 'User does not share data'}, status=400)
        if number_of_songs is None:
            user_songs_ratings = user.usersongrating_set.prefetch_related('song').order_by('-rating').all()
        else:
            number_of_songs = int(number_of_songs)
            user_songs_ratings = user.usersongrating_set.prefetch_related('song').order_by('-rating')[:number_of_songs]
        songs = [song_rating.song for song_rating in user_songs_ratings]
        artist_counts = Counter()
        for song in songs:
            song_artist_table = song.artistsong_set.prefetch_related('artist').all()
            all_artists = [artist_song.artist for artist_song in song_artist_table]
            for artist in all_artists:
                artist_counts[artist.name] += 1
        if not limit:
            return JsonResponse(dict(artist_counts.most_common(10)), status=200)
        else:
            return JsonResponse(dict(artist_counts.most_common(limit)), status=200)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User does not exist'}, status=404)
    except ValueError:
        return JsonResponse({'error': 'Invalid parameters'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@token_required
def get_friends_favorite_moods(request, userid):
    if request.method != 'GET':
        return HttpResponse(status=405)
    try:
        data = request.GET
        number_of_songs = data.get('number_of_songs')
        friend_id = data.get('friend_id')
        user = User.objects.get(id=friend_id)
        user_preferences = user.userpreferences
        if user_preferences.data_sharing_consent is False:
            return JsonResponse({'error': 'User does not share data'}, status=400)
        if number_of_songs is None:
            user_songs_ratings = user.usersongrating_set.prefetch_related('song').order_by('-rating').all()
        else:
            number_of_songs = int(number_of_songs)
            user_songs_ratings = user.usersongrating_set.prefetch_related('song').order_by('-rating')[:number_of_songs]
        songs = [song_rating.song for song_rating in user_songs_ratings]
        mood_counts = Counter()
        for song in songs:
            mood_label = Mood(song.mood).label
            mood_counts[mood_label] += 1
        return JsonResponse(dict(mood_counts.most_common()), status=200)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User does not exist'}, status=404)
    except ValueError:
        return JsonResponse({'error': 'Invalid parameters'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@token_required
def get_friends_favorite_tempos(request, userid):
    if request.method != 'GET':
        return HttpResponse(status=405)
    try:
        data = request.GET
        number_of_songs = data.get('number_of_songs')
        friend_id = data.get('friend_id')
        user = User.objects.get(id=friend_id)
        user_preferences = user.userpreferences
        if user_preferences.data_sharing_consent is False:
            return JsonResponse({'error': 'User does not share data'}, status=400)
        if number_of_songs is None:
            user_songs_ratings = user.usersongrating_set.prefetch_related('song').order_by('-rating').all()
        else:
            number_of_songs = int(number_of_songs)
            user_songs_ratings = user.usersongrating_set.prefetch_related('song').order_by('-rating')[:number_of_songs]
        songs = [song_rating.song for song_rating in user_songs_ratings]
        tempo_counts = Counter()
        for song in songs:
            tempo_label = Tempo(song.tempo).label
            tempo_counts[tempo_label] += 1
        return JsonResponse(dict(tempo_counts.most_common()), status=200)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User does not exist'}, status=404)
    except ValueError:
        return JsonResponse({'error': 'Invalid parameters'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@token_required
def get_friends_recent_addition_by_count(request, userid):
    if request.method != 'GET':
        return HttpResponse(status=405)
    try:
        data = request.GET
        friend_id = data.get('friend_id')
        user = User.objects.get(id=friend_id)
        user_preferences = user.userpreferences
        if user_preferences.data_sharing_consent is False:
            return JsonResponse({'error': 'User does not share data'}, status=400)
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=4)
        start_datetime = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
        song_count_by_day = {start_date + timedelta(days=i): 0 for i in range(5)}
        user_songs_per_day = user.usersongrating_set.filter(created_at__gte=start_datetime).prefetch_related('song').order_by('-created_at')
        for song_rating in user_songs_per_day:
            # Extract just the date part of the 'created_at' datetime
            created_date = song_rating.created_at.date()

            # Check if the created date is within our range
            if start_date <= created_date <= end_date:
                song_count_by_day[created_date] += 1
        formatted_song_count_by_day = {date.strftime("%d-%m"): count for date, count in song_count_by_day.items()}
        song_count_list = [{'date': date, 'count': count} for date, count in formatted_song_count_by_day.items()]
        return JsonResponse({'song_counts': song_count_list}, status=200)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User does not exist'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@token_required
def get_playlists(request, userid):
    if request.method != 'GET':
        return HttpResponse(status=405)
    try:
        data = request.GET
        count = data.get('number_of_playlists')
        if count is None:
            count = 10
        count = int(count)
        user = User.objects.filter(id=userid).first()

        if user is None:
            return JsonResponse({'error': 'User does not exist'}, status=404)

        playlists = user.playlists.order_by('-updated_at').all()

        if len(playlists) > count:
            playlists = playlists[:count]

        data = []
        for playlist in playlists:
            serialized_pl = serializePlaylistInfo(playlist)
            data.append(serialized_pl)
        return JsonResponse({'items': data, 'count': len(data)}, status=200)
    except Exception as e:
        return JsonResponse({'Unexpected error': str(e)}, status=500)


@csrf_exempt
@token_required
def get_playlist_by_id(request, userid):
    if request.method != 'GET':
        return HttpResponse(status=405)
    try:
        data = request.GET
        playlist_id = data.get('playlist_id')
        if playlist_id is None:
            return JsonResponse({'error': 'Missing parameters'}, status=400)

        playlist = Playlist.objects.filter(id=playlist_id).first()

        if playlist is None:
            return JsonResponse({'error': 'Playlist does not exist'}, status=404)

        serialized_pl = serializePlaylist(playlist)
        return JsonResponse({'playlist': serialized_pl}, status=200)
    except Exception as e:
        return JsonResponse({'Unexpected error': str(e)}, status=500)


@csrf_exempt
@token_required
def add_song_to_playlist(request, userid):
    if request.method != 'POST':
        return HttpResponse(status=405)
    try:
        data = json.loads(request.body)
        playlist_id = data.get('playlist_id')
        song_id = data.get('song_id')
        if playlist_id is None or song_id is None:
            return JsonResponse({'error': 'Missing parameters'}, status=400)

        playlist = Playlist.objects.filter(id=playlist_id).first()
        song = Song.objects.filter(id=song_id).first()

        if playlist is None:
            return JsonResponse({'error': 'Playlist does not exist'}, status=404)
        if song is None:
            return JsonResponse({'error': 'Song does not exist'}, status=404)

        if song in playlist.songs.all():
            return JsonResponse({'error': f'{song.name} already exists in playlist {playlist.name}'}
                                , status=400)

        playlist.songs.add(song)
        return JsonResponse({'message': f'{song.name} is added to playlist {playlist.name}'},status=200)

    except Exception as e:
        return JsonResponse({'Unexpected error': str(e)}, status=500)


@csrf_exempt
@token_required
def remove_song_from_playlist(request, userid):
    if request.method != 'DELETE':
        return HttpResponse(status=405)

    try:
        data = request.GET
        playlist_id = data.get('playlist_id')
        song_id = data.get('song_id')
        if playlist_id is None or song_id is None:
            return JsonResponse({'error': 'Missing parameters'}, status=400)

        playlist = Playlist.objects.filter(id=playlist_id).first()
        song = Song.objects.filter(id=song_id).first()

        if playlist is None:
            return JsonResponse({'error': 'Playlist does not exist'}, status=404)
        if song is None:
            return JsonResponse({'error': 'Song does not exist'}, status=404)

        if song not in playlist.songs.all():
            return JsonResponse({'error': f'{song.name} does not exist in playlist {playlist.name}'},
                                status=400)

        playlist.songs.remove(song)
        return JsonResponse({'message':
                            f'Song {song.name} removed from playlist {playlist.name} successfully'},
                            status=200)
    except Exception as e:
        return JsonResponse({'Unexpected error': str(e)}, status=500)


@csrf_exempt
@token_required
def create_empty_playlist(request, userid):
    if request.method != 'POST':
        return HttpResponse(status=405)
    try:
        data = json.loads(request.body)
        name = data.get('name')
        description = data.get('description')
        if description is None:
            description = ''

        user = User.objects.filter(id=userid).first()

        if user is None:
            return JsonResponse({'error': 'User does not exist'}, status=404)

        if name is None:
            name = f"Playlist #{user.playlists.count() + 1}"

        p = Playlist.objects.create(name=name,
                                    description=description,
                                    user=user)
        return JsonResponse({'message': f'Playlist {p.name} created succesfully'},
                            status=201)
    except Exception as e:
        return JsonResponse({'Unexpected error': str(e)}, status=500)


@csrf_exempt
@token_required
def delete_playlist(request, userid):
    if request.method != 'DELETE':
        return HttpResponse(status=405)
    try:
        data = request.GET
        playlist_id = data.get('playlist_id')
        if playlist_id is None:
            return JsonResponse({'error': 'Missing parameters'}, status=400)

        playlist = Playlist.objects.filter(id=playlist_id).first()

        if playlist is None:
            return JsonResponse({'error': 'Playlist does not exist'},
                                status=404)

        playlist.delete()
        return JsonResponse({'message': 'Playlist deleted successfully'},
                            status=200)
    except Exception as e:
        return JsonResponse({'Unexpected error': str(e)}, status=500)


@csrf_exempt
@token_required
def edit_playlist(request, userid):
    if request.method != 'PUT':
        return HttpResponse(status=405)
    try:
        data = json.loads(request.body)
        playlist_id = data.get('playlist_id')
        name = data.get('name')
        description = data.get('description')

        if playlist_id is None:
            return JsonResponse({'error': 'Missing playlist_id'}, status=400)

        playlist = Playlist.objects.filter(id=playlist_id).first()

        if playlist is None:
            return JsonResponse({'error': 'Playlist does not exist'},
                                status=404)

        if description is not None:
            playlist.description = description
        if name is not None:
            playlist.name = name

        playlist.save()
        serialized_pl = serializePlaylistInfo(playlist)
        return JsonResponse({'message': 'Playlist edited successfully',
                             'playlist': serialized_pl},
                            status=200)
    except Exception as e:
        return JsonResponse({'Unexpected error': str(e)}, status=500)


@csrf_exempt
@token_required
def get_global_all_friend_groups(request, userid):
    if request.method != 'GET':
        return HttpResponse(status=405)
    try:
        friend_groups = FriendGroup.objects.all()
        context = {
            "friend_groups": [serializeFriendGroupSimple(friend_group) for friend_group in friend_groups]
        }
        return JsonResponse(context, status=200)
    except Exception as e:
        logging.error(f"error: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@token_required
def create_friend_group(request, userid):
    if request.method != 'POST':
        return HttpResponse(status=405)
    try:
        creating_user = User.objects.get(id=userid)
        data = json.loads(request.body.decode('utf-8'))
        group_name = data.get('name')
        group_description = data.get('description')
        if group_description is None:
            group_description = ''
        if group_name:
            friend_group = FriendGroup.objects.create(name=group_name,
                                                      description=group_description, created_by=creating_user)
            friend_group.friends.add(creating_user)
            friend_group.save()
        else:
            return JsonResponse({'error': 'Please provide a name for the friend group.'}, status=400)
        return JsonResponse({'message': 'Friend group created successfully', 'id': f'{friend_group.id}'}, status=201)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User does not exist'}, status=404)
    except Exception as e:
        logging.error(f"error: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@token_required
def get_friend_group_by_id(request, userid):
    if request.method != 'GET':
        return HttpResponse(status=405)
    # retrieve all users from database
    try:
        data = request.GET
        group_id = data.get('group_id')
        if group_id is None:
            return JsonResponse({'error': 'Please provide the id for friend group.'}, status=400)
        extended = data.get('extended')
        friend_group = FriendGroup.objects.get(id=group_id)
        if not extended:
            friend_group = serializeFriendGroupSimple(friend_group)
        else:
            friend_group = serializeFriendGroupExtended(friend_group)
        return JsonResponse({'friend_group': friend_group}, status=200)
    except FriendGroup.DoesNotExist:
        return JsonResponse({'error': 'Friend group does not exist anymore.'}, status=404)
    except Exception as e:
        logging.error(f"error: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@token_required
def add_friend_to_group(request, userid):
    if request.method != 'PUT':
        return HttpResponse(status=405)
    try:
        data = json.loads(request.body.decode('utf-8'))
        group_id = data.get('group_id')
        friend_name = data.get('friend_name')
        if group_id is None or friend_name is None:
            return JsonResponse({'error': 'Missing parameters, '
                                          'please check friend name and group id fields'}, status=400)
        if not isinstance(group_id, int):
            return JsonResponse({'error': 'Invalid group id, please check the group id field'}, status=400)
        user = User.objects.get(id=userid)
        friend_group = FriendGroup.objects.get(id=group_id)
        if friend_group.created_by != user:
            return JsonResponse({'error': 'You are not authorized to add friends to this group'}, status=401)
        friend = User.objects.get(username=friend_name)
        if user == friend:
            return JsonResponse({'error': 'You cannot add yourself to a friend group'}, status=400)
        if friend in friend_group.friends.all():
            return JsonResponse({'error': f'User {friend_name} is already a member of the friend group'}, status=400)
        friend_group.friends.add(friend)
        return JsonResponse({'message': 'Friend was added to the group successfully'}, status=200)
    except FriendGroup.DoesNotExist:
        return JsonResponse({'error': 'Friend group with the given id does not exist'}, status=404)
    except User.DoesNotExist:
        return JsonResponse({'error': 'Friend with the given username does not exist'}, status=404)
    except Exception as e:
        logging.error(f"error: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@token_required
def remove_friend_from_group(request, userid):
    if request.method != 'PUT':
        return HttpResponse(status=405)
    try:
        data = json.loads(request.body.decode('utf-8'))
        group_id = data.get('group_id')
        friend_name = data.get('friend_name')
        if group_id is None or friend_name is None:
            return JsonResponse({'error': 'Missing parameters, '
                                          'please check friend name and group id fields'}, status=400)
        if not isinstance(group_id, int):
            return JsonResponse({'error': 'Invalid group id, please check the group id field'}, status=400)
        user = User.objects.get(id=userid)
        friend_group = FriendGroup.objects.get(id=group_id)
        if friend_group.created_by != user:
            return JsonResponse({'error': 'You are not authorized to remove friends from this group'}, status=401)
        friend = User.objects.get(username=friend_name)
        if user == friend:
            return JsonResponse({'error': 'You cannot remove yourself from a friend group'}, status=400)
        if friend not in friend_group.friends.all():
            return JsonResponse({'error': f'User {friend_name} is not a member of the friend group'}, status=400)
        friend_group.friends.remove(friend)
        return JsonResponse({'message': 'Friend was removed from the group successfully'}, status=200)
    except FriendGroup.DoesNotExist:
        return JsonResponse({'error': 'Friend group with the given id does not exist'}, status=404)
    except User.DoesNotExist:
        return JsonResponse({'error': 'Friend with the given username does not exist'}, status=404)
    except Exception as e:
        logging.error(f"error: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@token_required
def delete_friend_group(request, userid):
    if request.method != 'DELETE':
        return HttpResponse(status=405)
    try:
        data = request.GET
        group_id = data.get('group_id')
        if group_id is None:
            return JsonResponse({'error': 'Please check the group id field.'}, status=400)
        group_id = int(group_id)
        user = User.objects.get(id=userid)
        friend_group = FriendGroup.objects.get(id=group_id)
        if friend_group.created_by != user:
            return JsonResponse({'error': 'You are not authorized to delete this friend group.'}, status=401)
        friend_group.delete()
        return HttpResponse(status=204)
    except FriendGroup.DoesNotExist:
        return JsonResponse({'error': 'Friend group with the given id does not exist'}, status=404)
    except User.DoesNotExist:
        return JsonResponse({'error': 'Friend with the given username does not exist'}, status=404)
    except ValueError:
        return JsonResponse({'error': 'Please check the group id field.'}, status=400)
    except Exception as e:
        logging.error(f"error: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@token_required
def edit_friend_group(request, userid):
    if request.method != 'PUT':
        return HttpResponse(status=405)
    try:
        data = json.loads(request.body)
        group_id = data.get('group_id')
        name = data.get('name')
        description = data.get('description')

        if group_id is None or not isinstance(group_id, int):
            return JsonResponse({'error': 'Please check the group id field.'}, status=400)
        user = User.objects.get(id=userid)
        friend_group = FriendGroup.objects.get(id=group_id)
        if friend_group.created_by != user:
            return JsonResponse({'error': 'You are not authorized to update this friend group.'}, status=401)
        if description is not None:
            friend_group.description = description
        if name is not None:
            friend_group.name = name
        friend_group.save()
        return JsonResponse({'message': 'Friend group edited successfully'}, status=200)
    except FriendGroup.DoesNotExist:
        return JsonResponse({'error': 'Friend group with the given id does not exist'}, status=404)
    except User.DoesNotExist:
        return JsonResponse({'error': 'Friend with the given username does not exist'}, status=404)
    except Exception as e:
        logging.error(f"error: {e}")
        return JsonResponse({'error': str(e)}, status=500)



@csrf_exempt
@token_required
def get_all_friend_groups_of_user(request, userid):
    if request.method != 'GET':
        return HttpResponse(status=405)
    # retrieve all users from database
    try:
        data = request.GET
        extended = data.get('extended')
        user = User.objects.get(id=userid)
        friend_groups_of_user = user.friend_groups.all()
        if not extended:
            friend_groups_serialized = [serializeFriendGroupSimple(group) for group in friend_groups_of_user]
        else:
            friend_groups_serialized = [serializeFriendGroupExtended(group) for group in friend_groups_of_user]
        return JsonResponse({'friend_groups': friend_groups_serialized}, status=200)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User does not exist'}, status=404)
    except Exception as e:
        logging.error(f"error: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@token_required
def get_playlists_of_group(request, userid):
    if request.method != 'GET':
        return HttpResponse(status=405)
    # retrieve all users from database
    try:
        data = request.GET
        group_id = data.get('group_id')
        group_id = int(group_id)
        if group_id is None or not isinstance(group_id, int):
            return JsonResponse({'error': 'Please check the group id field.'}, status=400)
        friend_group = FriendGroup.objects.get(id=group_id)
        playlists = friend_group.playlists.order_by('-updated_at').all()
        data = []
        for playlist in playlists:
            serialized_pl = serializePlaylistInfo(playlist)
            data.append(serialized_pl)
        return JsonResponse({'items': data, 'count': len(data)}, status=200)
        #return JsonResponse({'playlists': serialized_playlists}, status=200)
    except ValueError:
        return JsonResponse({'error': 'Invalid parameters'}, status=400)
    except FriendGroup.DoesNotExist:
        return JsonResponse({'error': 'Friend group does not exist anymore.'}, status=404)
    except Exception as e:
        logging.error(f"error: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@token_required
def create_empty_playlist_in_group(request, userid):
    if request.method != 'POST':
        return HttpResponse(status=405)
    try:
        data = json.loads(request.body.decode('utf-8'))
        name = data.get('playlist_name')
        description = data.get('playlist_description')
        group_id = data.get('group_id')
        if group_id is None or not isinstance(group_id, int):
            return JsonResponse({'error': 'Please check the group id field.'}, status=400)
        if name is None:
            return JsonResponse({'error': 'Please provide the playlist name.'}, status=400)
        if description is None:
            description = ''
        user = User.objects.get(id=userid)
        friend_group = FriendGroup.objects.get(id=group_id)
        if user not in friend_group.friends.all():
            return JsonResponse({'error': 'You are not authorized to create a playlist in this group'}, status=401)
        playlist = Playlist.objects.create(name=name,
                                           description=description,
                                           friend_group=friend_group)
        serialized_pl = serializePlaylist(playlist)
        return JsonResponse({'message': 'Playlist created successfully',
                             'playlist': serialized_pl},
                            status=201)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User does not exist'}, status=404)
    except FriendGroup.DoesNotExist:
        return JsonResponse({'error': 'Friend group does not exist'}, status=404)
    except Exception as e:
        logging.error(f"error: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@token_required
def delete_playlist_from_group(request, userid):
    if request.method != 'DELETE':
        return HttpResponse(status=405)
    try:
        data = request.GET
        playlist_id = data.get('playlist_id')
        if not playlist_id or not isinstance(playlist_id, int):
            return JsonResponse({'error': 'Please check the playlist id field.'}, status=400)
        playlist = Playlist.objects.get(id=playlist_id)
        user = User.objects.get(id=userid)
        if user not in playlist.friend_group.friends.all():
            return JsonResponse({'error': 'You are not authorized to delete this playlist'}, status=401)
        playlist.delete()
        return HttpResponse(status=204)
    except Playlist.DoesNotExist:
        return JsonResponse({'error': 'Playlist does not exist'}, status=404)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User does not exist'}, status=404)
    except FriendGroup.DoesNotExist:
        return JsonResponse({'error': 'Friend group does not exist'}, status=404)
    except Exception as e:
        logging.error(f"error: {e}")
        return JsonResponse({'error': str(e)}, status=500)
    
@csrf_exempt
@token_required
def suggest_song(request, userid):
    try:
        if request.method != 'POST':
            return JsonResponse({'error': 'Invalid method'}, status=400)
        else:
            data = json.loads(request.body, encoding='utf-8')
            receiver_user = data.get('receiver_user')
            song_id = data.get('song_id')

            if receiver_user is None or song_id is None:
                return JsonResponse({'error': 'Missing parameters'}, status=400)
            
            try:
                sender = User.objects.get(id=userid)
                receiver = User.objects.get(username=receiver_user)
                song = Song.objects.get(id=song_id)
            except User.DoesNotExist:
                return JsonResponse({'error': 'User not found'}, status=404)
            except Song.DoesNotExist:
                return JsonResponse({'error': 'Song not found'}, status=404)
            
            if sender == receiver:
                return JsonResponse({'error': 'You cannot send a song to yourself'}, status=400)
            
            suggestion_notification = SuggestionNotification(suggester=sender, receiver=receiver, song=song)
            suggestion_notification.save()

            return JsonResponse({'message': 'Song suggestion sent successfully'}, status=200) 
    except KeyError as e:
        logging.error(f"A KeyError occurred: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)
    
@csrf_exempt
@token_required
def get_suggestions(request, userid):
    try:
        if request.method != 'GET':
            return JsonResponse({'error': 'Invalid method'}, status=400)
        else:
            if userid is None:
                return JsonResponse({'error': 'Missing parameters'}, status=400)
            try:
                user = User.objects.get(id=userid)
            except User.DoesNotExist:
                return JsonResponse({'error': 'User not found'}, status=404)
            notifications = SuggestionNotification.objects.filter(receiver=user)

            serialized_notifications = []
            for notification in notifications:
                serialized_notifications.append({
                    'id': notification.id,
                    'suggester_name': notification.suggester.username,
                    'suggester_img_url': User.objects.get(username=notification.suggester.username).img_url, #notification.receiver.username,
                    'song_id': notification.song.id,  # Replace with the appropriate field for the song name
                    'song_img_url': notification.song.img_url,
                    'song_name': notification.song.name
                })
            return JsonResponse({'items': serialized_notifications}, status=200)
    except KeyError as e:
        logging.error(f"A KeyError occurred: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)
    
@csrf_exempt
@token_required
def get_suggestion_count(request, userid):
    try:
        if request.method != 'GET':
            return JsonResponse({'error': 'Invalid method'}, status=400)
        else:
            if userid is None:
                return JsonResponse({'error': 'Missing parameters'}, status=400)
            try:
                user = User.objects.get(id=userid)
            except User.DoesNotExist:
                return JsonResponse({'error': 'User not found'}, status=404)
            notifications = SuggestionNotification.objects.filter(receiver=user, is_seen=False)
            notification_count = notifications.count()

            return JsonResponse({'count': notification_count}, status=200)
    except KeyError as e:
        logging.error(f"A KeyError occurred: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)
    
@csrf_exempt
@token_required
def set_suggestion_seen(request, userid):
    try:
        if request.method != 'PUT':
            return JsonResponse({'error': 'Invalid method'}, status=400)
        else:
            if userid is None:
                return JsonResponse({'error': 'Missing parameters'}, status=400)
            try:
                user = User.objects.get(id=userid)
            except User.DoesNotExist:
                return JsonResponse({'error': 'User not found'}, status=404)
            notifications = SuggestionNotification.objects.filter(receiver=user, is_seen=False)
            notifications.update(is_seen=True)
            return JsonResponse({'message': 'Suggestions are marked as seen'}, status=200)
    except KeyError as e:
        logging.error(f"A KeyError occurred: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)
    
@csrf_exempt
@token_required
def delete_suggestion(request, userid):
    try:
        if request.method != 'DELETE':
            return JsonResponse({'error': 'Invalid method'}, status=400)
        else:
            data = request.GET
            suggestion_id = data.get('suggestion_id')
            if suggestion_id is None:
                return JsonResponse({'error': 'Missing parameters'}, status=400)
            try:
                notification = SuggestionNotification.objects.get(id=suggestion_id)
            except SuggestionNotification.DoesNotExist:
                return JsonResponse({'error': 'Suggestion not found'}, status=404)
            notification.delete()
            return JsonResponse({'message': 'Suggestion deleted successfully'}, status=200)
    except KeyError as e:
        logging.error(f"A KeyError occurred: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)
    

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
                playlist.songs.add(song)

            return JsonResponse({'playlist_id': playlist.id}, status=201)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)

        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)

        except Song.DoesNotExist:
            return JsonResponse({'error': 'One or more songs not found'}, status=404)
        
        except Exception as e:
            print(f"An unexpected error occurred: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)