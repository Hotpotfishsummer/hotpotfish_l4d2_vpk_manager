"""VPK Export Service - handles exporting VPK files with zstandard compression"""

from pathlib import Path
from typing import List, Optional, TYPE_CHECKING
import shutil
import os
import time
import tarfile
import multiprocessing

try:
    import zstandard as zstd
    HAS_ZSTD = True
except ImportError:
    HAS_ZSTD = False

if TYPE_CHECKING:
    from features.vpk_manager.viewmodels.vpk_manager_viewmodel import VpkFile


class VpkExportService:
    """Service for exporting and deleting VPK files"""
    
    @staticmethod
    def export_vpk_files_to_7z(vpk_files: List['VpkFile'], output_dir: str) -> tuple[bool, str, float]:
        """
        Export selected VPK files and their thumbnails to a zstandard compressed tar archive.
        
        Args:
            vpk_files: List of VpkFile objects to export
            output_dir: Output directory (typically Downloads)
        
        Returns:
            Tuple of (success: bool, message: str, elapsed_time: float)
        """
        start_time = time.time()
        
        if not HAS_ZSTD:
            return False, 'zstandard library not installed. Install with: pip install zstandard', 0.0
        
        if not vpk_files:
            return False, 'No files selected for export', 0.0
        
        try:
            # Create output directory if it doesn't exist
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Generate archive name from addontitles
            archive_name = VpkExportService._generate_archive_name(vpk_files)
            archive_path = output_path / f"{archive_name}.tar.zst"
            
            print(f"export_vpk_files_to_7z: creating archive {archive_path}")
            
            # Create temporary directory for collecting files
            temp_dir = output_path / '.vpk_temp'
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            try:
                # Copy VPK files and thumbnails to temp directory
                for vpk_file in vpk_files:
                    vpk_path = Path(vpk_file.path)
                    
                    # Copy VPK file
                    if vpk_path.exists():
                        dest = temp_dir / vpk_path.name
                        print(f"export_vpk_files_to_7z: copying {vpk_path} to {dest}")
                        shutil.copy2(vpk_path, dest)
                    
                    # Copy thumbnail if it exists
                    if vpk_file.thumbnail_path:
                        thumb_path = Path(vpk_file.thumbnail_path)
                        if thumb_path.exists():
                            dest = temp_dir / thumb_path.name
                            print(f"export_vpk_files_to_7z: copying thumbnail {thumb_path} to {dest}")
                            shutil.copy2(thumb_path, dest)
                
                # Create tar.zst archive with zstandard compression
                print(f"export_vpk_files_to_7z: creating zstandard compressed archive with high compression")
                
                # Get system CPU count for multi-threaded compression
                num_threads = max(1, multiprocessing.cpu_count() - 1)  # Leave one core free
                print(f"export_vpk_files_to_7z: using {num_threads} threads for compression")
                
                # Create zstandard context with maximum compression level and multi-threading
                cctx = zstd.ZstdCompressor(
                    level=3,  # Maximum compression level (1-22, default 3)
                    threads=num_threads,  # Multi-threaded compression
                    write_checksum=True,  # Include checksum for integrity verification
                )
                
                # Create tar archive and compress with zstandard
                print(f"export_vpk_files_to_7z: compressing files into {archive_path}")
                with open(archive_path, 'wb') as f_out:
                    with cctx.stream_writer(f_out, closefd=False) as writer:
                        with tarfile.open(fileobj=writer, mode='w|') as tar:
                            # Add all files from temp directory to tar
                            for file_path in sorted(temp_dir.iterdir()):
                                if file_path.is_file():
                                    print(f"export_vpk_files_to_7z: adding {file_path.name} to archive")
                                    tar.add(file_path, arcname=file_path.name)
                
                elapsed_time = time.time() - start_time
                archive_size = archive_path.stat().st_size / (1024 * 1024)  # Size in MB
                print(f"export_vpk_files_to_7z: successfully created {archive_path} ({archive_size:.2f} MB) in {elapsed_time:.2f} seconds")
                return True, f"Archive created: {archive_path} ({archive_size:.2f} MB)", elapsed_time
            
            finally:
                # Clean up temp directory
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)
                    print(f"export_vpk_files_to_7z: cleaned up temp directory")
        
        except Exception as e:
            error_msg = f'Error exporting VPK files: {str(e)}'
            print(f"export_vpk_files_to_7z: {error_msg}")
            elapsed_time = time.time() - start_time
            return False, error_msg, elapsed_time
    
    @staticmethod
    def delete_vpk_files(vpk_files: List['VpkFile']) -> tuple[bool, str]:
        """
        Delete VPK files and their thumbnails.
        
        Args:
            vpk_files: List of VpkFile objects to delete
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        if not vpk_files:
            return False, 'No files selected for deletion'
        
        try:
            deleted_count = 0
            
            for vpk_file in vpk_files:
                vpk_path = Path(vpk_file.path)
                
                # Delete VPK file
                if vpk_path.exists():
                    print(f"delete_vpk_files: deleting {vpk_path}")
                    vpk_path.unlink()
                    deleted_count += 1
                
                # Delete thumbnail if it exists
                if vpk_file.thumbnail_path:
                    thumb_path = Path(vpk_file.thumbnail_path)
                    if thumb_path.exists():
                        print(f"delete_vpk_files: deleting thumbnail {thumb_path}")
                        thumb_path.unlink()
            
            message = f'Successfully deleted {deleted_count} file(s)'
            print(f"delete_vpk_files: {message}")
            return True, message
        
        except Exception as e:
            error_msg = f'Error deleting VPK files: {str(e)}'
            print(f"delete_vpk_files: {error_msg}")
            return False, error_msg
    
    @staticmethod
    def _generate_archive_name(vpk_files: List['VpkFile']) -> str:
        """Generate archive filename from addontitles of selected files"""
        addontitles = []
        
        for vpk_file in vpk_files:
            if vpk_file.addontitle and vpk_file.addontitle not in addontitles:
                addontitles.append(vpk_file.addontitle)
        
        if addontitles:
            archive_name = '-'.join(addontitles)
        else:
            # Fallback to using filenames if no addontitles
            filenames = [Path(vpk.path).stem for vpk in vpk_files]
            archive_name = '-'.join(filenames[:3])  # Limit to first 3 names
            
            if len(filenames) > 3:
                archive_name += f"-and-{len(filenames) - 3}-more"
        
        # Sanitize filename (remove invalid characters)
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            archive_name = archive_name.replace(char, '_')
        
        print(f"_generate_archive_name: generated archive name: {archive_name}")
        return archive_name
    
    @staticmethod
    def get_downloads_directory() -> str:
        """Get user's Downloads directory path"""
        if os.name == 'nt':  # Windows
            # Try using environment variable first
            downloads = os.environ.get('USERPROFILE')
            if downloads:
                downloads = str(Path(downloads) / 'Downloads')
                if Path(downloads).exists():
                    return downloads
        else:  # macOS and Linux
            downloads = os.path.expanduser('~/Downloads')
            if Path(downloads).exists():
                return downloads
        
        # Fallback to home directory
        return os.path.expanduser('~')
