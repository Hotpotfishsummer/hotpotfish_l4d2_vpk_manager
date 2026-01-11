"""VPK Manager ViewModel"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
import zipfile
import shutil
import tarfile
from core.viewmodels.base_viewmodel import BaseViewModel
from core.services.storage_service import StorageService
from features.vpk_manager.services.vpk_metadata_service import VpkMetadataService

try:
    import py7zr
    HAS_7ZR = True
except ImportError:
    HAS_7ZR = False

try:
    import zstandard as zstd
    HAS_ZSTD = True
except ImportError:
    HAS_ZSTD = False


def _safe_print(msg: str):
    """Safe print that handles encoding errors"""
    try:
        print(msg)
    except UnicodeEncodeError:
        # If encoding fails, replace problematic characters
        print(msg.encode('utf-8', errors='replace').decode('utf-8', errors='replace'))


@dataclass
class VpkFile:
    """VPK file data model"""
    name: str
    path: str
    size: int
    modified_time: str
    is_valid: bool = True
    thumbnail_path: Optional[str] = None  # Path to thumbnail image (.jpg)
    is_disabled: bool = False  # Whether the VPK is disabled (.vpk.disabled)
    addontitle: Optional[str] = None  # Add-on title extracted from addoninfo.txt


class VpkManagerViewModel(BaseViewModel):
    """VPK Manager ViewModel for state management and business logic"""
    
    STORAGE_KEY_DIRECTORY = 'vpk_manager_directory'
    
    def __init__(self):
        super().__init__()
        self._storage = StorageService()
        self._metadata_service: Optional[VpkMetadataService] = None
        
        # State
        self._directory_path: str = self._storage.get(self.STORAGE_KEY_DIRECTORY, '')
        self._vpk_files: List[VpkFile] = []
        self._workshop_files: List[VpkFile] = []
        self._is_loading = False
        self._is_exporting = False  # Track export state
        self._export_elapsed_time: float = 0.0  # Track export elapsed time in seconds
        self._error_message: str = ''
        self._selected_file: Optional[VpkFile] = None
        
        # Selection state - track which files are selected
        self._selected_vpk_files: set = set()  # Store file paths of selected local VPK files
        self._selected_workshop_files: set = set()  # Store file paths of selected workshop files
    
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
    def is_exporting(self) -> bool:
        """Check if export is in progress"""
        return self._is_exporting
    
    @property
    def export_elapsed_time(self) -> float:
        """Get export elapsed time in seconds"""
        return self._export_elapsed_time
    
    @property
    def export_elapsed_time_display(self) -> str:
        """Get formatted export elapsed time for display"""
        elapsed = self._export_elapsed_time
        if elapsed < 60:
            return f"{elapsed:.1f}s"
        else:
            minutes = int(elapsed // 60)
            seconds = elapsed % 60
            return f"{minutes}m {seconds:.1f}s"
    
    @property
    def has_error(self) -> bool:
        return len(self._error_message) > 0
    
    @property
    def error_message(self) -> str:
        return self._error_message
    
    @property
    def selected_file(self) -> Optional[VpkFile]:
        return self._selected_file
    
    @property
    def selected_vpk_files(self) -> set:
        """Get set of selected local VPK file paths"""
        return self._selected_vpk_files
    
    @property
    def selected_workshop_files(self) -> set:
        """Get set of selected workshop file paths"""
        return self._selected_workshop_files
    
    @property
    def has_selected_files(self) -> bool:
        """Check if any files are selected"""
        return len(self._selected_vpk_files) > 0 or len(self._selected_workshop_files) > 0
    
    @property
    def selected_count(self) -> int:
        """Get total count of selected files"""
        return len(self._selected_vpk_files) + len(self._selected_workshop_files)
    
    # Business logic methods
    def set_directory_sync(self, directory: str):
        """Set the working directory and load VPK files (synchronous)"""
        self._directory_path = directory
        self._storage.set(self.STORAGE_KEY_DIRECTORY, directory)
        _safe_print(f"set_directory_sync: saved directory to storage: {directory}")
        self.notify_listeners()
        self.load_vpk_files_sync(directory)
    
    def load_vpk_files_sync(self, directory: str):
        """Load VPK files from directory (synchronous)"""
        self._set_loading(True)
        try:
            self._vpk_files = self._get_vpk_files(directory)
            self._workshop_files = self._get_workshop_files(directory)
            self._error_message = ''
            # Clear selections when loading new directory
            self._selected_vpk_files.clear()
            self._selected_workshop_files.clear()
        except Exception as e:
            self._error_message = str(e)
        finally:
            self._set_loading(False)
    
    async def set_directory(self, directory: str):
        """Set the working directory and load VPK files"""
        self._directory_path = directory
        self.notify_listeners()
        self.load_vpk_files_sync(directory)
    
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
        """Get list of local VPK files from left4dead2\\addons directory"""
        vpk_files = []
        
        # Construct path to addons directory: directory\\left4dead2\\addons
        addons_path = Path(directory) / 'left4dead2' / 'addons'
        
        _safe_print(f"_get_vpk_files: checking addons path: {addons_path}")
        
        if not addons_path.exists():
            _safe_print(f"_get_vpk_files: addons directory does not exist: {addons_path}")
            return vpk_files
        
        # Create hidden config directory at the same level as addons directory
        config_dir = addons_path.parent / '.vpk_config'
        try:
            config_dir.mkdir(parents=True, exist_ok=True)
            _safe_print(f"_get_vpk_files: created config directory: {config_dir}")
        except Exception as e:
            _safe_print(f"_get_vpk_files: failed to create config directory: {e}")
        
        # Initialize metadata service
        self._metadata_service = VpkMetadataService(str(config_dir))
        
        # Iterate through all .vpk and .vpk.disabled files in addons directory (but not in workshop subdirectory)
        for vpk_file_path in sorted(addons_path.glob('*.vpk*')):
            # Skip workshop directory
            if vpk_file_path.parent.name == 'workshop':
                continue
            
            # Check if file is disabled
            is_disabled = vpk_file_path.name.endswith('.disabled')
            
            # Get the actual VPK path (without .disabled if present)
            if is_disabled:
                actual_vpk_path = vpk_file_path.with_suffix('')  # Remove .disabled
            else:
                actual_vpk_path = vpk_file_path
            
            stat = vpk_file_path.stat()
            
            # Look for corresponding .jpg thumbnail
            jpg_path = actual_vpk_path.with_suffix('.jpg')
            thumbnail_path = str(jpg_path) if jpg_path.exists() else None
            
            # Extract or get cached addontitle
            addontitle = None
            if self._metadata_service:
                addontitle = self._metadata_service.get_addontitle(str(vpk_file_path))
            
            vpk_file = VpkFile(
                name=vpk_file_path.name,
                path=str(vpk_file_path),
                size=stat.st_size,
                modified_time=str(stat.st_mtime),
                thumbnail_path=thumbnail_path or '',
                is_disabled=is_disabled,
                addontitle=addontitle,
            )
            vpk_files.append(vpk_file)
            _safe_print(f"_get_vpk_files: found {vpk_file_path.name}, thumbnail={thumbnail_path}, disabled={is_disabled}, addontitle={addontitle}")
        
        _safe_print(f"_get_vpk_files: found {len(vpk_files)} local VPK files")
        return vpk_files
    
    def _get_workshop_files(self, directory: str) -> List[VpkFile]:
        """Get list of Workshop VPK files from left4dead2\\addons\\workshop directory"""
        workshop_files = []
        
        # Construct path to workshop directory: directory\\left4dead2\\addons\\workshop
        workshop_path = Path(directory) / 'left4dead2' / 'addons' / 'workshop'
        
        _safe_print(f"_get_workshop_files: checking workshop path: {workshop_path}")
        
        if not workshop_path.exists():
            _safe_print(f"_get_workshop_files: workshop directory does not exist: {workshop_path}")
            return workshop_files
        
        # Ensure metadata service is initialized
        if not self._metadata_service:
            config_dir = workshop_path.parent.parent / '.vpk_config'
            self._metadata_service = VpkMetadataService(str(config_dir))
        
        # Iterate through all .vpk files in workshop directory
        for vpk_file_path in sorted(workshop_path.glob('*.vpk')):
            stat = vpk_file_path.stat()
            
            # Look for corresponding .jpg thumbnail
            jpg_path = vpk_file_path.with_suffix('.jpg')
            thumbnail_path = str(jpg_path) if jpg_path.exists() else None
            
            # Extract or get cached addontitle
            addontitle = None
            if self._metadata_service:
                addontitle = self._metadata_service.get_addontitle(str(vpk_file_path))
            
            vpk_file = VpkFile(
                name=vpk_file_path.name,
                path=str(vpk_file_path),
                size=stat.st_size,
                modified_time=str(stat.st_mtime),
                thumbnail_path=thumbnail_path or '',
                addontitle=addontitle,
            )
            workshop_files.append(vpk_file)
            _safe_print(f"_get_workshop_files: found {vpk_file_path.name}, thumbnail={thumbnail_path}, addontitle={addontitle}")
        
        _safe_print(f"_get_workshop_files: found {len(workshop_files)} workshop files")
        return workshop_files
    
    def _extract_vpk(self, file_path: str, output_dir: str) -> bool:
        """Extract VPK file"""
        try:
            # Placeholder for VPK extraction logic
            return True
        except Exception as e:
            _safe_print(f"Error extracting VPK: {e}")
            return False
    
    def _set_loading(self, loading: bool):
        """Set loading state"""
        self._is_loading = loading
        self.notify_listeners()
    
    def extract_archive_sync(self, archive_path: str) -> bool:
        """Extract archive file (zip or 7z) to local addons directory (synchronous)"""
        if not self._directory_path:
            self._error_message = 'No directory selected'
            self.notify_listeners()
            return False
        
        self._set_loading(True)
        try:
            archive_path_obj = Path(archive_path)
            if not archive_path_obj.exists():
                self._error_message = f'Archive file not found: {archive_path}'
                return False
            
            # Determine archive type and extract
            if archive_path.lower().endswith('.zip'):
                success = self._extract_zip(archive_path)
            elif archive_path.lower().endswith('.7z'):
                success = self._extract_7z(archive_path)
            elif archive_path.lower().endswith('.tar.zst') or archive_path.lower().endswith('.tar.zstd'):
                success = self._extract_tar_zst(archive_path)
            elif archive_path.lower().endswith('.tar'):
                success = self._extract_tar(archive_path)
            else:
                self._error_message = 'Unsupported archive format. Supported formats: ZIP, 7Z, TAR.ZST, TAR'
                return False
            
            if success:
                # Reload VPK files after extraction
                _safe_print(f"extract_archive_sync: reloading VPK files after extraction")
                self._vpk_files = self._get_vpk_files(self._directory_path)
                self._workshop_files = self._get_workshop_files(self._directory_path)
                self._error_message = ''
                _safe_print(f"extract_archive_sync: extraction and reload completed successfully")
                _safe_print(f"extract_archive_sync: {len(self._vpk_files)} local VPK files, {len(self._workshop_files)} workshop files")
            
            return success
        except Exception as e:
            self._error_message = f'Error extracting archive: {str(e)}'
            _safe_print(f"extract_archive_sync: {self._error_message}")
            return False
        finally:
            self._set_loading(False)
            _safe_print(f"extract_archive_sync: calling notify_listeners()")
            self.notify_listeners()
    
    def _extract_zip(self, zip_path: str) -> bool:
        """Extract ZIP archive to local addons directory (overwrite existing files)"""
        try:
            addons_path = Path(self._directory_path) / 'left4dead2' / 'addons'
            
            # Ensure addons directory exists
            addons_path.mkdir(parents=True, exist_ok=True)
            
            _safe_print(f"_extract_zip: extracting {zip_path} to {addons_path}")
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # extractall() will overwrite existing files by default
                zip_ref.extractall(addons_path)
                
                # Log extracted files
                extracted_files = zip_ref.namelist()
                _safe_print(f"_extract_zip: extracted {len(extracted_files)} file(s)")
                for file in extracted_files[:10]:  # Log first 10 files
                    print(f"  - {file}")
                if len(extracted_files) > 10:
                    _safe_print(f"  ... and {len(extracted_files) - 10} more file(s)")
            
            _safe_print(f"_extract_zip: successfully completed")
            return True
        except Exception as e:
            self._error_message = f'Error extracting ZIP: {str(e)}'
            _safe_print(f"_extract_zip: {self._error_message}")
            return False
    
    def _extract_7z(self, seven_z_path: str) -> bool:
        """Extract 7Z archive to local addons directory (overwrite existing files)"""
        if not HAS_7ZR:
            self._error_message = 'py7zr library not installed. Install with: pip install py7zr'
            _safe_print(f"_extract_7z: {self._error_message}")
            return False
        
        try:
            addons_path = Path(self._directory_path) / 'left4dead2' / 'addons'
            
            # Ensure addons directory exists
            addons_path.mkdir(parents=True, exist_ok=True)
            
            _safe_print(f"_extract_7z: extracting {seven_z_path} to {addons_path}")
            
            with py7zr.SevenZipFile(seven_z_path, 'r') as archive:
                # extractall() will overwrite existing files by default
                archive.extractall(path=addons_path)
                
                # Log archive info
                all_names = archive.getnames()
                _safe_print(f"_extract_7z: extracted {len(all_names)} file(s)")
                for file in all_names[:10]:  # Log first 10 files
                    _safe_print(f"  - {file}")
                if len(all_names) > 10:
                    _safe_print(f"  ... and {len(all_names) - 10} more file(s)")
            
            _safe_print(f"_extract_7z: successfully completed")
            return True
        except Exception as e:
            self._error_message = f'Error extracting 7Z: {str(e)}'
            _safe_print(f"_extract_7z: {self._error_message}")
            return False
    
    def _extract_tar_zst(self, tar_zst_path: str) -> bool:
        """Extract TAR.ZST archive to local addons directory (overwrite existing files)"""
        if not HAS_ZSTD:
            self._error_message = 'zstandard library not installed. Install with: pip install zstandard'
            _safe_print(f"_extract_tar_zst: {self._error_message}")
            return False
        
        try:
            addons_path = Path(self._directory_path) / 'left4dead2' / 'addons'
            
            # Ensure addons directory exists
            addons_path.mkdir(parents=True, exist_ok=True)
            
            print(f"_extract_tar_zst: extracting {tar_zst_path} to {addons_path}")
            
            # Decompress zstd and extract tar
            dctx = zstd.ZstdDecompressor()
            with open(tar_zst_path, 'rb') as f_in:
                with dctx.stream_reader(f_in) as reader:
                    with tarfile.open(fileobj=reader, mode='r|') as tar:
                        # Extract all files
                        tar.extractall(path=addons_path)
                        
                        # Log tar info
                        print(f"_extract_tar_zst: extracted files from archive")
            
            print(f"_extract_tar_zst: successfully completed")
            return True
        except Exception as e:
            self._error_message = f'Error extracting TAR.ZST: {str(e)}'
            print(f"_extract_tar_zst: {self._error_message}")
            return False
    
    def _extract_tar(self, tar_path: str) -> bool:
        """Extract TAR archive to local addons directory (overwrite existing files)"""
        try:
            addons_path = Path(self._directory_path) / 'left4dead2' / 'addons'
            
            # Ensure addons directory exists
            addons_path.mkdir(parents=True, exist_ok=True)
            
            print(f"_extract_tar: extracting {tar_path} to {addons_path}")
            
            # Extract tar archive
            with tarfile.open(tar_path, 'r') as tar:
                # Extract all files
                tar.extractall(path=addons_path)
                
                # Log tar info
                members = tar.getmembers()
                print(f"_extract_tar: extracted {len(members)} file(s)")
                for member in members[:10]:  # Log first 10 files
                    print(f"  - {member.name}")
                if len(members) > 10:
                    print(f"  ... and {len(members) - 10} more file(s)")
            
            print(f"_extract_tar: successfully completed")
            return True
        except Exception as e:
            self._error_message = f'Error extracting TAR: {str(e)}'
            print(f"_extract_tar: {self._error_message}")
            return False
    
    def disable_vpk_sync(self, vpk_file: VpkFile) -> bool:
        """Disable a VPK file by renaming it to .vpk.disabled"""
        try:
            if vpk_file.is_disabled:
                print(f"disable_vpk_sync: VPK is already disabled: {vpk_file.path}")
                return False
            
            vpk_path = Path(vpk_file.path)
            disabled_path = vpk_path.with_suffix(vpk_path.suffix + '.disabled')
            
            print(f"disable_vpk_sync: renaming {vpk_path} to {disabled_path}")
            vpk_path.rename(disabled_path)
            
            # Reload VPK files to reflect changes
            self.load_vpk_files_sync(self._directory_path)
            print(f"disable_vpk_sync: VPK disabled successfully")
            return True
        except Exception as e:
            self._error_message = f'Error disabling VPK: {str(e)}'
            print(f"disable_vpk_sync: {self._error_message}")
            self.notify_listeners()
            return False
    
    def enable_vpk_sync(self, vpk_file: VpkFile) -> bool:
        """Enable a VPK file by renaming it from .vpk.disabled to .vpk"""
        try:
            if not vpk_file.is_disabled:
                print(f"enable_vpk_sync: VPK is not disabled: {vpk_file.path}")
                return False
            
            vpk_path = Path(vpk_file.path)
            # Remove .disabled suffix
            enabled_path = vpk_path.with_suffix('')
            
            print(f"enable_vpk_sync: renaming {vpk_path} to {enabled_path}")
            vpk_path.rename(enabled_path)
            
            # Reload VPK files to reflect changes
            self.load_vpk_files_sync(self._directory_path)
            print(f"enable_vpk_sync: VPK enabled successfully")
            return True
        except Exception as e:
            self._error_message = f'Error enabling VPK: {str(e)}'
            print(f"enable_vpk_sync: {self._error_message}")
            self.notify_listeners()
            return False
    
    def delete_vpk_sync(self, vpk_file: VpkFile) -> bool:
        """Delete a VPK file and its thumbnail"""
        try:
            vpk_path = Path(vpk_file.path)
            
            # Delete VPK file
            if vpk_path.exists():
                print(f"delete_vpk_sync: deleting {vpk_path}")
                vpk_path.unlink()
            
            # Delete thumbnail if it exists
            if vpk_file.thumbnail_path:
                thumbnail_path = Path(vpk_file.thumbnail_path)
                if thumbnail_path.exists():
                    print(f"delete_vpk_sync: deleting thumbnail {thumbnail_path}")
                    thumbnail_path.unlink()
            
            # Reload VPK files to reflect changes
            self.load_vpk_files_sync(self._directory_path)
            print(f"delete_vpk_sync: VPK deleted successfully")
            return True
        except Exception as e:
            self._error_message = f'Error deleting VPK: {str(e)}'
            print(f"delete_vpk_sync: {self._error_message}")
            self.notify_listeners()
            return False
    
    def toggle_vpk_selection(self, vpk_file: VpkFile) -> bool:
        """Toggle selection of a local VPK file. Returns True if selected, False if deselected"""
        if vpk_file.path in self._selected_vpk_files:
            self._selected_vpk_files.remove(vpk_file.path)
            print(f"toggle_vpk_selection: deselected {vpk_file.name}")
            is_selected = False
        else:
            # Deselect workshop files when selecting local VPK
            self._selected_workshop_files.clear()
            self._selected_vpk_files.add(vpk_file.path)
            print(f"toggle_vpk_selection: selected {vpk_file.name}")
            is_selected = True
        self.notify_listeners()
        return is_selected
    
    def toggle_workshop_selection(self, workshop_file: VpkFile) -> bool:
        """Toggle selection of a workshop file. Returns True if selected, False if deselected"""
        if workshop_file.path in self._selected_workshop_files:
            self._selected_workshop_files.remove(workshop_file.path)
            print(f"toggle_workshop_selection: deselected {workshop_file.name}")
            is_selected = False
        else:
            # Deselect local VPK files when selecting workshop file
            self._selected_vpk_files.clear()
            self._selected_workshop_files.add(workshop_file.path)
            print(f"toggle_workshop_selection: selected {workshop_file.name}")
            is_selected = True
        self.notify_listeners()
        return is_selected
    
    def clear_selection(self):
        """Clear all selections"""
        self._selected_vpk_files.clear()
        self._selected_workshop_files.clear()
        self.notify_listeners()
    
    def get_selected_files(self) -> List[VpkFile]:
        """Get list of selected VpkFile objects"""
        selected_files = []
        
        # Get selected local VPK files
        for vpk_file in self._vpk_files:
            if vpk_file.path in self._selected_vpk_files:
                selected_files.append(vpk_file)
        
        # Get selected workshop files
        for workshop_file in self._workshop_files:
            if workshop_file.path in self._selected_workshop_files:
                selected_files.append(workshop_file)
        
        return selected_files
    
    def export_selected_vpk_files_sync(self, output_dir: str) -> bool:
        """Export selected VPK files to 7z archive (synchronous)"""
        from features.vpk_manager.services.vpk_export_service import VpkExportService
        
        selected_files = self.get_selected_files()
        if not selected_files:
            self._error_message = 'No files selected for export'
            self.notify_listeners()
            return False
        
        self._is_exporting = True
        self.notify_listeners()
        
        try:
            success, message, elapsed_time = VpkExportService.export_vpk_files_to_7z(selected_files, output_dir)
            self._export_elapsed_time = elapsed_time
            if success:
                self._error_message = ''
                # Clear selection after successful export
                self.clear_selection()
                print(f"export_selected_vpk_files_sync: export completed successfully in {elapsed_time:.2f} seconds")
            else:
                self._error_message = message
                print(f"export_selected_vpk_files_sync: export failed - {message}")
            
            return success
        except Exception as e:
            self._error_message = f'Error exporting VPK files: {str(e)}'
            print(f"export_selected_vpk_files_sync: {self._error_message}")
            return False
        finally:
            self._is_exporting = False
            self.notify_listeners()
    
    def delete_selected_vpk_files_sync(self) -> bool:
        """Delete selected VPK files (synchronous)"""
        from features.vpk_manager.services.vpk_export_service import VpkExportService
        
        selected_files = self.get_selected_files()
        if not selected_files:
            self._error_message = 'No files selected for deletion'
            self.notify_listeners()
            return False
        
        self._is_exporting = True  # Reuse exporting flag to block operations
        self.notify_listeners()
        
        try:
            success, message = VpkExportService.delete_vpk_files(selected_files)
            if success:
                self._error_message = ''
                # Reload VPK files to reflect deletions
                self.load_vpk_files_sync(self._directory_path)
                print(f"delete_selected_vpk_files_sync: deletion completed successfully")
            else:
                self._error_message = message
                print(f"delete_selected_vpk_files_sync: deletion failed - {message}")
            
            return success
        except Exception as e:
            self._error_message = f'Error deleting VPK files: {str(e)}'
            print(f"delete_selected_vpk_files_sync: {self._error_message}")
            return False
        finally:
            self._is_exporting = False
            self.notify_listeners()
    
    def dispose(self):
        """Clean up resources"""
        super().dispose()
        self._vpk_files.clear()
        self._workshop_files.clear()
        self._selected_file: Optional[VpkFile] = None
        self._selected_vpk_files.clear()
        self._selected_workshop_files.clear()
