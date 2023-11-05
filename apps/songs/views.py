from django.http import JsonResponse
from django.shortcuts import render

from apps.users.models import Song


# Create your views here.
def get_all_songs(request):
    users = Song.objects.all()

    context = {
        "users": list(users)
    }
    return JsonResponse(context, status=200)
