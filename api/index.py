from fastapi import FastAPI, Request, Form, HTTPException, Depends, Cookie
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from starlette.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
import sys
import os
from pathlib import Path

# Add parent directory to path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_handler import DataHandler
from firebase_visibility_manager import FirebaseVisibilityManager
from config import Config

app = FastAPI()
security = HTTPBasic()

# Fix templates path for both local and Vercel
TEMPLATE_DIR = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))

# Initialize managers
data_handler = DataHandler()
visibility_manager = None

def get_visibility_manager():
    global visibility_manager
    if visibility_manager is None:
        try:
            visibility_manager = FirebaseVisibilityManager(Config.SHEETS.keys())
        except Exception as e:
            print(f"Firebase initialization error: {e}")
            return {'round1': True, 'round2': True, 'round3': True, 'round4': True, 'overall': True}
    return visibility_manager

# ...rest of your existing route handlers...
