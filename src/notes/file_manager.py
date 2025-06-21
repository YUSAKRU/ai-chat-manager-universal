"""
Notes File Manager
==================

Notlar için dosya yükleme, saklama ve yönetim sistemi.
"""

import os
import uuid
import hashlib
import mimetypes
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
import shutil
import json

try:
    from PIL import Image, ImageOps
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from ..logger import logger

class NotesFileManager:
    """Not dosyalarını yöneten sınıf"""
    
    def __init__(self, upload_dir: str = "uploads"):
        """Initialize file manager"""
        # Use absolute path from current working directory
        # This is more reliable than relative path calculations
        current_dir = Path(os.getcwd())
        self.upload_dir = current_dir / upload_dir
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Alt dizinler
        self.images_dir = self.upload_dir / "images"
        self.documents_dir = self.upload_dir / "documents"
        self.thumbnails_dir = self.upload_dir / "thumbnails"
        self.temp_dir = self.upload_dir / "temp"
        
        # Dizinleri oluştur
        for directory in [self.images_dir, self.documents_dir, self.thumbnails_dir, self.temp_dir]:
            directory.mkdir(parents=True, exist_ok=True)
            
        # Desteklenen dosya türleri
        self.allowed_extensions = {
            'images': {'jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp'},
            'documents': {'pdf', 'doc', 'docx', 'txt', 'md', 'rtf'},
            'spreadsheets': {'xls', 'xlsx', 'csv'},
            'other': {'json', 'xml', 'yml', 'yaml'}
        }
        
        # Dosya boyutu limitleri (MB)
        self.size_limits = {
            'images': 10,
            'documents': 50,
            'spreadsheets': 25,
            'other': 10
        }
        
        # Metadata dosyası
        self.metadata_file = self.upload_dir / "file_metadata.json"
        self.metadata = self._load_metadata()
        
        logger.info(f"File Manager initialized. Upload dir: {self.upload_dir}")
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Dosya metadata'sını yükle"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Metadata loading error: {e}")
        return {}
    
    def _save_metadata(self):
        """Dosya metadata'sını kaydet"""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Metadata saving error: {e}")
    
    def get_file_category(self, filename: str) -> str:
        """Dosya kategorisini belirle"""
        extension = filename.lower().split('.')[-1] if '.' in filename else ''
        
        for category, extensions in self.allowed_extensions.items():
            if extension in extensions:
                return category
        return 'other'
    
    def validate_file(self, filename: str, file_size: int) -> Tuple[bool, str]:
        """Dosyayı doğrula"""
        if not filename or filename.startswith('.'):
            return False, "Geçersiz dosya adı"
        
        category = self.get_file_category(filename)
        extension = filename.lower().split('.')[-1] if '.' in filename else ''
        
        all_extensions = set()
        for exts in self.allowed_extensions.values():
            all_extensions.update(exts)
        
        if extension not in all_extensions:
            return False, f"Desteklenmeyen dosya türü: .{extension}"
        
        max_size_mb = self.size_limits.get(category, 10)
        max_size_bytes = max_size_mb * 1024 * 1024
        
        if file_size > max_size_bytes:
            return False, f"Dosya çok büyük. Maksimum: {max_size_mb}MB"
        
        return True, "OK"
    
    def generate_file_hash(self, file_path: Path) -> str:
        """Dosya hash'i oluştur"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def create_thumbnail(self, image_path: Path, file_id: str) -> Optional[str]:
        """Resim için thumbnail oluştur"""
        if not PIL_AVAILABLE:
            return None
            
        try:
            with Image.open(image_path) as img:
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                img.thumbnail((300, 300), Image.Resampling.LANCZOS)
                
                thumbnail_path = self.thumbnails_dir / f"{file_id}_thumb.jpg"
                img.save(thumbnail_path, 'JPEG', quality=85)
                
                return str(thumbnail_path.relative_to(self.upload_dir))
        except Exception as e:
            logger.error(f"Thumbnail creation error: {e}")
            return None
    
    def upload_file(self, file_data: bytes, filename: str, note_id: Optional[str] = None) -> Dict[str, Any]:
        """Dosya yükle"""
        try:
            file_size = len(file_data)
            is_valid, error_msg = self.validate_file(filename, file_size)
            
            if not is_valid:
                return {'success': False, 'error': error_msg}
            
            file_id = str(uuid.uuid4())
            category = self.get_file_category(filename)
            
            if category == 'images':
                target_dir = self.images_dir
            else:
                target_dir = self.documents_dir
            
            file_extension = filename.split('.')[-1] if '.' in filename else ''
            final_filename = f"{file_id}.{file_extension}"
            final_path = target_dir / final_filename
            
            with open(final_path, 'wb') as f:
                f.write(file_data)
            
            file_hash = self.generate_file_hash(final_path)
            mime_type, _ = mimetypes.guess_type(filename)
            
            thumbnail_path = None
            if category == 'images':
                thumbnail_path = self.create_thumbnail(final_path, file_id)
            
            metadata = {
                'id': file_id,
                'original_filename': filename,
                'stored_filename': final_filename,
                'file_path': str(final_path.relative_to(self.upload_dir)),
                'thumbnail_path': thumbnail_path,
                'file_size': file_size,
                'mime_type': mime_type,
                'category': category,
                'hash': file_hash,
                'upload_date': datetime.now().isoformat(),
                'notes': [note_id] if note_id else []
            }
            
            self.metadata[file_id] = metadata
            self._save_metadata()
            
            logger.info(f"File uploaded: {filename} -> {file_id}")
            
            return {
                'success': True,
                'file_id': file_id,
                'file_info': metadata
            }
            
        except Exception as e:
            logger.error(f"File upload error: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_file_info(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Dosya bilgilerini getir"""
        return self.metadata.get(file_id)
    
    def get_note_files(self, note_id: str) -> List[Dict[str, Any]]:
        """Note'un dosyalarını getir"""
        files = []
        for file_id, metadata in self.metadata.items():
            if note_id in metadata.get('notes', []):
                files.append(metadata)
        return files
    
    def get_file_path(self, file_id: str) -> Optional[Path]:
        """Dosya yolunu getir"""
        file_info = self.get_file_info(file_id)
        if not file_info:
            return None
        
        # Use the stored file_path from metadata
        stored_path = file_info.get('file_path')
        if stored_path:
            return self.upload_dir / stored_path
        
        # Fallback to old method if file_path not available
        category = file_info.get('category', 'other')
        stored_filename = file_info.get('stored_filename', f"{file_id}")
        
        if category == 'images':
            return self.upload_dir / 'images' / stored_filename
        else:
            return self.upload_dir / 'documents' / stored_filename
    
    def get_thumbnail_path(self, file_id: str) -> Optional[Path]:
        """Thumbnail yolunu getir"""
        file_info = self.get_file_info(file_id)
        if not file_info or file_info.get('category') != 'images':
            return None
        
        return self.upload_dir / 'thumbnails' / f"{file_id}_thumb.jpg"
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Storage istatistikleri"""
        total_files = len(self.metadata)
        total_size = sum(metadata['file_size'] for metadata in self.metadata.values())
        
        return {
            'total_files': total_files,
            'total_size': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2)
        }
    
    def delete_file(self, file_id: str, note_id: Optional[str] = None) -> Dict[str, Any]:
        """Dosyayı sil"""
        try:
            # Get file info from metadata
            file_info = self.get_file_info(file_id)
            if not file_info:
                return {'success': False, 'error': 'Dosya bulunamadı'}
            
            # Delete physical file
            file_path = self.get_file_path(file_id)
            if file_path and file_path.exists():
                file_path.unlink()
            
            # Delete thumbnail (if exists)
            thumbnail_path = self.get_thumbnail_path(file_id)
            if thumbnail_path and thumbnail_path.exists():
                thumbnail_path.unlink()
            
            # Remove from metadata
            if file_id in self.metadata:
                del self.metadata[file_id]
                self._save_metadata()
            
            logger.info(f"File deleted: {file_id}")
            return {'success': True, 'message': 'Dosya başarıyla silindi'}
            
        except Exception as e:
            logger.error(f"File deletion failed for file {file_id}: {e}")
            return {'success': False, 'error': str(e)}
 