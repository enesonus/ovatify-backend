import json
import logging
from datetime import datetime, timedelta
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.utils.dateparse import parse_duration
from django.views.decorators.csrf import csrf_exempt

from OVTF_Backend.firebase_auth import token_required

from songs.models import Genre, Song
from users.files import UploadFileForm
from users.models import (User, UserSongRating,)


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
        user = User.objects.get(firebase_uid=userid)
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
        if email is None:  # if email is not provided
            return HttpResponse(status=400)
        if User.objects.filter(email=email).exists():  # if user already exists
            return HttpResponse(status=400)
        random_username: str = email.split('@')[0] + str(datetime.now().timestamp()).split('.')[0]
        user = User(firebase_uid=userid, username=random_username, email=email, last_login=timezone.now())
        user.save()
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
        user = User.objects.get(firebase_uid=userid)
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
def add_song_rating(request, userid):
    try:
        if request.method == 'POST':
            data = request.POST
            song_id = data.get('song_id')
            rating = data.get('rating')
            rating_date = datetime.now()

            if userid is None or song_id is None or rating is None or rating_date is None:
                return JsonResponse({'error': 'Missing parameter'}, status=400)
            
            try:
                user = User.objects.get(firebase_uid=userid)
            except User.DoesNotExist:
                return JsonResponse({'error': 'User not found'}, status=404)
            
            try:
                song = Song.objects.get(song_id=song_id)
            except Song.DoesNotExist:
                return JsonResponse({'error': 'Song not found'}, status=404)
            
            try:
                user_rating, created_rating = UserSongRating.objects.get_or_create(user=user, song=song, rating=rating, date_rated=rating_date)

                if not created_rating:
                    return JsonResponse({'error': 'User rating already exists'}, status=400)
                return JsonResponse({'message': 'User rating added successfully'}, status=200)
            except IntegrityError:
                return JsonResponse({'error': 'Integrity Error: Invalid user or song reference'}, status=400)
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
def hello_github(request):
    return JsonResponse({'message': 'Hello from Ovatify Team!'}, status=200)
