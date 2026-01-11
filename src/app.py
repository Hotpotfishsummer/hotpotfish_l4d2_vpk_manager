"""
L4D2 VPK Manager - Main Application
Uses MVVM architecture
"""

import flet as ft
from pathlib import Path


def _safe_print(msg: str):
    """Safe print that handles encoding errors"""
    try:
        print(msg)
    except UnicodeEncodeError:
        # If encoding fails, replace problematic characters
        print(msg.encode('utf-8', errors='replace').decode('utf-8', errors='replace'))


def main(page: "ft.Page"):
    """Main application entry point"""
    
    _safe_print("=" * 50)
    _safe_print("main() function called")
    _safe_print(f"Page object: {page}")
    _safe_print("=" * 50)
    
    try:
        # Initialize localization first
        _safe_print("Importing localization...")
        from core.localization import localization
        _safe_print("✓ Localization imported")
        
        _safe_print(f"Available locales: {localization.get_available_locales()}")
        localization.set_locale('zh')  # Default to Chinese, can be changed
        _safe_print(f"Current locale: {localization.get_locale()}")
        
        # Test translations
        _safe_print(f"Test translation - appTitle: {localization.t('appTitle')}")
        _safe_print(f"Test translation - directoryPathLabel: {localization.t('directoryPathLabel')}")
        
    except Exception as e:
        _safe_print(f"✗ Error initializing localization: {e}")
        import traceback
        _safe_print(traceback.format_exc())
        # Show error on page
        page.add(ft.Text(f"Error loading localization: {e}", color="red"))
        return
    
    try:
        # Configure page
        _safe_print("Configuring page...")
        page.title = localization.t('appTitle')
        page.window.width = 900
        page.window.height = 600
        page.window.min_width = 600
        page.window.min_height = 400
        _safe_print("✓ Page configured")
    except Exception as e:
        _safe_print(f"Warning: Could not set window properties: {e}")
    
    try:
        # Initialize viewmodel and screen
        _safe_print("Importing VPK Manager components...")
        from features.vpk_manager.screens.vpk_manager_screen import VpkManagerScreen
        from features.vpk_manager.viewmodels.vpk_manager_viewmodel import VpkManagerViewModel
        _safe_print("✓ Components imported")
        
        _safe_print("Creating ViewModel...")
        viewmodel = VpkManagerViewModel()
        _safe_print("✓ ViewModel created")
        
        _safe_print("Creating Screen...")
        vpk_manager_screen = VpkManagerScreen(viewmodel)
        vpk_manager_screen.set_page(page)
        _safe_print("✓ Screen created and page set")
        
        # Build UI and add to page
        _safe_print("Building UI...")
        ui = vpk_manager_screen.build()
        _safe_print(f"✓ UI built: {type(ui)}")
        
        _safe_print("Adding UI to page...")
        page.add(ui)
        _safe_print("✓ UI added to page")
        
        _safe_print("=" * 50)
        _safe_print("Application UI loaded successfully!")
        _safe_print("=" * 50)
        
    except Exception as e:
        _safe_print(f"✗ Error building UI: {e}")
        import traceback
        _safe_print(traceback.format_exc())
        # Show error on page
        error_text = f"Error building UI: {str(e)}"
        page.add(ft.Text(error_text, color="red", size=14))
        page.update()

    page.add(ui)
    _safe_print("UI added to page")