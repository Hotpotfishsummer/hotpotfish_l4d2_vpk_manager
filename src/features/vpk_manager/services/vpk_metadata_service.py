"""VPK metadata extraction and caching service"""

import json
from pathlib import Path
from typing import Optional, Dict, Any
import vpk


def _safe_print(msg: str):
    """Safe print that handles encoding errors"""
    try:
        print(msg)
    except UnicodeEncodeError:
        # If encoding fails, replace problematic characters
        print(msg.encode('utf-8', errors='replace').decode('utf-8', errors='replace'))


class VpkMetadataService:
    """Service for extracting and caching VPK metadata"""
    
    def __init__(self, config_dir: str):
        """Initialize metadata service with config directory"""
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def get_json_path(self, vpk_file_path: str) -> Path:
        """Get the JSON file path for a VPK file"""
        vpk_name = Path(vpk_file_path).stem  # Get filename without extension
        return self.config_dir / f"{vpk_name}.json"
    
    def load_metadata(self, vpk_file_path: str) -> Optional[Dict[str, Any]]:
        """Load metadata from JSON file if it exists"""
        json_path = self.get_json_path(vpk_file_path)
        if json_path.exists():
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                _safe_print(f"load_metadata: failed to load JSON {json_path}: {e}")
        return None
    
    def save_metadata(self, vpk_file_path: str, metadata: Optional[Dict[str, Any]]) -> bool:
        """Save metadata to JSON file"""
        json_path = self.get_json_path(vpk_file_path)
        try:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(metadata or {}, f, ensure_ascii=False, indent=2)
            _safe_print(f"save_metadata: saved metadata to {json_path}")
            return True
        except Exception as e:
            _safe_print(f"save_metadata: failed to save JSON {json_path}: {e}")
            return False
    
    def extract_addontitle(self, vpk_file_path: str) -> Optional[str]:
        """Extract addontitle from VPK file"""
        try:
            # Try to open VPK file
            vpk_file = vpk.VPK(vpk_file_path)
            
            # Look for addoninfo.txt in the VPK
            if 'addoninfo.txt' in vpk_file:
                # Try multiple encodings to handle various character sets
                addoninfo_data = None
                for encoding in ['utf-8', 'utf-16', 'gbk', 'latin-1']:
                    try:
                        addoninfo_data = vpk_file['addoninfo.txt'].read().decode(encoding)
                        break
                    except (UnicodeDecodeError, LookupError):
                        continue
                
                # If all encodings fail, use utf-8 with error handling
                if addoninfo_data is None:
                    addoninfo_data = vpk_file['addoninfo.txt'].read().decode('utf-8', errors='replace')
                
                addontitle = self._parse_addontitle(addoninfo_data)
                return addontitle
            else:
                _safe_print(f"extract_addontitle: addoninfo.txt not found in {vpk_file_path}")
                return None
        except Exception as e:
            _safe_print(f"extract_addontitle: failed to extract from {vpk_file_path}: {e}")
            return None
    
    def _parse_addontitle(self, addoninfo_content: str) -> Optional[str]:
        """Parse addontitle from addoninfo.txt content"""
        try:
            for line in addoninfo_content.split('\n'):
                line = line.strip()
                if line.startswith('addontitle'):
                    # Extract value between quotes
                    # Format: addontitle "value"
                    parts = line.split('"')
                    if len(parts) >= 2:
                        return parts[1]
            return None
        except Exception as e:
            _safe_print(f"_parse_addontitle: failed to parse addoninfo content: {e}")
            return None
    
    def get_or_extract_metadata(self, vpk_file_path: str) -> Optional[Dict[str, Any]]:
        """Get metadata from cache or extract from VPK"""
        # First, try to load from JSON cache
        cached_metadata = self.load_metadata(vpk_file_path)
        if cached_metadata is not None:
            _safe_print(f"get_or_extract_metadata: using cached metadata for {vpk_file_path}")
            return cached_metadata
        
        # If not cached, extract from VPK
        _safe_print(f"get_or_extract_metadata: extracting metadata from {vpk_file_path}")
        addontitle = self.extract_addontitle(vpk_file_path)
        
        # Create metadata dict (even if empty for error cases)
        metadata = {
            'addontitle': addontitle
        } if addontitle else {}
        
        # Save to cache
        self.save_metadata(vpk_file_path, metadata)
        
        return metadata if metadata else None
    
    def get_addontitle(self, vpk_file_path: str) -> Optional[str]:
        """Get addontitle for a VPK file (from cache or extracted)"""
        metadata = self.get_or_extract_metadata(vpk_file_path)
        if metadata and 'addontitle' in metadata:
            return metadata['addontitle']
        return None
