import json
import os
from firebase_admin import initialize_app, credentials
FIREBASE_CREDENTIALS = os.environ.get("FIREBASE_DB_URL")
initialize_app(credentials.Certificate(json.loads(FIREBASE_CREDENTIALS)))