import firebase_admin
from firebase_admin import credentials, db
import pyrebase
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Pyrebase configuration
firebase_config = {
    "apiKey": "AIzaSyA_Xdf-e9Scs9rGeROxtXx3XY4RjwlB4ME",
    "authDomain": "leaderboard-accde.firebaseapp.com",
    "databaseURL": "https://leaderboard-accde-default-rtdb.asia-southeast1.firebasedatabase.app",
    "projectId": "leaderboard-accde",
    "storageBucket": "leaderboard-accde.firebasestorage.app",
    "messagingSenderId": "160063863408",
    "appId": "1:160063863408:web:823b71dd101698ecda12b5",
    "measurementId": "G-G9Q50F3LDT"
}

def get_db():
    """Get Firebase database reference"""
    try:
        firebase = pyrebase.initialize_app(firebase_config)
        return firebase.database()
    except Exception as e:
        print(f"Firebase initialization error: {str(e)}")
        return None
