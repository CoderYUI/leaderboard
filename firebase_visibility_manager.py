from firebase_config import get_db

class FirebaseVisibilityManager:
    def __init__(self, default_sheets):
        self.default_visibility = {sheet_id: True for sheet_id in default_sheets}
        self.db = get_db()
        if self.db:
            self._ensure_visibility_exists()

    def _ensure_visibility_exists(self):
        """Initialize visibility if not exists"""
        try:
            current = self.db.child('visibility').get()
            if not current.val():
                self.db.child('visibility').set(self.default_visibility)
        except:
            print("Error checking visibility, using defaults")

    def load_visibility(self):
        """Load visibility settings with fallback"""
        try:
            if self.db:
                visibility = self.db.child('visibility').get()
                if visibility.val():
                    return visibility.val()
        except Exception as e:
            print(f"Error loading visibility: {e}")
        return self.default_visibility

    def toggle_sheet(self, sheet_id):
        """Toggle visibility of a sheet"""
        try:
            if self.db:
                current = self.load_visibility()
                current[sheet_id] = not current.get(sheet_id, True)
                self.db.child('visibility').set(current)
                return current[sheet_id]
        except Exception as e:
            print(f"Toggle error: {e}")
        return None
