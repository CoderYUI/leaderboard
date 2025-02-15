from fastapi import FastAPI, Request, Form, HTTPException, Depends, Cookie
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from starlette.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from data_handler import DataHandler
from firebase_visibility_manager import FirebaseVisibilityManager
from config import Config
from typing import Optional
import uvicorn
import os

app = FastAPI()
security = HTTPBasic()
templates = Jinja2Templates(directory="templates")

# Initialize managers
data_handler = DataHandler()
visibility_manager = None  # Initialize later to handle Firebase errors gracefully

def get_visibility_manager():
    global visibility_manager
    if visibility_manager is None:
        try:
            visibility_manager = FirebaseVisibilityManager(Config.SHEETS.keys())
        except Exception as e:
            print(f"Firebase initialization error: {e}")
            # Return a default visibility (all sheets visible)
            return {'round1': True, 'round2': True, 'round3': True, 'round4': True, 'overall': True}
    return visibility_manager

# Move admin routes BEFORE the general sheet routes for proper priority
@app.get("/admin", response_class=HTMLResponse)
async def admin_get(request: Request):
    """Admin login page - should be handled before the general sheet route"""
    # If already authenticated, go to panel
    if request.cookies.get("admin_auth") == "authenticated":
        return RedirectResponse(url="/admin/panel", status_code=302)
    # Otherwise show login page
    return templates.TemplateResponse("admin_login.html", {
        "request": request,
        "error": None
    })

@app.get("/admin/panel", response_class=HTMLResponse)
async def admin_panel(request: Request):
    """Admin control panel with all sheets data"""
    # Verify admin authentication
    if request.cookies.get("admin_auth") != "authenticated":
        return RedirectResponse(url="/admin", status_code=302)
    
    try:
        # Get visibility settings
        vm = get_visibility_manager()
        visibility = vm.load_visibility() if not isinstance(vm, dict) else vm
        
        # Fetch all sheets data
        sheets_data = {}
        for sheet_id, sheet_info in Config.SHEETS.items():
            data = data_handler.fetch_sheet_data(Config.SHEET_URL, sheet_info['gid'])
            if data:
                if sheet_id == 'overall':
                    rounds_data = {
                        rid: data_handler.fetch_sheet_data(
                            Config.SHEET_URL, 
                            Config.SHEETS[rid]['gid']
                        )
                        for rid in ['round1', 'round2', 'round3', 'round4']
                    }
                    sheets_data[sheet_id] = data_handler.calculate_overall(rounds_data)
                elif sheet_id == 'round1':
                    sheets_data[sheet_id] = data_handler.sort_round1(data)
                elif sheet_id == 'round2':
                    round1_data = data_handler.fetch_sheet_data(
                        Config.SHEET_URL, 
                        Config.SHEETS['round1']['gid']
                    )
                    sheets_data[sheet_id] = data_handler.sort_round2(data, round1_data)
                elif sheet_id == 'round3':
                    round1_data = data_handler.fetch_sheet_data(
                        Config.SHEET_URL, 
                        Config.SHEETS['round1']['gid']
                    )
                    round2_data = data_handler.fetch_sheet_data(
                        Config.SHEET_URL, 
                        Config.SHEETS['round2']['gid']
                    )
                    sheets_data[sheet_id] = data_handler.sort_round3(
                        data, round2_data, round1_data
                    )
                elif sheet_id == 'round4':
                    round1_data = data_handler.fetch_sheet_data(
                        Config.SHEET_URL, 
                        Config.SHEETS['round1']['gid']
                    )
                    round2_data = data_handler.fetch_sheet_data(
                        Config.SHEET_URL, 
                        Config.SHEETS['round2']['gid']
                    )
                    round3_data = data_handler.fetch_sheet_data(
                        Config.SHEET_URL, 
                        Config.SHEETS['round3']['gid']
                    )
                    sheets_data[sheet_id] = data_handler.sort_round4(
                        data, round3_data, round2_data, round1_data
                    )
        
        return templates.TemplateResponse(
            "admin_panel.html",
            {
                "request": request,
                "sheets": Config.SHEETS,
                "visibility": visibility,
                "sheets_data": sheets_data
            }
        )
    except Exception as e:
        print(f"Admin panel error: {e}")
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "message": f"Error loading admin panel: {str(e)}"
            }
        )

@app.post("/admin/login")
async def admin_login_post(request: Request):
    form_data = await request.form()
    password = form_data.get("password")
    
    if password == str(Config.ADMIN_PASSWORD):
        response = RedirectResponse(url="/admin/panel", status_code=302)
        response.set_cookie(
            key="admin_auth",
            value="authenticated",
            httponly=True,
            max_age=1800
        )
        return response
    
    return templates.TemplateResponse(
        "admin_login.html",
        {
            "request": request,
            "error": "Invalid password"
        }
    )

@app.post("/admin/toggle/{sheet_id}")
async def toggle_sheet(request: Request, sheet_id: str):
    if request.cookies.get("admin_auth") != "authenticated":
        raise HTTPException(status_code=401)
    
    vm = get_visibility_manager()
    if isinstance(vm, dict):
        return {"error": "Firebase not available"}
    
    result = vm.toggle_sheet(sheet_id)
    return {"visible": result}

@app.get("/admin/logout")
async def admin_logout():
    response = RedirectResponse(url="/admin", status_code=302)
    response.delete_cookie("admin_auth")
    return response

# Now the general sheet routes come AFTER the admin routes
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Root route redirects to round1"""
    return await index(request, "round1")

@app.get("/{sheet_id}", response_class=HTMLResponse)
async def index(request: Request, sheet_id: Optional[str] = 'round1'):
    try:
        # Get visibility settings with fallback
        vm = get_visibility_manager()
        if isinstance(vm, dict):
            visibility = vm  # Using fallback visibility
        else:
            visibility = vm.load_visibility() or {k: True for k in Config.SHEETS}
        
        visible_sheets = {k: v for k, v in Config.SHEETS.items() if visibility.get(k, True)}
        
        if not visible_sheets:
            visible_sheets = Config.SHEETS  # Fallback to all sheets visible
        
        if sheet_id not in visible_sheets:
            sheet_id = list(visible_sheets.keys())[0]

        data = data_handler.fetch_sheet_data(Config.SHEET_URL, Config.SHEETS[sheet_id]['gid'])
        
        if not data:
            return templates.TemplateResponse("error.html", {
                "request": request,
                "message": f"No data available for {sheet_id}"
            })

        if sheet_id == 'overall':
            rounds_data = {
                rid: data_handler.fetch_sheet_data(Config.SHEET_URL, Config.SHEETS[rid]['gid'])
                for rid in ['round1', 'round2', 'round3', 'round4']
            }
            processed_data = data_handler.calculate_overall(rounds_data)
        elif sheet_id == 'round1':
            processed_data = data_handler.sort_round1(data)
        elif sheet_id == 'round2':
            round1_data = data_handler.fetch_sheet_data(Config.SHEET_URL, Config.SHEETS['round1']['gid'])
            processed_data = data_handler.sort_round2(data, round1_data)
        elif sheet_id == 'round3':
            round1_data = data_handler.fetch_sheet_data(Config.SHEET_URL, Config.SHEETS['round1']['gid'])
            round2_data = data_handler.fetch_sheet_data(Config.SHEET_URL, Config.SHEETS['round2']['gid'])
            processed_data = data_handler.sort_round3(data, round2_data, round1_data)
        elif sheet_id == 'round4':
            round1_data = data_handler.fetch_sheet_data(Config.SHEET_URL, Config.SHEETS['round1']['gid'])
            round2_data = data_handler.fetch_sheet_data(Config.SHEET_URL, Config.SHEETS['round2']['gid'])
            round3_data = data_handler.fetch_sheet_data(Config.SHEET_URL, Config.SHEETS['round3']['gid'])
            processed_data = data_handler.sort_round4(data, round3_data, round2_data, round1_data)

        return templates.TemplateResponse("index.html", {
            "request": request,
            "data": processed_data,
            "sheets": visible_sheets,
            "current_sheet": sheet_id
        })

    except Exception as e:
        print(f"Error processing request: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "message": "An error occurred while processing your request"
        })

import uvicorn

if __name__ == "__main__":
    uvicorn.run("api.index:app", host="127.0.0.1", port=8000, reload=True)
