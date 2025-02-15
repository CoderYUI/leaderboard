import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Flask configuration
    FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'default-secret-key')
    
    # Admin configuration
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', '2427')
    
    # Firebase configuration
    FIREBASE_DATABASE_URL = os.getenv('FIREBASE_DATABASE_URL')
    
    # Google Sheets configuration
    SHEET_URL = os.getenv('GOOGLE_SHEET_URL')
    
    # Sheet IDs configuration with updated GIDs
    SHEETS = {
        'round1': {'name': 'Round 1', 'gid': 0},
        'round2': {'name': 'Round 2', 'gid': 855009639},
        'round3': {'name': 'Round 3', 'gid': 2028513950},
        'round4': {'name': 'Round 4', 'gid': 893729618},
        'overall': {'name': 'Overall Score', 'gid': 990261427}
    }
