import json
import os
from firebase_admin import initialize_app, credentials, auth
import logging
from dotenv import load_dotenv
from functools import wraps
from django.http import JsonResponse, HttpResponse

logger = logging.getLogger(__name__)
load_dotenv()
FIREBASE_CREDENTIALS = os.environ.get("FIREBASE_CREDENTIALS")
creds = json.loads(FIREBASE_CREDENTIALS)
initialize_app(credentials.Certificate(creds))


def verify_token(id_token: str):
    try:
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token['uid']
        return uid
    except Exception as e:
        logger.error(e)
        return None


def token_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if 'HTTP_AUTHORIZATION' not in request.META:
            return JsonResponse({"error": "No token provided"}, status=401)
        else:
            auth_header = request.META['HTTP_AUTHORIZATION']
            bearer_token = auth_header.split(" ")[1]
            token: str = verify_token(bearer_token)
            if token is None:
                return JsonResponse({"error": "Invalid token"}, status=401)
            return view_func(request, *args, **kwargs)  # Call the original view function

    return _wrapped_view
