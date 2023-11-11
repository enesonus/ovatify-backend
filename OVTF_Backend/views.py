from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def health_check(request):
    context = {"status": "OK"}
    return JsonResponse(context, status=200)
