import json
import os
from firebase_admin import initialize_app, credentials
import logging
from dotenv import load_dotenv

logging.basicConfig(level=logging.ERROR, format="%(asctime)s %(levelname)s %(message)s")

load_dotenv()
FIREBASE_CREDENTIALS = os.environ.get("FIREBASE_CREDENTIALS")
creds = json.loads(FIREBASE_CREDENTIALS)
initialize_app(credentials.Certificate(creds))
logging.info("hello")
