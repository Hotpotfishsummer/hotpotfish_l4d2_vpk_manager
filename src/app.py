"""
L4D2 VPK Manager - Main Application
Uses MVVM architecture
"""

import flet as ft
from features.vpk_manager.screens.vpk_manager_screen import VpkManagerScreen
from features.vpk_manager.viewmodels.vpk_manager_viewmodel import VpkManagerViewModel
from core.localization import localization


def main(page: ft.Page):
    """Main application entry point"""
    
    # Initialize localization first
    print(f"Available locales: {localization.get_available_locales()}")
    localization.set_locale('zh')  # Default to Chinese, can be changed
    print(f"Current locale: {localization.get_locale()}")
    print(f"Sample translation: {localization.t('appTitle')}")
    print(f"Sample translation: {localization.t('directoryPathLabel')}")
    print(f"Sample translation: {localization.t('localVpkFiles')}")
    
    # Configure page
    try:
        page.title = localization.t('appTitle')
        page.window.width = 900
        page.window.height = 600
        page.window.min_width = 600
        page.window.min_height = 400
    except Exception as e:
        print(f"Warning: Could not set window properties: {e}")
    
    # Initialize viewmodel and screen
    viewmodel = VpkManagerViewModel()
    vpk_manager_screen = VpkManagerScreen(viewmodel)
    vpk_manager_screen.set_page(page)
    
    # Build UI and add to page
    print("Building UI...")
    ui = vpk_manager_screen.build()
    print(f"UI built: {type(ui)}")
    page.add(ui)
    print("UI added to page")


if __name__ == "__main__":
    try:
        ft.app(target=main)
    except Exception as e:
        print(f"Error running app: {e}")
        exit(1)