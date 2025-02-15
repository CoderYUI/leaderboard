from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import os

# Import your existing app
from api.index import app as existing_app

# Create new app for Vercel
app = FastAPI()

# Copy all routes from existing app
app.routes = existing_app.routes

# Mount templates using absolute path for Vercel
VERCEL_TEMPLATE_DIR = os.path.join(os.getcwd(), "templates")
templates = Jinja2Templates(directory=VERCEL_TEMPLATE_DIR)

# Update template directory in existing routes
for route in app.routes:
    if hasattr(route, 'endpoint'):
        if hasattr(route.endpoint, '__globals__'):
            route.endpoint.__globals__['templates'] = templates
