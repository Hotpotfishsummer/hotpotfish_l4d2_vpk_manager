"""VPK Manager ViewModel"""

from dataclasses import dataclass
from pathlib import Path
from typing import List
from src.core.viewmodels.base_viewmodel import BaseViewModel
from src.core.services.storage_service import StorageService


@dataclass
class VpkFile:
    """VPK file data model"""
    name: str
    path: str
    size: int
    modified_time: str
    is_valid: bool = True


class VpkManagerViewModel(BaseViewModel):
    """VPK Manager ViewModel for state management and business logic"""
    
    STORAGE_KEY_DIRECTORY = 'vpk_manager_directory'
    
    def __init__(self):
        super().__init__()
        self._storage = StorageService()
        
        # State
        self._directory_path: str = self._storage.get(self.STORAGE_KEY_DIRECTORY, '')
        self._vpk_files: List[VpkFile] = []
        self._workshop_files: List[VpkFile] = []
        self._is_loading = False
        self._error_message: str = ''
        self._selected_file: VpkFile = None
    
    # Getters
    @property
    def directory_path(self) -> str:
        return self._directory_path
    
    @property
    def vpk_files(self) -> List[VpkFile]:
        return self._vpk_files
    
    @property
    def workshop_files(self) -> List[VpkFile]:
        return self._workshop_files
    
    @property
    def is_loading(self) -> bool:
        return self._is_loading
    
    @property
    def has_error(self) -> bool:
        return len(self._error_message) > 0
    
    @property
    def error_message(self) -> str:
        return self._error_message
    
    @property
    def selected_file(self) -> VpkFile:
        return self._selected_file
    
    # Business logic methods
    def set_directory_sync(self, directory: str):
        """Set the working directory and load VPK files (synchronous)"""
        self._directory_path = directory
        self._storage.set(self.STORAGE_KEY_DIRECTORY, directory)
        print(f"set_directory_sync: saved directory to storage: {directory}")
        self.notify_listeners()
        self.load_vpk_files_sync(directory)
    
    def load_vpk_files_sync(self, directory: str):
        """Load VPK files from directory (synchronous)"""
        self._set_loading(True)
        try:
            self._vpk_files = self._get_vpk_files(directory)
            self._workshop_files = []  # Placeholder for workshop files
            self._error_message = ''
        except Exception as e:
            self._error_message = str(e)
        finally:
            self._set_loading(False)
    
    async def set_directory(self, directory: str):
        """Set the working directory and load VPK files"""
        self._directory_path = directory
        self.notify_listeners()
        await self.load_vpk_files(directory)
    
    async def select_file(self, file: VpkFile):
        """Select a VPK file"""
        self._selected_file = file
        self.notify_listeners()
    
    async def extract_selected_file(self, output_dir: str) -> bool:
        """Extract selected VPK file"""
        if not self._selected_file:
            self._error_message = 'No file selected'
            self.notify_listeners()
            return False
        
        self._set_loading(True)
        try:
            success = self._extract_vpk(
                self._selected_file.path,
                output_dir
            )
            if success:
                self._error_message = ''
            else:
                self._error_message = 'Failed to extract VPK file'
            return success
        except Exception as e:
            self._error_message = str(e)
            return False
        finally:
            self._set_loading(False)
    
    # Private helper methods
    def _get_vpk_files(self, directory: str) -> List[VpkFile]:
        """Get list of VPK files from directory"""
        vpk_files = []
        path = Path(directory)
        
        if not path.exists():
            return vpk_files
        
        for file_path in path.glob('*.vpk'):
            stat = file_path.stat()
            vpk_file = VpkFile(
                name=file_path.name,
                path=str(file_path),
                size=stat.st_size,
                modified_time=str(stat.st_mtime),
            )
            vpk_files.append(vpk_file)
        
        return vpk_files
    
    def _extract_vpk(self, file_path: str, output_dir: str) -> bool:
        """Extract VPK file"""
        try:
            # Placeholder for VPK extraction logic
            return True
        except Exception as e:
            print(f"Error extracting VPK: {e}")
            return False
    
    def _set_loading(self, loading: bool):
        """Set loading state"""
        self._is_loading = loading
        self.notify_listeners()
    
    def dispose(self):
        """Clean up resources"""
        super().dispose()
        self._vpk_files.clear()
        self._workshop_files.clear()
        self._selected_file = None
