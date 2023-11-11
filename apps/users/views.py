import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from OVTF_Backend.firebase_auth import token_required
from apps.users.models import User
from apps.users.models import UserPreferences

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
def user_preferences_create(request):
    try:
        data = json.loads(request.body.decode('utf-8'))

        user, created = User.objects.get_or_create(username=data.get('user'))

        user_preferences, preferences_created = UserPreferences.objects.get_or_create(user=user)

        user_preferences.data_processing_consent = data.get('data_processing_consent', True)
        user_preferences.data_sharing_consent = data.get('data_sharing_consent', True)
        user_preferences.save()

        if preferences_created:
            return JsonResponse({'message': 'UserPreferences created successfully.'}, status=201)
        else:
            return JsonResponse({'message': 'UserPreferences updated successfully.'}, status=200)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)