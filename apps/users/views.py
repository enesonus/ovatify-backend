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
from apps.users.utils import recommendation_creator
from songs.models import Song, Genre, Mood, Tempo, GenreSong, ArtistSong, Artist, AlbumSong, Album, InstrumentSong, RecordedEnvironment, Instrument
from users.models import User, UserPreferences, UserSongRating, Friend, FriendRequest, RequestStatus
from users.utils import getFavoriteGenres, getFavoriteSongs, getFavoriteArtists, getFavoriteMoods, getFavoriteTempos
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
        random_username: str = email.split('@')[0] + str(datetime.now().timestamp()).split('.')[0]
        user = User.objects.create(id=userid, username=random_username, email=email, last_login=timezone.now())
        if not UserPreferences.objects.filter(user=user).exists():
            UserPreferences.objects.create(user=user, data_processing_consent=True, data_sharing_consent=True)
        return HttpResponse(status=201)
    except Exception as e:
        #TODO logging.("create_user: " + str(e))
        return HttpResponse(status=500)


@csrf_exempt
@token_required
def delete_user(request, userid):
    if request.method != 'DELETE':
        return HttpResponse(status=405)
    try:
        user = User.objects.get(id=userid)
        user.delete()
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
        if request.method == 'POST':
            try:
                user_id = request.POST.get('user_id')
                friend_id = request.POST.get('friend_id')

                user = User.objects.get(id=user_id)
                friend = User.objects.get(id=friend_id)

                # Check if the friendship exists
                if not user.friends.filter(id=friend.id).exists():
                    return JsonResponse({'detail': 'Friendship does not exist'}, status=400)

                # Remove the friend relationship using .remove() method
                user.friends.remove(friend)

                return JsonResponse({'detail': 'Friend removed successfully'}, status=200)

            except User.DoesNotExist:
                return JsonResponse({'detail': 'User or friend does not exist'}, status=404)

        else:
            return JsonResponse({'error': 'Invalid method'}, status=400)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@token_required
def add_friend(request, userid):
    try:
        if request.method == 'POST':
            try:
                user_id = request.POST.get('user_id')
                friend_id = request.POST.get('friend_id')

                user = User.objects.get(id=user_id)
                friend = User.objects.get(id=friend_id)

                # Check if the friendship already exists
                if Friend.objects.filter(user=user, friend=friend).exists():
                    return JsonResponse({'detail': 'Friendship already exists'}, status=400)

                # Modify the existing friend relationship by using .add() method
                user.friends.add(friend)

                return JsonResponse({'detail': 'Friend added successfully'}, status=200)

            except User.DoesNotExist:
                return JsonResponse({'detail': 'User or friend does not exist'}, status=404)

        else:
            return JsonResponse({'error': 'Invalid method'}, status=400)

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

        return JsonResponse(dict(genre_counts.most_common()), status=200)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User does not exist'}, status=404)
    except ValueError:
        return JsonResponse({'error': 'Invalid number of songs'}, status=400)
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

        return JsonResponse(dict(artist_counts.most_common()), status=200)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User does not exist'}, status=404)
    except ValueError:
        return JsonResponse({'error': 'Invalid number of songs'}, status=400)
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
            elif existing_friend_request.status == RequestStatus.ACCEPTED:
                return JsonResponse({'message': f'You are already friends with {receiverUser}'}, status=400)
            elif existing_friend_request.status == RequestStatus.REJECTED:
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

            if user_songs.exists() is False:
                return JsonResponse({'error': 'No songs found for the user, cannot make recommendation'}, status=404)

            client_credentials = SpotifyClientCredentials(client_id=os.getenv('SPOTIPY_CLIENT_ID'), client_secret=os.getenv('SPOTIPY_CLIENT_SECRET'))
            sp = spotipy.Spotify(client_credentials_manager=client_credentials)

            track_list = []

            for songs in user_songs:
                track_list.append(songs.song.id)

            list(set(track_list))

            if len(track_list) > 5:
                track_list =  random.sample(track_list, 5)

            params = {
                'limit': count,
                'seed_tracks': track_list
            }
            spotify_recommendations = sp.recommendations(**params)

            if spotify_recommendations['tracks'] is None:
                return JsonResponse({'error': 'No recommendations based on track can be made currently, please try again later'}, status=404)
            tracks_info = recommendation_creator(spotify_recommendations)
            return JsonResponse({'message': 'Recommendation based on track is successful', 'tracks_info': tracks_info}, status=200)
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
            
            available_seeds = sp.recommendation_genre_seeds()['genres']

            ratings = UserSongRating.objects.filter(user=userid).order_by('-rating')[:20]

            user_genre_seeds = []

            for rating in ratings:
                song = Song.objects.get(id=rating.song.id)
                for genre in song.genres.all():
                    user_genre_seeds.append(genre.name.lower())
            list(set(user_genre_seeds))

            user_genre_seeds = [seed for seed in user_genre_seeds if seed in available_seeds]

            if len(user_genre_seeds) > 2:
                user_genre_seeds = random.sample(user_genre_seeds, 2)
            elif len(user_genre_seeds) < 1:
                return JsonResponse({'error': 'No genre found for the user, cannot make recommendation'}, status=404)
            
            artist_list = {}

            for rating in ratings:
                song = Song.objects.get(id=rating.song.id)
                for artist in song.artists.all():
                    artist_list[artist.name] = artist.id

            if len(artist_list) > 2:
                selected_artists = random.sample(artist_list.items(), 2)
                artist_list = dict(selected_artists)

            elif len(artist_list) < 1:
                return JsonResponse({'error': 'No artist found for the user, cannot make recommendation'}, status=404)
            
            results = {}
            
            for genre in user_genre_seeds:
                params = {
                    'limit': count,
                    'seed_genres': [genre]
                }
                spotify_recommendations = sp.recommendations(**params)
                if spotify_recommendations['tracks'] is None:
                    return JsonResponse({'error': 'No recommendations can be made currently, please try again later'}, status=404)
                results[genre] = recommendation_creator(spotify_recommendations)
            
            for artist in artist_list:
                params = {
                    'limit': count,
                    'seed_artists': [artist_list[artist]]
                }
                spotify_recommendations = sp.recommendations(**params)
                if spotify_recommendations['tracks'] is None:
                    return JsonResponse({'error': 'No recommendations can be made currently, please try again later'}, status=404)
                results[artist] = recommendation_creator(spotify_recommendations)

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

                client_credentials = SpotifyClientCredentials(client_id=os.getenv('SPOTIPY_CLIENT_ID'), client_secret=os.getenv('SPOTIPY_CLIENT_SECRET'))
                sp = spotipy.Spotify(client_credentials_manager=client_credentials)
                spotify_recommendations = sp.recommendations(**params)

                if spotify_recommendations['tracks'] is None:
                    return JsonResponse({'error': 'No recommendations based on friends can be made currently, please try again later'}, status=404)
                tracks_info = recommendation_creator(spotify_recommendations)
                return JsonResponse({'message': 'Recommendation based on friends is successful', 'tracks_info': tracks_info}, status=200)
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