"""VPK Manager screen"""

import flet as ft
from features.vpk_manager.viewmodels.vpk_manager_viewmodel import VpkManagerViewModel, VpkFile
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
        
        # File pickers
        self._folder_picker = ft.FilePicker(on_result=self._on_folder_selected)
        self._archive_picker = ft.FilePicker(on_result=self._on_archive_selected)
        
        # Main container reference for dynamic updates
        self._main_column = None
        
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
        
        # Create main column and store reference
        self._main_column = ft.Column([
            self._build_top_bar(self._directory_input),
            self._build_content_area(),
        ], expand=True, spacing=10)
        
        return ft.Container(
            content=self._main_column,
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
        """Build content area with collapsible sections using ExpansionPanel"""
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
        
        # Create expansion panels
        panels = []
        
        # Local VPK Files Panel
        local_vpk_content = ft.Column(
            controls=[
                self._build_local_vpk_item(vpk)
                for vpk in self._viewmodel.vpk_files
            ],
            spacing=5,
        ) if self._viewmodel.vpk_files else ft.Text(
            localization.t('noLocalVpkFiles'),
            color='gray',
            size=14,
        )
        
        def on_upload_click(e):
            """Handle upload button click"""
            self._archive_picker.pick_files(
                allowed_extensions=['zip', '7z']
            )
        
        # Upload button for archive files
        upload_button = ft.IconButton(
            icon=ft.icons.UPLOAD_FILE,
            tooltip=localization.t('uploadArchive') if localization.t('uploadArchive') != 'uploadArchive' else 'Upload Archive',
            on_click=on_upload_click,
            disabled=not self._current_directory,
        )
        
        # Content with upload button
        content_with_upload = ft.Column([
            ft.Row([
                ft.Text(localization.t('localVpkFiles') if localization.t('localVpkFiles') != 'localVpkFiles' else 'Local VPK Files', weight='bold', expand=True),
                upload_button,
            ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            local_vpk_content,
        ], spacing=10)
        
        local_vpk_panel = ft.ExpansionPanel(
            header=ft.ListTile(
                title=ft.Text(
                    f"{localization.t('localVpkFiles')} ({len(self._viewmodel.vpk_files)})",
                    weight='bold',
                    size=14,
                    color='#ffffff',
                ),
                subtitle=ft.Text(localization.t('localVpkFilesSubtitle'), size=11, color='#a0a0a0'),
            ),
            content=ft.Container(
                content=content_with_upload,
                padding=15,
                border_radius=8,
            ),
            expanded=self._local_vpk_expanded,
            bgcolor='#242424',
            can_tap_header=True,
        )
        panels.append(local_vpk_panel)
        
        # Workshop Files Panel
        workshop_content = ft.Column(
            controls=[
                self._build_workshop_item(workshop)
                for workshop in self._viewmodel.workshop_files
            ],
            spacing=5,
        ) if self._viewmodel.workshop_files else ft.Text(
            localization.t('noWorkshopFiles'),
            color='gray',
            size=14,
        )
        
        workshop_panel = ft.ExpansionPanel(
            header=ft.ListTile(
                title=ft.Text(
                    f"{localization.t('workshopFiles')} ({len(self._viewmodel.workshop_files)})",
                    weight='bold',
                    size=14,
                    color='#ffffff',
                ),
                subtitle=ft.Text(localization.t('workshopFilesSubtitle'), size=11, color='#a0a0a0'),
            ),
            content=ft.Container(
                content=workshop_content,
                padding=15,
                border_radius=8,
            ),
            expanded=self._workshop_expanded,
            bgcolor='#242424',
            can_tap_header=True,
        )
        panels.append(workshop_panel)
        
        # Create expansion panel list with change handler
        def on_panel_change(e):
            # Update state based on which panels are expanded
            # Note: e.data contains the index of the changed panel
            panel_index = int(e.data) if e.data else -1
            if panel_index == 0:
                self._local_vpk_expanded = panels[0].expanded
            elif panel_index == 1:
                self._workshop_expanded = panels[1].expanded
        
        expansion_list = ft.ExpansionPanelList(
            controls=panels,
            on_change=on_panel_change,
            spacing=12,
            divider_color='#333333',
        )
        
        # Wrap in a scrollable column to enable mouse wheel scrolling
        return ft.Container(
            content=ft.Column(
                controls=[expansion_list],
                expand=True,
                scroll=ft.ScrollMode.AUTO,
            ),
            expand=True,
            padding=0,
        )
    
    def _build_local_vpk_item(self, vpk: VpkFile) -> ft.Container:
        """Build a single local VPK item with thumbnail, filename, and action buttons"""
        # Build thumbnail image or placeholder
        if vpk.thumbnail_path:
            thumbnail = ft.Image(
                src=vpk.thumbnail_path,
                width=120,
                height=120,
                fit=ft.ImageFit.CONTAIN,
            )
        else:
            # Show placeholder if no thumbnail
            thumbnail = ft.Container(
                content=ft.Icon(ft.icons.IMAGE_NOT_SUPPORTED, size=50, color='#666666'),
                width=120,
                height=120,
                bgcolor='#3a3a3a',
                border_radius=8,
                alignment=ft.alignment.center,
            )
        
        # Build filename and info
        name_text_color = '#888888' if vpk.is_disabled else '#ffffff'
        info_text_color = '#666666' if vpk.is_disabled else '#a0a0a0'
        
        file_info = ft.Column([
            ft.Row([
                ft.Text(vpk.name, weight='bold', size=12, color=name_text_color),
                ft.Container(
                    content=ft.Text('已禁用', size=9, color='#ffffff', weight='bold'),
                    bgcolor='#f44336',
                    padding=ft.padding.symmetric(horizontal=6, vertical=2),
                    border_radius=4,
                    visible=vpk.is_disabled,
                ),
            ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Text(
                localization.t('fileSize', size=f'{vpk.size / (1024*1024):.2f}'),
                size=11,
                color=info_text_color,
            ),
        ], tight=True, expand=True)
        
        # Create action buttons based on disabled state
        def on_disable_click(e):
            """Handle disable button click"""
            print(f"_build_local_vpk_item: disabling {vpk.name}")
            self._viewmodel.disable_vpk_sync(vpk)
        
        def on_enable_click(e):
            """Handle enable button click"""
            print(f"_build_local_vpk_item: enabling {vpk.name}")
            self._viewmodel.enable_vpk_sync(vpk)
        
        def on_delete_click(e):
            """Handle delete button click"""
            print(f"_build_local_vpk_item: deleting {vpk.name}")
            self._viewmodel.delete_vpk_sync(vpk)
        
        if vpk.is_disabled:
            # Show "Enable" and "Delete" buttons for disabled files
            action_buttons = ft.Row([
                ft.IconButton(
                    icon=ft.icons.CHECK_CIRCLE,
                    tooltip='Enable',
                    on_click=on_enable_click,
                    icon_color='#4caf50',
                ),
                ft.IconButton(
                    icon=ft.icons.DELETE,
                    tooltip='Delete',
                    on_click=on_delete_click,
                    icon_color='#f44336',
                ),
            ], spacing=5)
        else:
            # Show "Disable" and "Delete" buttons for enabled files
            action_buttons = ft.Row([
                ft.IconButton(
                    icon=ft.icons.BLOCK,
                    tooltip='Disable',
                    on_click=on_disable_click,
                    icon_color='#ff9800',
                ),
                ft.IconButton(
                    icon=ft.icons.DELETE,
                    tooltip='Delete',
                    on_click=on_delete_click,
                    icon_color='#f44336',
                ),
            ], spacing=5)
        
        # Build filename and info with action buttons
        item_content = ft.Row([
            thumbnail,
            file_info,
            action_buttons,
        ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER, opacity=0.6 if vpk.is_disabled else 1.0)
        
        # Apply disabled visual style if disabled
        bgcolor = '#2d2d2d'
        if vpk.is_disabled:
            bgcolor = '#1a1a1a'
        
        return ft.Container(
            content=item_content,
            padding=10,
            border_radius=4,
            bgcolor=bgcolor,
        )
    
    def _build_workshop_item(self, workshop: VpkFile) -> ft.Container:
        """Build a single workshop item with thumbnail and filename"""
        # Build thumbnail image or placeholder
        if workshop.thumbnail_path:
            thumbnail = ft.Image(
                src=workshop.thumbnail_path,
                width=120,
                height=120,
                fit=ft.ImageFit.CONTAIN,
            )
        else:
            # Show placeholder if no thumbnail
            thumbnail = ft.Container(
                content=ft.Icon(ft.icons.IMAGE_NOT_SUPPORTED, size=50, color='#666666'),
                width=120,
                height=120,
                bgcolor='#3a3a3a',
                border_radius=8,
                alignment=ft.alignment.center,
            )
        
        # Build filename and info
        name_text_color = '#888888' if workshop.is_disabled else '#ffffff'
        info_text_color = '#666666' if workshop.is_disabled else '#a0a0a0'
        
        item_content = ft.Row([
            thumbnail,
            ft.Column([
                ft.Row([
                    ft.Text(workshop.name, weight='bold', size=12, color=name_text_color),
                    ft.Container(
                        content=ft.Text('已禁用', size=9, color='#ffffff', weight='bold'),
                        bgcolor='#f44336',
                        padding=ft.padding.symmetric(horizontal=6, vertical=2),
                        border_radius=4,
                        visible=workshop.is_disabled,
                    ),
                ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Text(
                    localization.t('fileSize', size=f'{workshop.size / (1024*1024):.2f}'),
                    size=11,
                    color=info_text_color,
                ),
            ], tight=True, expand=True),
        ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER, opacity=0.6 if workshop.is_disabled else 1.0)
        
        return ft.Container(
            content=item_content,
            padding=10,
            border_radius=4,
            bgcolor='#1a1a1a' if workshop.is_disabled else '#2d2d2d',
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
        """Set page reference for dialogs and file pickers"""
        self._page = page
        # Add file pickers to page
        if self._folder_picker not in self._page.overlay:
            self._page.overlay.append(self._folder_picker)
        if self._archive_picker not in self._page.overlay:
            self._page.overlay.append(self._archive_picker)
    
    def _on_state_changed(self):
        """Handle state changes from ViewModel"""
        # Rebuild the content area when state changes
        print(f"_on_state_changed: called, is_loading={self._viewmodel.is_loading}")
        if self._page and self._main_column:
            # Rebuild the content area with new data
            print(f"_on_state_changed: rebuilding content area")
            new_content_area = self._build_content_area()
            # Replace the second element (index 1) of the column with new content area
            self._main_column.controls[1] = new_content_area
            print(f"_on_state_changed: calling page.update()")
            self._page.update()
            print(f"_on_state_changed: page.update() completed")
    
    def _on_archive_selected(self, e: ft.FilePickerResultEvent):
        """Handle archive file selection from file picker"""
        if e.files:
            selected_file = e.files[0]
            file_path = selected_file.path
            
            print(f"_on_archive_selected: selected file: {file_path}")
            
            # Check if directory is selected
            if not self._current_directory:
                self._viewmodel._error_message = 'Please select a game directory first'
                print(f"_on_archive_selected: no directory selected")
                self._on_state_changed()
                return
            
            # Extract archive (this will trigger load_vpk_files_sync and notify_listeners)
            print(f"_on_archive_selected: calling extract_archive_sync()")
            success = self._viewmodel.extract_archive_sync(file_path)
            print(f"_on_archive_selected: extract result: {success}")
            print(f"_on_archive_selected: waiting for notify_listeners() to trigger _on_state_changed()")
            
            # The notify_listeners() from extract_archive_sync will trigger _on_state_changed()
    
    def dispose(self):
        """Clean up resources"""
        self._viewmodel.dispose()
