"""VPK Manager screen"""

import flet as ft
from src.features.vpk_manager.viewmodels.vpk_manager_viewmodel import VpkManagerViewModel
from core.localization import localization


class VpkManagerScreen:
    """VPK Manager screen"""
    
    def __init__(self, viewmodel: VpkManagerViewModel):
        self._viewmodel = viewmodel
        self._viewmodel.add_listener(self._on_state_changed)
        
        # UI state - restore from ViewModel
        self._page = None
        self._current_directory = self._viewmodel.directory_path
        self._directory_input = None  # Will be created in build()
        
        # Collapsible state
        self._local_vpk_expanded = True
        self._workshop_expanded = True
        
        # File picker
        self._folder_picker = ft.FilePicker(on_result=self._on_folder_selected)
        
        # Load VPK files if directory was saved
        if self._current_directory:
            print(f"VpkManagerScreen.__init__: loading VPK files from saved directory: {self._current_directory}")
            self._viewmodel.load_vpk_files_sync(self._current_directory)
    
    def build(self) -> ft.Container:
        """Build the UI"""
        # Create directory input with current locale
        self._directory_input = ft.TextField(
            label=localization.t('directoryPathLabel'),
            expand=True,
            read_only=True,
            value=self._current_directory,
        )
        
        return ft.Container(
            content=ft.Column([
                self._build_top_bar(self._directory_input),
                self._build_content_area(),
            ], expand=True, spacing=10),
            expand=True,
            padding=10,
        ) if self._page is not None else ft.Container()
    
    def _build_top_bar(self, directory_input: ft.TextField) -> ft.Row:
        """Build top bar with directory input and folder button"""
        def on_folder_click(e):
            """Handle folder button click - open directory picker"""
            self._folder_picker.get_directory_path()
        
        label_text = localization.t('directoryPathLabel')
        browse_text = localization.t('browseFolder')
        print(f"_build_top_bar: label='{label_text}', browse='{browse_text}'")
        
        directory_input.label = label_text
        
        return ft.Row([
            directory_input,
            ft.IconButton(
                icon=ft.icons.FOLDER_OPEN,
                tooltip=browse_text,
                on_click=on_folder_click,
            ),
        ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER)
    
    def _build_content_area(self) -> ft.Container:
        """Build content area with collapsible sections"""
        if self._viewmodel.is_loading:
            return ft.Container(
                content=ft.Column([
                    ft.ProgressRing(),
                    ft.Text(localization.t('loading'), size=14),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                expand=True,
            )
        
        if self._viewmodel.has_error:
            return ft.Container(
                content=ft.Column([
                    ft.Icon(ft.icons.ERROR, color='red', size=50),
                    ft.Text(
                        localization.t('error', error=self._viewmodel.error_message),
                        color='red',
                        text_align=ft.TextAlign.CENTER,
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                expand=True,
            )
        
        return ft.Container(
            content=ft.Column([
                self._build_local_vpk_section(),
                self._build_workshop_section(),
            ], spacing=10, expand=True, scroll=ft.ScrollMode.AUTO),
            expand=True,
        )
    
    def _build_local_vpk_section(self) -> ft.Card:
        """Build collapsible section for local VPK files"""
        def toggle_local_vpk(e):
            self._local_vpk_expanded = not self._local_vpk_expanded
            self._on_state_changed()
        
        local_title = localization.t('localVpkFiles')
        local_subtitle = localization.t('localVpkFilesSubtitle')
        no_files = localization.t('noLocalVpkFiles')
        print(f"_build_local_vpk_section: title='{local_title}', subtitle='{local_subtitle}', nofiles='{no_files}'")
        
        vpk_list = ft.Column(
            controls=[
                ft.ListTile(
                    title=ft.Text(vpk.name, size=12),
                    subtitle=ft.Text(localization.t('fileSize', size=f'{vpk.size / (1024*1024):.2f}'), size=11),
                    trailing=ft.Icon(ft.icons.FILE_PRESENT, size=18),
                )
                for vpk in self._viewmodel.vpk_files
            ],
            spacing=5,
        ) if self._viewmodel.vpk_files else ft.Text(
            no_files,
            color='gray',
            size=14,
        )
        
        header = ft.Row([
            ft.Icon(
                ft.icons.EXPAND_MORE if self._local_vpk_expanded else ft.icons.CHEVRON_RIGHT,
                size=20,
            ),
            ft.Column([
                ft.Text(
                    f"{local_title} ({len(self._viewmodel.vpk_files)})",
                    weight='bold',
                    size=14,
                ),
                ft.Text(local_subtitle, size=11, color='gray'),
            ], tight=True, expand=True),
        ], tight=True)
        
        header_container = ft.Container(
            content=header,
            on_click=toggle_local_vpk,
            padding=10,
        )
        
        content = vpk_list if self._local_vpk_expanded else ft.Container(height=0)
        
        return ft.Card(
            content=ft.Column([
                header_container,
                ft.Divider(height=1),
                ft.Container(
                    content=content,
                    padding=10,
                ),
            ], spacing=0, tight=True),
        )
    
    def _build_workshop_section(self) -> ft.Card:
        """Build collapsible section for workshop files"""
        def toggle_workshop(e):
            self._workshop_expanded = not self._workshop_expanded
            self._on_state_changed()
        
        workshop_list = ft.Column(
            controls=[
                ft.ListTile(
                    title=ft.Text(workshop.name, size=12),
                    subtitle=ft.Text(localization.t('fileSize', size=f'{workshop.size / (1024*1024):.2f}'), size=11),
                    trailing=ft.Icon(ft.icons.CLOUD, size=18),
                )
                for workshop in self._viewmodel.workshop_files
            ],
            spacing=5,
        ) if self._viewmodel.workshop_files else ft.Text(
            localization.t('noWorkshopFiles'),
            color='gray',
            size=14,
        )
        
        header = ft.Row([
            ft.Icon(
                ft.icons.EXPAND_MORE if self._workshop_expanded else ft.icons.CHEVRON_RIGHT,
                size=20,
            ),
            ft.Column([
                ft.Text(
                    f"{localization.t('workshopFiles')} ({len(self._viewmodel.workshop_files)})",
                    weight='bold',
                    size=14,
                ),
                ft.Text(localization.t('workshopFilesSubtitle'), size=11, color='gray'),
            ], tight=True, expand=True),
        ], tight=True)
        
        header_container = ft.Container(
            content=header,
            on_click=toggle_workshop,
            padding=10,
        )
        
        content = workshop_list if self._workshop_expanded else ft.Container(height=0)
        
        return ft.Card(
            content=ft.Column([
                header_container,
                ft.Divider(height=1),
                ft.Container(
                    content=content,
                    padding=10,
                ),
            ], spacing=0, tight=True),
        )
    
    def _on_folder_selected(self, e: ft.FilePickerResultEvent):
        """Handle folder selection from system file picker"""
        if e.path:
            self._current_directory = e.path
            print(f"_on_folder_selected: selected path={e.path}")
            
            # Update the directory_input TextField directly
            if self._directory_input:
                self._directory_input.value = e.path
                print(f"_on_folder_selected: updated _directory_input.value to {e.path}")
            
            # Update ViewModel to load VPK files
            self._viewmodel.set_directory_sync(e.path)
            print(f"_on_folder_selected: called set_directory_sync({e.path})")
            
            # Trigger UI update
            if self._page:
                self._page.update()
                print(f"_on_folder_selected: called page.update()")
    
    def _show_folder_picker(self):
        """Show system folder picker"""
        def on_dialog_close(e):
            if dialog.data:
                path = path_input.value
                if path:
                    import asyncio
                    asyncio.create_task(self._viewmodel.set_directory(path))
        
        path_input = ft.TextField(
            label=localization.t('enterFolderPath'),
            width=400,
        )
        
        dialog = ft.AlertDialog(
            title=ft.Text(localization.t('selectDirectory')),
            content=path_input,
            actions=[
                ft.TextButton(localization.t('cancel'), on_click=lambda e: self._close_dialog(dialog)),
                ft.TextButton(
                    localization.t('ok'),
                    on_click=lambda e: self._handle_path_selected(path_input.value, dialog),
                ),
            ],
        )
        
        if self._page:
            self._page.dialog = dialog
            dialog.open = True
            self._page.update()
    
    def _handle_path_selected(self, path: str, dialog: ft.AlertDialog):
        """Handle path selection from dialog"""
        import asyncio
        dialog.open = False
        if self._page:
            self._page.update()
        if path:
            self._current_directory = path
            asyncio.create_task(self._viewmodel.set_directory(path))
        self._on_state_changed()
    
    def _close_dialog(self, dialog: ft.AlertDialog):
        """Close dialog"""
        dialog.open = False
        if self._page:
            self._page.update()
    
    def set_page(self, page: ft.Page):
        """Set page reference for dialogs"""
        self._page = page
        # Add file picker to page
        if self._folder_picker not in self._page.overlay:
            self._page.overlay.append(self._folder_picker)
    
    def _on_state_changed(self):
        """Handle state changes from ViewModel"""
        # Rebuild the content area when state changes
        if self._page:
            self._page.update()
    
    def dispose(self):
        """Clean up resources"""
        self._viewmodel.dispose()
