import firebase_admin
from firebase_admin import credentials, db
from dotenv import load_dotenv
import os
import json

# Load environment variables
load_dotenv()

def initialize_firebase():
    """Initialize Firebase connection with proper error handling"""
    try:
        if not firebase_admin._apps:
            # Create the credentials dict with explicit string conversions and error checking
            service_account_info = {
                "type": "service_account",
                "project_id": str(os.getenv('FIREBASE_PROJECT_ID', '')),
                "private_key_id": str(os.getenv('FIREBASE_PRIVATE_KEY_ID', '')),
                "private_key": str(os.getenv('FIREBASE_PRIVATE_KEY', '')).replace('\\n', '\n'),
                "client_email": str(os.getenv('FIREBASE_CLIENT_EMAIL', '')),
                "client_id": str(os.getenv('FIREBASE_CLIENT_ID', '')),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": str(os.getenv('FIREBASE_CLIENT_CERT_URL', '')),
                "universe_domain": "googleapis.com"
            }

            # Validate required fields
            required_fields = ['project_id', 'private_key', 'client_email']
            missing_fields = [field for field in required_fields if not service_account_info.get(field)]
            if missing_fields:
                raise ValueError(f"Missing required Firebase credentials: {', '.join(missing_fields)}")

            print("Service account info:", {k: '***' if k == 'private_key' else v[:10] + '...' for k, v in service_account_info.items()})
            
            cred = credentials.Certificate(service_account_info)
            firebase_admin.initialize_app(cred, {
                'databaseURL': str(os.getenv('FIREBASE_DATABASE_URL', ''))
            })
            print("Firebase initialized successfully")
            return True
    except Exception as e:
        print(f"Detailed Firebase initialization error: {str(e)}")
        return False

def get_db():
    """Get Firebase database reference with fallback"""
    if not firebase_admin._apps:
        success = initialize_firebase()
        if not success:
            print("Using fallback visibility settings")
            return None
    return db.reference()
