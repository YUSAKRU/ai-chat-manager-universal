"""
📤 ExportEngine - Multi-format Document Export
==============================================

Belgeleri farklı formatlara export etme:
- PDF export (HTML-to-PDF)
- Word export (python-docx)
- HTML export (styled templates)
- Markdown export (raw/formatted)
"""

import os
import tempfile
from typing import Optional, Dict, Any
from datetime import datetime


class ExportEngine:
    """Multi-format Document Export Engine"""
    
    def __init__(self, output_dir="generated_documents"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    async def html_to_pdf(self, html_content: str, filename: str) -> Optional[str]:
        """
        HTML içeriğini PDF'e çevir
        Note: Bu basit implementation. Production'da weasyprint veya puppeteer kullanılabilir.
        """
        try:
            # For now, just return the HTML path as we don't have PDF conversion setup
            # In future, we can integrate weasyprint or similar
            print("⚠️ PDF export requires additional setup (weasyprint/puppeteer)")
            return None
            
        except Exception as e:
            print(f"🚨 PDF export error: {e}")
            return None
    
    def markdown_to_html(self, markdown_content: str, title: str = "Document") -> str:
        """
        Markdown'ı styled HTML'e çevir
        """
        try:
            # Simple markdown to HTML conversion
            # In production, use markdown library
            
            html_template = f"""<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        {self._get_export_styles()}
    </style>
</head>
<body>
    <div class="container">
        <div class="content">
            {self._markdown_to_html_simple(markdown_content)}
        </div>
    </div>
</body>
</html>"""
            
            return html_template
            
        except Exception as e:
            print(f"🚨 Markdown to HTML conversion error: {e}")
            return markdown_content
    
    def save_file(self, content: str, filename: str, file_format: str = "txt") -> str:
        """
        İçeriği dosya olarak kaydet
        """
        try:
            full_filename = f"{filename}.{file_format}"
            file_path = os.path.join(self.output_dir, full_filename)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"💾 Dosya kaydedildi: {file_path}")
            return file_path
            
        except Exception as e:
            print(f"🚨 File save error: {e}")
            raise
    
    def _markdown_to_html_simple(self, markdown_content: str) -> str:
        """
        Basit markdown to HTML conversion
        Production'da markdown library kullanılacak
        """
        html = markdown_content
        
        # Headers
        html = html.replace('# ', '<h1>').replace('\n', '</h1>\n', 1)
        html = html.replace('## ', '<h2>').replace('\n', '</h2>\n')
        html = html.replace('### ', '<h3>').replace('\n', '</h3>\n')
        
        # Bold
        import re
        html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
        
        # Lists
        lines = html.split('\n')
        in_list = False
        result_lines = []
        
        for line in lines:
            if line.strip().startswith('- '):
                if not in_list:
                    result_lines.append('<ul>')
                    in_list = True
                result_lines.append(f'<li>{line.strip()[2:]}</li>')
            else:
                if in_list:
                    result_lines.append('</ul>')
                    in_list = False
                result_lines.append(line)
        
        if in_list:
            result_lines.append('</ul>')
        
        # Paragraphs
        html = '\n'.join(result_lines)
        html = html.replace('\n\n', '</p><p>')
        html = f'<p>{html}</p>'
        
        return html
    
    def _get_export_styles(self) -> str:
        """Export için CSS stilleri"""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #fff;
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
            padding: 40px 20px;
        }
        
        h1, h2, h3 {
            margin-bottom: 20px;
            color: #2c3e50;
        }
        
        h1 {
            font-size: 2.5em;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }
        
        h2 {
            font-size: 1.8em;
            border-left: 4px solid #3498db;
            padding-left: 15px;
            margin-top: 30px;
        }
        
        h3 {
            font-size: 1.3em;
            color: #34495e;
        }
        
        p {
            margin-bottom: 15px;
        }
        
        ul {
            margin-bottom: 20px;
            padding-left: 30px;
        }
        
        li {
            margin-bottom: 8px;
        }
        
        strong {
            color: #2c3e50;
        }
        
        @media print {
            body {
                font-size: 12pt;
            }
            
            .container {
                max-width: none;
                margin: 0;
                padding: 20px;
            }
        }
        """
    
    def get_supported_formats(self) -> Dict[str, str]:
        """Desteklenen export formatları"""
        return {
            'markdown': 'Markdown (.md)',
            'html': 'HTML (.html)',
            'pdf': 'PDF (.pdf) - Requires setup',
            'docx': 'Word Document (.docx) - Future'
        }
    
    def validate_filename(self, filename: str) -> str:
        """Dosya adını validate et ve temizle"""
        import re
        
        # Invalid characters'ları temizle
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # Uzunluğu sınırla
        if len(filename) > 200:
            filename = filename[:200]
        
        # Boşlukları underscore'a çevir
        filename = filename.replace(' ', '_')
        
        return filename 