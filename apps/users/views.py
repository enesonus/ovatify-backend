import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from OVTF_Backend.firebase_auth import token_required
from apps.users.models import User
from apps.users.models import UserSongRating
from apps.songs.models import Song

# Create endpoints

@csrf_exempt
@token_required
def get_all_users(request):
    users = User.objects.all()

    context = {
        "users": list(users)
    }
    return JsonResponse(context, status=200)


@csrf_exempt
@token_required
def return_post_body(request):
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
def user_songs_view(request, user_id):
    try:
        user_ratings = UserSongRating.objects.filter(user__firebase_uid=user_id)

        song_ids = user_ratings.values_list('song_id', flat=True)
        
        songs = Song.objects.filter(song_id__in=song_ids)
        
        serialized_songs = [
    {
        'song_id': song.song_id,
        'track_name': song.track_name,
        'release_year': song.release_year,
        'length': song.length.total_seconds(),  # Convert DurationField to seconds
        'tempo': song.tempo,
        'genre': song.genre.name,  # Assuming Genre has a 'name' attribute
        'mood': song.mood,
        'recommended_environment': song.recommended_environment,
        'duration': song.duration,
        'replay_count': song.replay_count,
        'version': song.version,
    }
    for song in songs
]

        
        return JsonResponse({'songs': serialized_songs})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)