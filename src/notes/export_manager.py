"""
Notes Export Manager
===================

Notları farklı formatlarda export etme sistemi.
"""

import os
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import tempfile
from pathlib import Path

from ..logger import logger


class NotesExportManager:
    """Not export işlemlerini yöneten sınıf"""
    
    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = output_dir or tempfile.gettempdir()
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        
        # Export formatları (temel formatlar - kütüphane bağımlılığı yok)
        self.available_formats = {
            'markdown': True,
            'html': True,
            'json': True,
            'txt': True
        }
        
        logger.info(f"Export Manager initialized. Available formats: {list(self.available_formats.keys())}")
    
    def export_single_note(self, note: Dict[str, Any], format_type: str = 'markdown') -> str:
        """Tek bir notu export et"""
        if format_type not in self.available_formats:
            raise ValueError(f"Desteklenmeyen format: {format_type}")
        
        # Dosya adı oluştur
        safe_title = self._safe_filename(note.get('title', 'Untitled'))
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_title}_{timestamp}.{format_type}"
        filepath = os.path.join(self.output_dir, filename)
        
        # Format'a göre export
        if format_type == 'markdown':
            content = self._export_to_markdown(note)
        elif format_type == 'html':
            content = self._export_to_html(note)
        elif format_type == 'json':
            content = self._export_to_json(note)
        elif format_type == 'txt':
            content = self._export_to_txt(note)
        
        # Dosyaya yaz
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Note exported: {filepath}")
        return filepath
    
    def export_multiple_notes(self, notes: List[Dict[str, Any]], 
                            format_type: str = 'markdown') -> List[str]:
        """Birden fazla notu export et"""
        if not notes:
            raise ValueError("Export edilecek not bulunamadı")
        
        exported_files = []
        
        # Her notu export et
        for note in notes:
            try:
                filepath = self.export_single_note(note, format_type)
                exported_files.append(filepath)
            except Exception as e:
                logger.error(f"Note export failed for {note.get('title', 'Unknown')}: {e}")
        
        return exported_files
    
    def export_workspace_summary(self, workspace_name: str, notes: List[Dict[str, Any]]) -> str:
        """Workspace özeti oluştur"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self._safe_filename(workspace_name)}_summary_{timestamp}.md"
        filepath = os.path.join(self.output_dir, filename)
        
        lines = []
        lines.append(f"# {workspace_name} - Workspace Summary")
        lines.append("")
        lines.append(f"**Export Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**Total Notes:** {len(notes)}")
        lines.append("")
        
        # Notes listesi
        lines.append("## Notes List")
        lines.append("")
        
        for i, note in enumerate(notes, 1):
            title = note.get('title', 'Untitled')
            created = note.get('created_at', 'Unknown')
            lines.append(f"{i}. **{title}** (Created: {created})")
            
            # Preview
            content = note.get('content', '')
            clean_content = re.sub(r'<[^>]+>', '', content)
            preview = clean_content[:100] + "..." if len(clean_content) > 100 else clean_content
            if preview.strip():
                lines.append(f"   _{preview}_")
            lines.append("")
        
        content = "\n".join(lines)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Workspace summary exported: {filepath}")
        return filepath
    
    def _export_to_markdown(self, note: Dict[str, Any]) -> str:
        """Markdown formatına export"""
        lines = []
        
        # Başlık
        title = note.get('title', 'Untitled')
        lines.append(f"# {title}")
        lines.append("")
        
        # Metadata
        lines.append("## Metadata")
        lines.append("")
        lines.append(f"- **Created:** {note.get('created_at', 'Unknown')}")
        lines.append(f"- **Updated:** {note.get('updated_at', 'Unknown')}")
        lines.append(f"- **Author:** {note.get('created_by', 'Unknown')}")
        
        if note.get('tags'):
            tag_names = [tag.get('name', tag) if isinstance(tag, dict) else str(tag) for tag in note['tags']]
            lines.append(f"- **Tags:** {', '.join(tag_names)}")
        
        lines.append("")
        
        # İçerik
        lines.append("## Content")
        lines.append("")
        
        content = note.get('content', '')
        # HTML etiketlerini temizle
        clean_content = re.sub(r'<[^>]+>', '', content)
        lines.append(clean_content)
        
        lines.append("")
        lines.append("---")
        lines.append(f"*Exported from AI Notes on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        
        return "\n".join(lines)
    
    def _export_to_html(self, note: Dict[str, Any]) -> str:
        """HTML formatına export"""
        title = note.get('title', 'Untitled')
        content = note.get('content', '')
        
        html = f"""<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
        }}
        .metadata {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 20px;
            font-size: 14px;
        }}
        .tags {{
            margin-top: 20px;
        }}
        .tag {{
            display: inline-block;
            background: #007bff;
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            margin-right: 5px;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            font-size: 12px;
            color: #666;
            text-align: center;
        }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    
    <div class="metadata">
        <strong>Created:</strong> {note.get('created_at', 'Unknown')}<br>
        <strong>Updated:</strong> {note.get('updated_at', 'Unknown')}<br>
        <strong>Author:</strong> {note.get('created_by', 'Unknown')}
    </div>
    
    <div class="content">
        {content}
    </div>
    
    {"<div class='tags'>" + "".join([f"<span class='tag'>{tag.get('name', tag) if isinstance(tag, dict) else str(tag)}</span>" for tag in note.get('tags', [])]) + "</div>" if note.get('tags') else ""}
    
    <div class="footer">
        Exported from AI Notes on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    </div>
</body>
</html>"""
        return html
    
    def _export_to_json(self, note: Dict[str, Any]) -> str:
        """JSON formatına export"""
        export_data = {
            'export_date': datetime.now().isoformat(),
            'export_version': '1.0',
            'note': note
        }
        return json.dumps(export_data, indent=2, ensure_ascii=False)
    
    def _export_to_txt(self, note: Dict[str, Any]) -> str:
        """Plain text formatına export"""
        lines = []
        
        # Başlık
        title = note.get('title', 'Untitled')
        lines.append(title)
        lines.append("=" * len(title))
        lines.append("")
        
        # Metadata
        lines.append(f"Created: {note.get('created_at', 'Unknown')}")
        lines.append(f"Updated: {note.get('updated_at', 'Unknown')}")
        lines.append(f"Author: {note.get('created_by', 'Unknown')}")
        
        if note.get('tags'):
            tag_names = [tag.get('name', tag) if isinstance(tag, dict) else str(tag) for tag in note['tags']]
            lines.append(f"Tags: {', '.join(tag_names)}")
        
        lines.append("")
        lines.append("-" * 50)
        lines.append("")
        
        # İçerik
        content = note.get('content', '')
        # HTML etiketlerini temizle
        clean_content = re.sub(r'<[^>]+>', '', content)
        lines.append(clean_content)
        
        lines.append("")
        lines.append("-" * 50)
        lines.append(f"Exported from AI Notes on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return "\n".join(lines)
    
    def _safe_filename(self, filename: str) -> str:
        """Güvenli dosya adı oluştur"""
        # Tehlikeli karakterleri temizle
        safe = re.sub(r'[<>:"/\\|?*]', '_', filename)
        safe = re.sub(r'\s+', '_', safe)  # Boşlukları underscore yap
        safe = safe[:100]  # Maksimum 100 karakter
        return safe if safe else 'untitled'
    
    def get_available_formats(self) -> Dict[str, bool]:
        """Kullanılabilir export formatlarını döndür"""
        return self.available_formats.copy()
 