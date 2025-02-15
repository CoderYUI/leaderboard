from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from data_handler import DataHandler
from firebase_visibility_manager import FirebaseVisibilityManager
from config import Config
from typing import Optional
import uvicorn

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Initialize managers
visibility_manager = FirebaseVisibilityManager(Config.SHEETS.keys())
data_handler = DataHandler()

@app.get("/", response_class=HTMLResponse)
@app.get("/{sheet_id}", response_class=HTMLResponse)
async def index(request: Request, sheet_id: Optional[str] = 'round1'):
    # Get visibility settings
    visibility = visibility_manager.load_visibility()
    visible_sheets = {k: v for k, v in Config.SHEETS.items() if visibility.get(k, True)}
    
    if not visible_sheets:
        return "No sheets are currently visible"
    
    if sheet_id not in visible_sheets:
        sheet_id = list(visible_sheets.keys())[0]
    
    try:
        # Fetch sheet data
        data = data_handler.fetch_sheet_data(Config.SHEET_URL, Config.SHEETS[sheet_id]['gid'])
        
        if not data:
            return f"No data available for {sheet_id}"
            
        # Process data based on sheet type
        if sheet_id == 'overall':
            # Fetch all rounds data
            rounds_data = {}
            for rid in ['round1', 'round2', 'round3', 'round4']:
                rounds_data[rid] = data_handler.fetch_sheet_data(
                    Config.SHEET_URL, 
                    Config.SHEETS[rid]['gid']
                )
            processed_data = data_handler.calculate_overall(rounds_data)
        elif sheet_id == 'round1':
            processed_data = data_handler.sort_round1(data)
        else:
            processed_data = data_handler.sort_rounds_2_to_4(data)
        
        # Return processed data to template
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "data": processed_data,
                "sheets": visible_sheets,
                "current_sheet": sheet_id
            }
        )
            
    except Exception as e:
        print(f"Error processing {sheet_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.route("/admin/reset_visibility", methods=["POST"])
async def reset_visibility():
    if visibility_manager.reset_visibility():
        return {"success": True}
    return {"error": "Failed to reset visibility"}, 500

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
