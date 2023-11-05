import json
from django.http import JsonResponse

from apps.users.models import User


# Create endpoints
def get_all_users(request):
    users = User.objects.all()

    context = {
        "users": list(users)
    }
    return JsonResponse(context, status=200)


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
