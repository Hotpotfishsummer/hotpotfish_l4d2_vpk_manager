"""Localization module for multi-language support"""

from .localizations import Localizations

# Global instance
localization = Localizations()

__all__ = ['Localizations', 'localization']
