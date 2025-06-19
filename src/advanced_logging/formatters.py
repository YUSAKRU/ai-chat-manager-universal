"""
Logging Formatters - JSON ve Plain text formatları
"""
import logging
import json
import sys
import traceback
from datetime import datetime
from typing import Dict, Any


class JSONFormatter(logging.Formatter):
    """
    JSON formatında log kaydı oluşturan formatter
    
    Çıktı örneği:
    {
        "timestamp": "2025-06-19T17:45:30.123Z",
        "level": "INFO", 
        "logger": "ai_chrome_chat_manager",
        "component": "web_ui",
        "message": "Request processed successfully",
        "data": {...},
        "context": {...}
    }
    """
    
    def __init__(self, include_extra: bool = True):
        super().__init__()
        self.include_extra = include_extra
    
    def format(self, record: logging.LogRecord) -> str:
        """LogRecord'u JSON formatına dönüştür"""
        try:
            # Temel log verisi
            log_data = {
                "timestamp": datetime.fromtimestamp(record.created).isoformat() + 'Z',
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno
            }
            
            # Thread bilgileri
            if hasattr(record, 'thread'):
                log_data["thread"] = record.thread
                log_data["thread_name"] = record.threadName
            
            # Process bilgileri
            if hasattr(record, 'process'):
                log_data["process"] = record.process
            
            # Exception bilgileri
            if record.exc_info:
                log_data["exception"] = {
                    "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                    "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                    "traceback": self.formatException(record.exc_info)
                }
            
            # Extra alanları ekle
            if self.include_extra:
                extra_data = {}
                
                # LogRecord'daki ekstra alanları topla
                for key, value in record.__dict__.items():
                    if key not in ('name', 'msg', 'args', 'levelname', 'levelno', 
                                 'pathname', 'filename', 'module', 'exc_info', 
                                 'exc_text', 'stack_info', 'lineno', 'funcName',
                                 'created', 'msecs', 'relativeCreated', 'thread',
                                 'threadName', 'processName', 'process', 'getMessage'):
                        try:
                            # JSON serializable olup olmadığını kontrol et
                            json.dumps(value)
                            extra_data[key] = value
                        except (TypeError, ValueError):
                            # Serialize edilemeyenler için string representation
                            extra_data[key] = str(value)
                
                if extra_data:
                    log_data["extra"] = extra_data
            
            # Request context (eğer thread local'da varsa)
            context = self._get_request_context()
            if context:
                log_data["context"] = context
            
            return json.dumps(log_data, ensure_ascii=False, separators=(',', ':'))
            
        except Exception as e:
            # Formatter hatası durumunda fallback
            fallback_data = {
                "timestamp": datetime.utcnow().isoformat() + 'Z',
                "level": "ERROR",
                "logger": "JSONFormatter",
                "message": f"Formatting error: {str(e)}",
                "original_message": record.getMessage() if hasattr(record, 'getMessage') else str(record),
                "error": str(e)
            }
            return json.dumps(fallback_data, ensure_ascii=False)
    
    def _get_request_context(self) -> Dict[str, Any]:
        """Thread local'dan request context'ini al"""
        import threading
        context = {}
        current_thread = threading.current_thread()
        
        # Request ID
        if hasattr(current_thread, 'request_id'):
            context['request_id'] = current_thread.request_id
        
        # User session
        if hasattr(current_thread, 'user_session'):
            context['user_session'] = current_thread.user_session
        
        # HTTP request bilgileri
        if hasattr(current_thread, 'http_method'):
            context['http_method'] = current_thread.http_method
        
        if hasattr(current_thread, 'endpoint'):
            context['endpoint'] = current_thread.endpoint
        
        if hasattr(current_thread, 'ip_address'):
            context['ip_address'] = current_thread.ip_address
        
        # Performance metrikleri
        if hasattr(current_thread, 'request_start_time'):
            elapsed = datetime.utcnow().timestamp() - current_thread.request_start_time
            context['request_duration'] = round(elapsed, 3)
        
        return context


class PlainTextFormatter(logging.Formatter):
    """
    Okunabilir plain text formatında log kaydı oluşturan formatter
    
    Çıktı örneği:
    2025-06-19 17:45:30.123 | INFO | web_ui | Request processed successfully | REQ-123456
    """
    
    def __init__(self, 
                 format_string: str = None,
                 include_context: bool = True,
                 colored_output: bool = None):
        self.include_context = include_context
        self.colored_output = colored_output if colored_output is not None else self._supports_color()
        
        if format_string is None:
            format_string = self._get_default_format()
        
        super().__init__(format_string)
    
    def _get_default_format(self) -> str:
        """Varsayılan format string'i"""
        if self.colored_output:
            return "%(asctime)s | %(colored_level)s | %(component)s | %(message)s"
        else:
            return "%(asctime)s | %(levelname)-8s | %(component)s | %(message)s"
    
    def _supports_color(self) -> bool:
        """Terminal renk desteğini kontrol et"""
        # Windows CMD/PowerShell renk desteği
        if sys.platform == "win32":
            import os
            return os.environ.get('TERM') in ('xterm', 'xterm-256color') or 'ANSICON' in os.environ
        
        # Unix-like sistemler
        return hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()
    
    def format(self, record: logging.LogRecord) -> str:
        """LogRecord'u plain text formatına dönüştür"""
        try:
            # Component bilgisini ekle (yoksa logger adını kullan)
            if not hasattr(record, 'component'):
                # Logger adından component çıkar (logger_name:component formatında ise)
                if ':' in record.name:
                    record.component = record.name.split(':', 1)[1]
                else:
                    record.component = record.name.split('.')[-1]
            
            # Renkli level (eğer destekleniyorsa)
            if self.colored_output:
                record.colored_level = self._colorize_level(record.levelname)
            
            # Context bilgilerini ekle
            context_parts = []
            
            if self.include_context:
                import threading
                current_thread = threading.current_thread()
                
                # Request ID
                if hasattr(current_thread, 'request_id'):
                    context_parts.append(f"[{current_thread.request_id}]")
                
                # User session
                if hasattr(current_thread, 'user_session'):
                    context_parts.append(f"[User: {current_thread.user_session}]")
                
                # Performance info
                if hasattr(current_thread, 'request_start_time'):
                    elapsed = datetime.utcnow().timestamp() - current_thread.request_start_time
                    context_parts.append(f"[{elapsed:.3f}s]")
            
            # Ana formatı uygula
            formatted = super().format(record)
            
            # Context'i ekle
            if context_parts:
                formatted += " " + " ".join(context_parts)
            
            # Exception bilgilerini ekle
            if record.exc_info:
                formatted += "\n" + self.formatException(record.exc_info)
            
            return formatted
            
        except Exception as e:
            # Formatter hatası durumunda fallback
            return f"{datetime.utcnow().isoformat()} | ERROR | PlainTextFormatter | Formatting error: {str(e)}"
    
    def _colorize_level(self, level: str) -> str:
        """Log level'ını renklendir"""
        colors = {
            'DEBUG': '\033[36m',      # Cyan
            'INFO': '\033[32m',       # Green  
            'WARNING': '\033[33m',    # Yellow
            'ERROR': '\033[31m',      # Red
            'CRITICAL': '\033[35m'    # Magenta
        }
        reset = '\033[0m'
        
        color = colors.get(level, '')
        return f"{color}{level:<8}{reset}"


class CompactJSONFormatter(JSONFormatter):
    """
    Daha kompakt JSON formatı - debug/development için
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Kompakt JSON formatı"""
        try:
            log_data = {
                "ts": datetime.fromtimestamp(record.created).strftime('%H:%M:%S.%f')[:-3],
                "lvl": record.levelname[0],  # I, W, E, C, D
                "comp": getattr(record, 'component', record.name.split('.')[-1]),
                "msg": record.getMessage()
            }
            
            # Request ID (kısa format)
            import threading
            if hasattr(threading.current_thread(), 'request_id'):
                req_id = threading.current_thread().request_id
                # Sadece son 8 karakteri al
                log_data["req"] = req_id[-8:] if len(req_id) > 8 else req_id
            
            # Exception (varsa)
            if record.exc_info:
                log_data["exc"] = record.exc_info[0].__name__ if record.exc_info[0] else "Unknown"
            
            return json.dumps(log_data, ensure_ascii=False, separators=(',', ':'))
            
        except Exception as e:
            return f'{{"ts":"{datetime.utcnow().strftime("%H:%M:%S")}","lvl":"E","comp":"Formatter","msg":"Format error: {str(e)}"}}'


class StructuredTextFormatter(logging.Formatter):
    """
    Yapılandırılmış ancak okunabilir text formatı
    
    Çıktı örneği:
    [2025-06-19 17:45:30] INFO web_ui: Request processed successfully
        ├─ request_id: REQ-123456
        ├─ duration: 0.123s
        └─ status: success
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Yapılandırılmış text formatı"""
        try:
            # Ana satır
            timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
            component = getattr(record, 'component', record.name.split('.')[-1])
            
            lines = [f"[{timestamp}] {record.levelname} {component}: {record.getMessage()}"]
            
            # Extra bilgileri alt satırlara ekle
            extra_items = []
            
            # Thread context
            import threading
            current_thread = threading.current_thread()
            
            if hasattr(current_thread, 'request_id'):
                extra_items.append(f"request_id: {current_thread.request_id}")
            
            if hasattr(current_thread, 'request_start_time'):
                elapsed = datetime.utcnow().timestamp() - current_thread.request_start_time
                extra_items.append(f"duration: {elapsed:.3f}s")
            
            # Record'daki extra alanlar
            for key, value in record.__dict__.items():
                if key not in ('name', 'msg', 'args', 'levelname', 'levelno', 
                             'pathname', 'filename', 'module', 'exc_info', 
                             'exc_text', 'stack_info', 'lineno', 'funcName',
                             'created', 'msecs', 'relativeCreated', 'thread',
                             'threadName', 'processName', 'process', 'getMessage',
                             'component'):
                    extra_items.append(f"{key}: {value}")
            
            # Extra items'ları tree formatında ekle
            for i, item in enumerate(extra_items):
                if i == len(extra_items) - 1:
                    lines.append(f"    └─ {item}")
                else:
                    lines.append(f"    ├─ {item}")
            
            # Exception bilgisi
            if record.exc_info:
                lines.append("    └─ exception:")
                exc_lines = self.formatException(record.exc_info).split('\n')
                for exc_line in exc_lines:
                    if exc_line.strip():
                        lines.append(f"       {exc_line}")
            
            return '\n'.join(lines)
            
        except Exception as e:
            return f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}] ERROR StructuredTextFormatter: Format error: {str(e)}" 