import json
import logging
from collections import Counter
from datetime import datetime, timedelta
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from OVTF_Backend.firebase_auth import token_required

from songs.models import Song, Genre, Mood, Tempo, GenreSong, ArtistSong, Artist, AlbumSong, Album, InstrumentSong
from users.models import User, UserPreferences, UserSongRating, Friend



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
        User.objects.create(id=userid, username=random_username, email=email, last_login=timezone.now())
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
        return JsonResponse({'error': 'An unexpected error occurred'}, status=500)


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

                friendship = Friend.objects.filter(user=user, friend=friend).first()
                if not friendship:
                    return JsonResponse({'detail': 'Friendship does not exist'}, status=400)

                friendship.delete()

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

                # Create a new friend instance
                Friend.objects.create(user=user, friend=friend)

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

            return JsonResponse({'message': 'User rating deleted successfully'}, status=201)
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
                'tempo': song.tempo,
                'mood': song.mood,
                'recorded_environment': song.recorded_environment,
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
                'tempo': song.tempo,
                'mood': song.mood,
                'recorded_environment': song.recorded_environment,
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
        tempo_name = tempo_name.upper()
        user = User.objects.get(id=userid)
        user_songs_ratings = user.usersongrating_set.prefetch_related('song').all()[:number_of_songs]
        songs = [song_rating.song for song_rating in user_songs_ratings]  # Get the song objects from the ratings
        matching_songs = []
        for song in songs:
            if song.tempo == tempo_name:
                matching_songs.append(song)
        serialized_songs = [
            {
                'id': song.id,
                'name': song.name,
                'release_year': song.release_year,
                'duration': song.duration.total_seconds(),  # Convert DurationField to seconds
                'tempo': song.tempo,
                'mood': song.mood,
                'recorded_environment': song.recorded_environment,
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
        mood_name = mood_name.upper()
        user = User.objects.get(id=userid)
        user_songs_ratings = user.usersongrating_set.prefetch_related('song').all()[:number_of_songs]
        songs = [song_rating.song for song_rating in user_songs_ratings]  # Get the song objects from the ratings
        matching_songs = []
        for song in songs:
            if song.mood == mood_name:
                matching_songs.append(song)
        serialized_songs = [
            {
                'id': song.id,
                'name': song.name,
                'release_year': song.release_year,
                'duration': song.duration.total_seconds(),  # Convert DurationField to seconds
                'tempo': song.tempo,
                'mood': song.mood,
                'recorded_environment': song.recorded_environment,
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
        number_of_songs: int = data.get('number_of_songs', 10)
        number_of_songs = int(number_of_songs)
        user = User.objects.get(id=userid)
        user_songs_ratings = user.usersongrating_set.prefetch_related('song').order_by('-created_at')[:number_of_songs]
        songs = [song_rating.song for song_rating in user_songs_ratings] # Get the song objects from the ratings
        serialized_songs = [
            {
                'id': song.id,
                'name': song.name,
                'release_year': song.release_year,
                'duration': song.duration.total_seconds(),  # Convert DurationField to seconds
                'tempo': song.tempo,
                'mood': song.mood,
                'recorded_environment': song.recorded_environment,
                'replay_count': song.replay_count,
                'version': song.version,
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
        number_of_songs: int = data.get('number_of_songs', 10)
        number_of_songs = int(number_of_songs)
        user = User.objects.get(id=userid)
        user_songs_ratings = user.usersongrating_set.prefetch_related('song').order_by('-rating')[:number_of_songs]
        songs = [song_rating.song for song_rating in user_songs_ratings]  # Get the song objects from the ratings
        # ratings = [song_rating.rating for song_rating in user_songs_ratings]  # In case we want to retrieve ratings
        serialized_songs = [
            {
                'id': song.id,
                'name': song.name,
                'release_year': song.release_year,
                'duration': song.duration.total_seconds(),  # Convert DurationField to seconds
                'tempo': song.tempo,
                'mood': song.mood,
                'recorded_environment': song.recorded_environment,
                'replay_count': song.replay_count,
                'version': song.version,
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
        number_of_songs: int = data.get('number_of_songs', 10)
        number_of_songs = int(number_of_songs)
        user = User.objects.get(id=userid)
        user_songs_ratings = user.usersongrating_set.prefetch_related('song').order_by('-rating')[:number_of_songs]
        songs = [song_rating.song for song_rating in user_songs_ratings]
        genre_counts = Counter()
        for song in songs:
            song_genre_table = song.genresong_set.prefetch_related('genre').all()
            all_genres = [genre_song.genre for genre_song in song_genre_table]
            for genre in all_genres:
                genre_counts[genre.name] += 1

        return JsonResponse(dict(genre_counts), status=200)
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
        number_of_songs: int = data.get('number_of_songs', 10)
        number_of_songs = int(number_of_songs)
        user = User.objects.get(id=userid)
        user_songs_ratings = user.usersongrating_set.prefetch_related('song').order_by('-rating')[:number_of_songs]
        songs = [song_rating.song for song_rating in user_songs_ratings]
        artist_counts = Counter()
        for song in songs:
            song_artist_table = song.artistsong_set.prefetch_related('artist').all()
            all_artists = [artist_song.artist for artist_song in song_artist_table]
            for artist in all_artists:
                artist_counts[artist.name] += 1

        return JsonResponse(dict(artist_counts), status=200)
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
        number_of_songs: int = data.get('number_of_songs', 10)
        number_of_songs = int(number_of_songs)
        user = User.objects.get(id=userid)
        user_songs_ratings = user.usersongrating_set.prefetch_related('song').order_by('-rating')[:number_of_songs]
        songs = [song_rating.song for song_rating in user_songs_ratings]
        mood_counts = Counter()
        for song in songs:
            mood_counts[song.mood] += 1

        return JsonResponse(dict(mood_counts), status=200)
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
        number_of_songs: int = data.get('number_of_songs', 10)
        number_of_songs = int(number_of_songs)
        user = User.objects.get(id=userid)
        user_songs_ratings = user.usersongrating_set.prefetch_related('song').order_by('-rating')[:number_of_songs]
        songs = [song_rating.song for song_rating in user_songs_ratings]
        tempo_counts = Counter()
        for song in songs:
            tempo_counts[song.tempo] += 1

        return JsonResponse(dict(tempo_counts), status=200)
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

