"""Localization manager for handling multi-language support using ARB files"""

import json
from pathlib import Path
from typing import Dict, Optional


class Localizations:
    """Singleton class for managing localization with ARB files"""
    
    _instance: Optional['Localizations'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the localization system"""
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self._current_locale = 'en'
        self._translations: Dict[str, Dict[str, str]] = {}
        self._load_translations()
    
    def _load_translations(self):
        """Load all ARB translation files"""
        # Try multiple possible paths for the i18n directory
        possible_paths = [
            Path(__file__).parent.parent.parent.parent / 'assets' / 'i18n',  # From __file__
            Path.cwd() / 'assets' / 'i18n',  # Current working directory
            Path(__file__).parent.parent.parent.parent.parent / 'assets' / 'i18n',  # One level up
        ]
        
        i18n_dir = None
        for path in possible_paths:
            if path.exists():
                i18n_dir = path
                print(f"Found i18n directory at: {i18n_dir}")
                break
        
        if i18n_dir is None:
            print(f"Warning: i18n directory not found. Tried: {[str(p) for p in possible_paths]}")
            return
        
        # Load all .arb files
        for arb_file in i18n_dir.glob('*.arb'):
            locale = arb_file.stem
            try:
                with open(arb_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Filter out metadata (keys starting with @@)
                translations = {
                    k: v for k, v in data.items()
                    if not k.startswith('@@') and isinstance(v, str)
                }
                
                self._translations[locale] = translations
                print(f"Loaded locale: {locale} ({len(translations)} translations)")
            except Exception as e:
                print(f"Error loading {arb_file}: {e}")
    
    def set_locale(self, locale: str):
        """Set the current locale"""
        if locale in self._translations:
            self._current_locale = locale
        else:
            print(f"Warning: Locale '{locale}' not found. Available: {list(self._translations.keys())}")
    
    def get_locale(self) -> str:
        """Get the current locale"""
        return self._current_locale
    
    def get_available_locales(self) -> list:
        """Get list of available locales"""
        return list(self._translations.keys())
    
    def translate(self, key: str, params: Optional[Dict[str, str]] = None) -> str:
        """
        Translate a key to the current locale
        
        Args:
            key: Translation key
            params: Optional parameters for string interpolation
            
        Returns:
            Translated string, or the key itself if not found
        """
        translations = self._translations.get(self._current_locale, {})
        text = translations.get(key, key)
        
        # Handle parameter interpolation
        if params:
            for param_key, param_value in params.items():
                text = text.replace(f'{{{param_key}}}', str(param_value))
        
        return text
    
    def t(self, key: str, **kwargs) -> str:
        """Shorthand for translate method"""
        return self.translate(key, kwargs if kwargs else None)
    
    def get_translation_dict(self, locale: Optional[str] = None) -> Dict[str, str]:
        """Get entire translation dictionary for a locale"""
        if locale is None:
            locale = self._current_locale
        
        return self._translations.get(locale, {})
    
    def reload_translations(self):
        """Reload all translation files"""
        self._translations.clear()
        self._load_translations()
