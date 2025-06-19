"""
Custom Logging Handlers - Özelleştirilmiş log handler'ları
"""
import logging
import logging.handlers
import os
import gzip
import shutil
import time
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import threading
import queue
import json


class RotatingFileHandler(logging.handlers.RotatingFileHandler):
    """
    Geliştirilmiş rotating file handler
    - Automatic compression
    - Better rotation logic  
    - Archive management
    """
    
    def __init__(self, 
                 filename: str,
                 maxBytes: int = 100*1024*1024,  # 100MB
                 backupCount: int = 10,
                 encoding: str = 'utf-8',
                 compress: bool = True,
                 archive_dir: Optional[str] = None):
        
        super().__init__(filename, maxBytes=maxBytes, backupCount=backupCount, encoding=encoding)
        self.compress = compress
        self.archive_dir = Path(archive_dir) if archive_dir else Path(filename).parent / 'archived'
        
        # Archive dizinini oluştur
        self.archive_dir.mkdir(parents=True, exist_ok=True)
    
    def doRollover(self):
        """Geliştirilmiş rollover işlemi"""
        if self.stream:
            self.stream.close()
            self.stream = None
        
        # Mevcut log dosyasını yedekle
        base_filename = self.baseFilename
        
        # Backup dosyalarını kaydır
        for i in range(self.backupCount - 1, 0, -1):
            sfn = f"{base_filename}.{i}"
            dfn = f"{base_filename}.{i + 1}"
            
            if os.path.exists(sfn):
                if os.path.exists(dfn):
                    os.remove(dfn)
                os.rename(sfn, dfn)
        
        # En son backup'ı arşivle
        if self.backupCount > 0:
            old_log = f"{base_filename}.{self.backupCount}"
            if os.path.exists(old_log):
                self._archive_log_file(old_log)
        
        # Ana dosyayı backup olarak taşı
        if os.path.exists(base_filename):
            dfn = f"{base_filename}.1"
            if os.path.exists(dfn):
                os.remove(dfn)
            os.rename(base_filename, dfn)
        
        # Yeni stream aç
        if not self.delay:
            self.stream = self._open()
    
    def _archive_log_file(self, log_file_path: str):
        """Log dosyasını arşivle"""
        try:
            log_path = Path(log_file_path)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            if self.compress:
                # Gzip ile sıkıştır
                archive_name = f"{log_path.stem}_{timestamp}.log.gz"
                archive_path = self.archive_dir / archive_name
                
                with open(log_file_path, 'rb') as f_in:
                    with gzip.open(archive_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
            else:
                # Sadece taşı
                archive_name = f"{log_path.stem}_{timestamp}.log"
                archive_path = self.archive_dir / archive_name
                shutil.move(log_file_path, archive_path)
            
            # Orijinal dosyayı sil
            if os.path.exists(log_file_path):
                os.remove(log_file_path)
                
        except Exception:
            # Arşivleme hatası durumunda dosyayı sadece sil
            if os.path.exists(log_file_path):
                os.remove(log_file_path)


class APITrackingHandler(logging.StreamHandler):
    """
    API çağrılarını izleyen özel handler
    - API metrics collection
    - Rate limiting detection
    - Cost tracking
    """
    
    def __init__(self, stream=None):
        super().__init__(stream)
        self.api_stats = {
            'total_calls': 0,
            'total_cost': 0.0,
            'total_tokens': 0,
            'by_provider': {},
            'by_model': {},
            'errors': 0,
            'last_reset': datetime.utcnow().isoformat()
        }
        self.stats_lock = threading.Lock()
    
    def emit(self, record):
        """API log'larını işle ve istatistikleri güncelle"""
        try:
            # Sadece API tracker component'ini işle
            if hasattr(record, 'component') and record.component == 'api_tracker':
                self._update_api_stats(record)
            
            # Normal log işlemeye devam et
            super().emit(record)
            
        except Exception:
            self.handleError(record)
    
    def _update_api_stats(self, record):
        """API istatistiklerini güncelle"""
        try:
            message = record.getMessage()
            
            # JSON formatındaysa parse et
            if message.startswith('{'):
                try:
                    log_data = json.loads(message)
                    data = log_data.get('data', {})
                except json.JSONDecodeError:
                    return
            else:
                return
            
            with self.stats_lock:
                self.api_stats['total_calls'] += 1
                
                # Cost tracking
                cost = data.get('cost', 0)
                self.api_stats['total_cost'] += cost
                
                # Token tracking
                tokens = data.get('total_tokens', 0)
                self.api_stats['total_tokens'] += tokens
                
                # Provider stats
                provider = data.get('provider', 'unknown')
                if provider not in self.api_stats['by_provider']:
                    self.api_stats['by_provider'][provider] = {
                        'calls': 0, 'cost': 0.0, 'tokens': 0
                    }
                
                self.api_stats['by_provider'][provider]['calls'] += 1
                self.api_stats['by_provider'][provider]['cost'] += cost
                self.api_stats['by_provider'][provider]['tokens'] += tokens
                
                # Model stats
                model = data.get('model', 'unknown')
                if model not in self.api_stats['by_model']:
                    self.api_stats['by_model'][model] = {
                        'calls': 0, 'cost': 0.0, 'tokens': 0
                    }
                
                self.api_stats['by_model'][model]['calls'] += 1
                self.api_stats['by_model'][model]['cost'] += cost
                self.api_stats['by_model'][model]['tokens'] += tokens
                
        except Exception:
            pass
    
    def get_api_stats(self) -> Dict[str, Any]:
        """API istatistiklerini döndür"""
        with self.stats_lock:
            return self.api_stats.copy()
    
    def reset_stats(self):
        """İstatistikleri sıfırla"""
        with self.stats_lock:
            self.api_stats = {
                'total_calls': 0,
                'total_cost': 0.0,
                'total_tokens': 0,
                'by_provider': {},
                'by_model': {},
                'errors': 0,
                'last_reset': datetime.utcnow().isoformat()
            } 