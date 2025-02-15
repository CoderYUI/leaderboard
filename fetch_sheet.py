import requests
import csv
import io
from typing import List, Dict, Any

def get_sheet_data(sheet_url: str, sheet_name: int) -> List[Dict[str, Any]]:
    """Fetch data from a public Google Sheet"""
    try:
        sheet_id = sheet_url.split('/d/')[1].split('/')[0]
        export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={sheet_name}"
        
        response = requests.get(export_url)
        if response.status_code != 200:
            return []
            
        csv_content = io.StringIO(response.text)
        reader = csv.DictReader(csv_content)
        return list(reader)
        
    except Exception as e:
        print(f"Error fetching sheet (GID {sheet_name}): {str(e)}")
        return []