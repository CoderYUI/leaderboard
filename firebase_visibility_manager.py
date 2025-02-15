from firebase_config import get_db

class FirebaseVisibilityManager:
    def __init__(self, default_sheets):
        self.default_visibility = {sheet_id: True for sheet_id in default_sheets}
        self.current_visibility = self.default_visibility.copy()  # Add local cache
        try:
            self.db = get_db()
            if self.db:
                self.visibility_ref = self.db.child('visibility')
                self._ensure_visibility_exists()
            else:
                self.visibility_ref = None
        except Exception as e:
            print(f"Firebase init error (using defaults): {e}")
            self.db = None
            self.visibility_ref = None

    def _ensure_visibility_exists(self):
        if not self.visibility_ref:
            return
        try:
            current = self.visibility_ref.get()
            if not current:
                self.visibility_ref.set(self.default_visibility)
                self.current_visibility = self.default_visibility.copy()
        except Exception as e:
            print(f"Visibility check error: {e}")

    def reset_visibility(self):
        """Reset visibility settings to default (all visible)"""
        try:
            self.visibility_ref.set(self.default_visibility)
            return True
        except Exception as e:
            print(f"Error resetting visibility: {e}")
            return False
    
    def load_visibility(self):
        """Load visibility settings with fallback to defaults"""
        if not self.visibility_ref:
            return self.current_visibility
        try:
            visibility = self.visibility_ref.get()
            if visibility:
                self.current_visibility = visibility
            return self.current_visibility
        except:
            return self.current_visibility
    
    def save_visibility(self, visibility):
        """Save sheet visibility settings"""
        try:
            self.visibility_ref.set(visibility)
            return True
        except Exception as e:
            print(f"Error saving visibility settings: {e}")
            return False
    
    def toggle_sheet(self, sheet_id):
        """Toggle visibility of a sheet"""
        try:
            self.current_visibility[sheet_id] = not self.current_visibility.get(sheet_id, True)
            if self.visibility_ref:
                self.visibility_ref.set(self.current_visibility)
            return self.current_visibility[sheet_id]
        except Exception as e:
            print(f"Toggle error: {e}")
            return None
