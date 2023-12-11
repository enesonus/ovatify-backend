import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView


@csrf_exempt
def health_check(request):
    context = {"status": "OK"}
    return JsonResponse(context, status=200)

def custom_openapi(request):
    with open('openapi.json', 'r') as file:
        data = json.load(file)
        return JsonResponse(data)