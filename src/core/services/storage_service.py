"""Storage service for persisting user preferences and data"""

import json
from pathlib import Path
from typing import Any, Optional


class StorageService:
    """Singleton service for persisting user preferences to local storage"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # Create storage directory in user's home
        self._storage_dir = Path.home() / '.l4d2_vpk_manager'
        self._storage_dir.mkdir(exist_ok=True)
        
        # Storage file path
        self._storage_file = self._storage_dir / 'preferences.json'
        
        # Load existing preferences
        self._preferences = self._load_preferences()
        
        self._initialized = True
    
    def _load_preferences(self) -> dict:
        """Load preferences from storage file"""
        if not self._storage_file.exists():
            return {}
        
        try:
            with open(self._storage_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading preferences: {e}")
            return {}
    
    def _save_preferences(self):
        """Save preferences to storage file"""
        try:
            with open(self._storage_file, 'w', encoding='utf-8') as f:
                json.dump(self._preferences, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"Error saving preferences: {e}")
    
    def set(self, key: str, value: Any):
        """Set a preference value"""
        self._preferences[key] = value
        self._save_preferences()
        print(f"StorageService.set: key='{key}', value='{value}'")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a preference value"""
        return self._preferences.get(key, default)
    
    def remove(self, key: str):
        """Remove a preference"""
        if key in self._preferences:
            del self._preferences[key]
            self._save_preferences()
            print(f"StorageService.remove: key='{key}'")
    
    def clear(self):
        """Clear all preferences"""
        self._preferences.clear()
        self._save_preferences()
        print("StorageService.clear: all preferences cleared")
