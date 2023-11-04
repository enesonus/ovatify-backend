import json
import os
from firebase_admin import initialize_app, credentials, auth
import logging
from dotenv import load_dotenv
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

