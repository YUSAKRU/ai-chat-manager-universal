import re
import asyncio
import os
import mimetypes
from typing import Dict, List, Any
import logging
import sys

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from plugin_manager import BasePlugin

logger = logging.getLogger(__name__)

class DocumentReaderPlugin(BasePlugin):
    """
    Document Reader Plugin - Analyzes uploaded files and provides summaries.
    
    Triggers:
    - [analyze: "file_path"]
    - [document: "file_path"]
    - [read: "file_path"]  
    - [summarize: "file_path"]
    - When files are uploaded via the web interface
    """
    
    def __init__(self):
        super().__init__()
        self.supported_formats = {
            '.txt': self._read_text_file,
            '.md': self._read_markdown_file,
            '.py': self._read_code_file,
            '.js': self._read_code_file,
            '.html': self._read_html_file,
            '.json': self._read_json_file,
            '.csv': self._read_csv_file,
            '.log': self._read_text_file
        }
        self.upload_dir = "uploads"
        
        # Create uploads directory if it doesn't exist
        os.makedirs(self.upload_dir, exist_ok=True)
        
    def get_triggers(self) -> List[str]:
        """Return regex patterns that trigger document analysis"""
        return [
            r'\[analyze:\s*["\']([^"\']+)["\']\s*\]',
            r'\[document:\s*["\']([^"\']+)["\']\s*\]',
            r'\[read:\s*["\']([^"\']+)["\']\s*\]',
            r'\[summarize:\s*["\']([^"\']+)["\']\s*\]',
            r'\[dosya:\s*["\']([^"\']+)["\']\s*\]',
            r'FILE_UPLOADED:\s*([^\s]+)'  # Special trigger for file uploads
        ]
    
    async def execute(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute document analysis based on detected triggers"""
        try:
            # Extract file paths from all triggers
            file_paths = []
            
            for trigger_pattern in self.get_triggers():
                matches = re.finditer(trigger_pattern, message, re.IGNORECASE)
                for match in matches:
                    file_path = match.group(1).strip()
                    if file_path:
                        file_paths.append(file_path)
            
            if not file_paths:
                return {}
            
            # Process each file
            analysis_results = []
            for file_path in file_paths:
                logger.info(f"Analyzing document: {file_path}")
                
                result = await self._analyze_document(file_path, context)
                if result:
                    analysis_results.append(result)
            
            if analysis_results:
                return {
                    'type': 'document_analysis_result',
                    'role': '📄 Doküman Analisti',
                    'content': self._format_analysis_results(analysis_results),
                    'files': file_paths,
                    'timestamp': context.get('timestamp', ''),
                    'metadata': {
                        'file_count': len(analysis_results),
                        'supported_formats': list(self.supported_formats.keys())
                    }
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"Error in DocumentReaderPlugin: {str(e)}")
            return {
                'type': 'plugin_error',
                'role': '📄 Doküman Analisti',
                'content': f"Doküman analizi sırasında hata oluştu: {str(e)}",
                'error': str(e)
            }
    
    def _format_analysis_results(self, analysis_results: List[Dict[str, Any]]) -> str:
        """Format analysis results for display in chat"""
        formatted_results = []
        
        for analysis in analysis_results:
            file_path = analysis.get('file_path', 'Unknown file')
            status = analysis.get('status', 'unknown')
            
            if status == 'error':
                result_text = f"❌ **{os.path.basename(file_path)}**\n"
                result_text += f"   Hata: {analysis.get('error', 'Unknown error')}\n\n"
            elif status == 'unsupported':
                result_text = f"⚠️ **{os.path.basename(file_path)}**\n"
                result_text += f"   Desteklenmeyen format: {analysis.get('file_type', 'Unknown')}\n\n"
            else:
                result_text = f"✅ **{os.path.basename(file_path)}**\n"
                result_text += f"   📏 Boyut: {analysis.get('file_size', 0)} bytes\n"
                result_text += f"   📝 Tür: {analysis.get('content_type', 'Unknown')}\n"
                
                # Add specific content info
                if 'word_count' in analysis:
                    result_text += f"   📊 {analysis['word_count']} kelime, {analysis['line_count']} satır\n"
                if 'function_count' in analysis:
                    result_text += f"   🔧 {analysis['function_count']} fonksiyon, {analysis['class_count']} sınıf\n"
                if 'column_count' in analysis:
                    result_text += f"   📋 {analysis['column_count']} sütun, {analysis['row_count']} satır\n"
                
                result_text += f"   📄 Özet: {analysis.get('summary', 'No summary available')}\n\n"
                
                # Add preview if available
                if 'preview' in analysis:
                    result_text += f"   **Önizleme:**\n```\n{analysis['preview'][:200]}...\n```\n\n"
            
            formatted_results.append(result_text)
        
        return "\n" + "="*50 + "\n".join(formatted_results)
    
    async def _analyze_document(self, file_path: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a single document"""
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                # Try in uploads directory
                upload_path = os.path.join(self.upload_dir, file_path)
                if os.path.exists(upload_path):
                    file_path = upload_path
                else:
                    return {
                        'file_path': file_path,
                        'error': 'File not found',
                        'status': 'error'
                    }
            
            # Get file info
            file_size = os.path.getsize(file_path)
            file_ext = os.path.splitext(file_path)[1].lower()
            mime_type, _ = mimetypes.guess_type(file_path)
            
            # Check if format is supported
            if file_ext not in self.supported_formats:
                return {
                    'file_path': file_path,
                    'file_size': file_size,
                    'file_type': file_ext,
                    'mime_type': mime_type,
                    'error': f'Unsupported format: {file_ext}',
                    'status': 'unsupported'
                }
            
            # Read and analyze the file
            reader_func = self.supported_formats[file_ext]
            content_analysis = await reader_func(file_path)
            
            return {
                'file_path': file_path,
                'file_size': file_size,
                'file_type': file_ext,
                'mime_type': mime_type,
                'status': 'success',
                **content_analysis
            }
            
        except Exception as e:
            logger.error(f"Error analyzing document {file_path}: {str(e)}")
            return {
                'file_path': file_path,
                'error': str(e),
                'status': 'error'
            }
    
    async def _read_text_file(self, file_path: str) -> Dict[str, Any]:
        """Read and analyze plain text files"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Basic analysis
            lines = content.split('\n')
            words = content.split()
            chars = len(content)
            
            # Generate summary (first few lines and basic stats)
            summary_lines = lines[:5] if len(lines) > 5 else lines
            summary = '\n'.join(summary_lines)
            if len(lines) > 5:
                summary += f"\n... ({len(lines) - 5} more lines)"
            
            return {
                'content_type': 'text',
                'line_count': len(lines),
                'word_count': len(words),
                'char_count': chars,
                'summary': summary,
                'preview': content[:500] + "..." if len(content) > 500 else content
            }
            
        except Exception as e:
            return {'error': f'Failed to read text file: {str(e)}'}
    
    async def _read_markdown_file(self, file_path: str) -> Dict[str, Any]:
        """Read and analyze markdown files"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Extract headers
            headers = re.findall(r'^#+\s+(.+)$', content, re.MULTILINE)
            
            # Basic analysis
            lines = content.split('\n')
            words = content.split()
            
            return {
                'content_type': 'markdown',
                'line_count': len(lines),
                'word_count': len(words),
                'header_count': len(headers),
                'headers': headers[:10],  # First 10 headers
                'summary': f"Markdown document with {len(headers)} headers",
                'preview': content[:500] + "..." if len(content) > 500 else content
            }
            
        except Exception as e:
            return {'error': f'Failed to read markdown file: {str(e)}'}
    
    async def _read_code_file(self, file_path: str) -> Dict[str, Any]:
        """Read and analyze code files"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            lines = content.split('\n')
            
            # Basic code analysis
            import_lines = [line for line in lines if line.strip().startswith(('import ', 'from '))]
            function_lines = [line for line in lines if 'def ' in line or 'function ' in line]
            class_lines = [line for line in lines if line.strip().startswith('class ')]
            comment_lines = [line for line in lines if line.strip().startswith(('#', '//', '/*'))]
            
            return {
                'content_type': 'code',
                'line_count': len(lines),
                'import_count': len(import_lines),
                'function_count': len(function_lines),
                'class_count': len(class_lines),
                'comment_count': len(comment_lines),
                'imports': [line.strip() for line in import_lines[:10]],
                'functions': [line.strip() for line in function_lines[:10]],
                'summary': f"Code file with {len(function_lines)} functions, {len(class_lines)} classes",
                'preview': content[:500] + "..." if len(content) > 500 else content
            }
            
        except Exception as e:
            return {'error': f'Failed to read code file: {str(e)}'}
    
    async def _read_html_file(self, file_path: str) -> Dict[str, Any]:
        """Read and analyze HTML files"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Extract basic HTML info
            title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
            title = title_match.group(1).strip() if title_match else "No title found"
            
            # Count basic HTML elements
            links = len(re.findall(r'<a\s+[^>]*href', content, re.IGNORECASE))
            images = len(re.findall(r'<img\s+[^>]*src', content, re.IGNORECASE))
            scripts = len(re.findall(r'<script', content, re.IGNORECASE))
            
            return {
                'content_type': 'html',
                'title': title,
                'link_count': links,
                'image_count': images,
                'script_count': scripts,
                'summary': f"HTML document: '{title}' with {links} links, {images} images",
                'preview': content[:500] + "..." if len(content) > 500 else content
            }
            
        except Exception as e:
            return {'error': f'Failed to read HTML file: {str(e)}'}
    
    async def _read_json_file(self, file_path: str) -> Dict[str, Any]:
        """Read and analyze JSON files"""
        try:
            import json
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                data = json.load(f)
            
            def count_items(obj, depth=0):
                if depth > 3:  # Prevent deep recursion
                    return 0
                if isinstance(obj, dict):
                    return len(obj) + sum(count_items(v, depth+1) for v in obj.values())
                elif isinstance(obj, list):
                    return len(obj) + sum(count_items(item, depth+1) for item in obj)
                return 1
            
            total_items = count_items(data)
            
            return {
                'content_type': 'json',
                'structure_type': type(data).__name__,
                'total_items': total_items,
                'top_level_keys': list(data.keys()) if isinstance(data, dict) else None,
                'summary': f"JSON {type(data).__name__} with {total_items} total items",
                'preview': str(data)[:500] + "..." if len(str(data)) > 500 else str(data)
            }
            
        except Exception as e:
            return {'error': f'Failed to read JSON file: {str(e)}'}
    
    async def _read_csv_file(self, file_path: str) -> Dict[str, Any]:
        """Read and analyze CSV files"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            if not lines:
                return {'error': 'Empty CSV file'}
            
            # Assume first line is header
            header = lines[0].strip().split(',')
            data_rows = len(lines) - 1
            
            return {
                'content_type': 'csv',
                'column_count': len(header),
                'row_count': data_rows,
                'columns': [col.strip().strip('"') for col in header],
                'summary': f"CSV with {len(header)} columns and {data_rows} data rows",
                'preview': ''.join(lines[:5]) + "..." if len(lines) > 5 else ''.join(lines)
            }
            
        except Exception as e:
            return {'error': f'Failed to read CSV file: {str(e)}'}
