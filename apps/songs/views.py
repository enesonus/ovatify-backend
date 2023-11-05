from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from OVTF_Backend.firebase_auth import token_required
from apps.users.models import Song


# Create your views here.

@csrf_exempt
@token_required
def get_all_songs(request):
    users = Song.objects.all()
    context = {
        "users": list(users)
    }
    return JsonResponse(context, status=200)
