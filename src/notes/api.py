"""
Notes API Endpoints
===================

Not sistemi için Flask API endpoint'leri.
"""

from flask import Blueprint, request, jsonify, session, send_file
from typing import Dict, Any
import json
from functools import wraps

from .database import NotesDatabase
from .models import Note, NoteWorkspace
from .ai_integration import NotesAIIntegration
from .export_manager import NotesExportManager
from .file_manager import NotesFileManager
from ..logger import logger
import asyncio
import os
import tempfile
from werkzeug.utils import secure_filename

# Blueprint oluştur
notes_blueprint = Blueprint('notes', __name__, url_prefix='/api/notes')

# Database instance
notes_db = NotesDatabase()

# AI Integration (will be initialized from main app)
ai_integration = None

# Export Manager
export_manager = NotesExportManager()

# File Manager
file_manager = NotesFileManager()

def init_ai_integration(ai_adapter):
    """AI entegrasyonunu başlat"""
    global ai_integration
    ai_integration = NotesAIIntegration(ai_adapter)


@notes_blueprint.route('/workspaces', methods=['GET'])
def get_workspaces():
    """Kullanıcının workspace'lerini listele"""
    user_id = request.args.get('user_id', 'default_user')
    
    try:
        workspaces = notes_db.get_user_workspaces(user_id)
        return jsonify({
            'success': True,
            'workspaces': [workspace.to_dict() for workspace in workspaces]
        })
    except Exception as e:
        logger.error(f"Workspace listing failed for user {user_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@notes_blueprint.route('/workspaces', methods=['POST'])
def create_workspace():
    """Yeni workspace oluştur"""
    data = request.get_json()
    
    name = data.get('name')
    description = data.get('description', '')
    created_by = data.get('created_by', 'default_user')
    
    if not name:
        return jsonify({'success': False, 'error': 'Workspace adı gerekli'}), 400
    
    try:
        workspace = notes_db.create_workspace(name, created_by, description)
        return jsonify({
            'success': True,
            'workspace': workspace.to_dict()
        })
    except Exception as e:
        logger.error(f"Workspace creation failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@notes_blueprint.route('/', methods=['GET'])
def get_notes():
    """Notları listele"""
    workspace_id = request.args.get('workspace_id')
    limit = int(request.args.get('limit', 50))
    query = request.args.get('q', '')
    
    try:
        if query:
            notes = notes_db.search_notes(workspace_id, query)
        else:
            notes = notes_db.get_notes(workspace_id, limit=limit)
        
        return jsonify({
            'success': True,
            'notes': [note.to_dict() for note in notes]
        })
    except Exception as e:
        logger.error(f"Notes listing failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@notes_blueprint.route('/', methods=['POST'])
def create_note():
    """Yeni not oluştur"""
    data = request.get_json()
    
    title = data.get('title', 'Yeni Not')
    content = data.get('content', 'Notunuzu yazmaya başlayın...')
    workspace_id = data.get('workspace_id')
    created_by = data.get('created_by', 'default_user')
    
    if not workspace_id:
        return jsonify({'success': False, 'error': 'Workspace ID gerekli'}), 400
    
    try:
        note = notes_db.create_note(
            title=title, 
            workspace_id=workspace_id, 
            created_by=created_by,
            content=content
        )
        return jsonify({
            'success': True,
            'note': note.to_dict()
        })
    except Exception as e:
        logger.error(f"Note creation failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@notes_blueprint.route('/<note_id>', methods=['GET'])
def get_note(note_id):
    """Belirli bir notu getir"""
    increment_view = request.args.get('increment_view', 'false').lower() == 'true'
    
    try:
        note = notes_db.get_note(note_id, increment_view=increment_view)
        if not note:
            return jsonify({'success': False, 'error': 'Not bulunamadı'}), 404
        
        # Note'a ait dosyaları da getir
        files = file_manager.get_note_files(note_id)
        note_dict = note.to_dict()
        note_dict['files'] = files
        
        return jsonify({
            'success': True,
            'note': note_dict
        })
    except Exception as e:
        logger.error(f"Note fetch failed for note {note_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@notes_blueprint.route('/<note_id>', methods=['PUT'])
def update_note(note_id):
    """Notu güncelle"""
    data = request.get_json()
    
    try:
        updated_note = notes_db.update_note(
            note_id=note_id,
            title=data.get('title'),
            content=data.get('content'),
            is_pinned=data.get('is_pinned'),
            edited_by=data.get('edited_by', 'default_user')
        )
        
        if updated_note:
            logger.info(f"Note updated: {note_id} by {data.get('edited_by', 'default_user')}")
            return jsonify({
                'success': True,
                'note': updated_note.to_dict()
            })
        else:
            return jsonify({'success': False, 'error': 'Not bulunamadı'}), 404
            
    except Exception as e:
        logger.error(f"Note update failed for note {note_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@notes_blueprint.route('/<note_id>', methods=['DELETE'])
def delete_note(note_id):
    """Notu sil"""
    try:
        success = notes_db.delete_note(note_id)
        
        if success:
            return jsonify({'success': True, 'message': 'Not silindi'})
        else:
            return jsonify({'success': False, 'error': 'Not bulunamadı'}), 404
            
    except Exception as e:
        logger.error(f"Note deletion failed for note {note_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@notes_blueprint.route('/<note_id>/archive', methods=['POST'])
def archive_note(note_id):
    """Notu arşivle"""
    success = notes_db.archive_note(note_id)
    
    if not success:
        return jsonify({'success': False, 'error': 'Not bulunamadı'}), 404
    
    return jsonify({
        'success': True,
        'message': 'Not başarıyla arşivlendi'
    })


@notes_blueprint.route('/tree/<workspace_id>', methods=['GET'])
def get_note_tree(workspace_id):
    """Not hiyerarşisini getir"""
    tree = notes_db.get_note_tree(workspace_id)
    
    return jsonify({
        'success': True,
        'tree': tree
    })


@notes_blueprint.route('/recent/<workspace_id>', methods=['GET'])
def get_recent_notes(workspace_id):
    """Son düzenlenen notları getir"""
    limit = int(request.args.get('limit', 10))
    
    try:
        notes = notes_db.get_recent_notes(workspace_id, limit)
        return jsonify({
            'success': True,
            'notes': [note.to_dict() for note in notes]
        })
    except Exception as e:
        logger.error(f"Recent notes fetch failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@notes_blueprint.route('/pinned/<workspace_id>', methods=['GET'])
def get_pinned_notes(workspace_id):
    """Sabitlenmiş notları getir"""
    try:
        notes = notes_db.get_pinned_notes(workspace_id)
        return jsonify({
            'success': True,
            'notes': [note.to_dict() for note in notes]
        })
    except Exception as e:
        logger.error(f"Pinned notes fetch failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@notes_blueprint.route('/tags/<workspace_id>', methods=['GET'])
def list_tags(workspace_id):
    """Workspace'deki etiketleri listele"""
    tags = notes_db.list_tags(workspace_id)
    
    return jsonify({
        'success': True,
        'tags': [
            {
                'id': tag.id,
                'name': tag.name,
                'color': tag.color
            }
            for tag in tags
        ]
    })


@notes_blueprint.route('/tags/<workspace_id>/popular', methods=['GET'])
def get_popular_tags(workspace_id):
    """En çok kullanılan etiketleri getir"""
    limit = int(request.args.get('limit', 10))
    
    tags = notes_db.get_popular_tags(workspace_id, limit=limit)
    
    return jsonify({
        'success': True,
        'tags': tags
    })


@notes_blueprint.route('/stats/<workspace_id>', methods=['GET'])
def get_workspace_stats(workspace_id):
    """Workspace istatistiklerini getir"""
    stats = notes_db.get_workspace_stats(workspace_id)
    
    return jsonify({
        'success': True,
        'stats': stats
    })


@notes_blueprint.route('/<note_id>/pin', methods=['POST'])
def pin_note(note_id):
    """Notu sabitle/sabitlemeyi kaldır"""
    try:
        # Get note
        note = notes_db.get_note(note_id)
        if not note:
            return jsonify({'success': False, 'error': 'Not bulunamadı'}), 404
        
        # Toggle pin status
        data = request.get_json() or {}
        new_pin_status = not note.is_pinned  # Toggle current status
        
        # If pinned status explicitly provided, use it
        if 'pinned' in data:
            new_pin_status = data['pinned']
        
        # Update note
        updated_note = notes_db.update_note(
            note_id=note_id,
            is_pinned=new_pin_status,
            edited_by='default_user'
        )
        
        if not updated_note:
            return jsonify({'success': False, 'error': 'Pin güncelleme başarısız'}), 500
        
        logger.info(f"Note pin status changed: {note_id} -> {new_pin_status}")
        
        return jsonify({
            'success': True,
            'note': updated_note.to_dict(),
            'message': f'Not {"sabitlendi" if new_pin_status else "sabitleme kaldırıldı"}'
        })
        
    except Exception as e:
        logger.error(f"Pin operation failed for note {note_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# AI Endpoints
@notes_blueprint.route('/<note_id>/ai/analyze', methods=['POST'])
def ai_analyze_note(note_id):
    """AI ile not analizi"""
    if not ai_integration:
        return jsonify({'success': False, 'error': 'AI entegrasyonu mevcut değil'}), 500
    
    try:
        note = notes_db.get_note(note_id)
        if not note:
            return jsonify({'success': False, 'error': 'Not bulunamadı'}), 404
        
        # AI analizi yap
        result = asyncio.run(ai_integration.analyze_note(note.content))
        
        if result['success']:
            return jsonify({
                'success': True,
                'analysis': result['analysis']
            })
        else:
            return jsonify({'success': False, 'error': result['error']})
            
    except Exception as e:
        logger.error(f"AI analysis failed for note {note_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@notes_blueprint.route('/<note_id>/ai/suggest-tags', methods=['POST'])
def ai_suggest_tags(note_id):
    """AI ile etiket önerisi"""
    if not ai_integration:
        return jsonify({'success': False, 'error': 'AI entegrasyonu mevcut değil'}), 500
    
    try:
        note = notes_db.get_note(note_id)
        if not note:
            return jsonify({'success': False, 'error': 'Not bulunamadı'}), 404
        
        # Get existing tags
        existing_tags = [tag.name for tag in note.tags] if note.tags else []
        
        # Call with correct parameters
        suggested_tags = asyncio.run(ai_integration.suggest_tags(note.title, note.content, existing_tags))
        
        return jsonify({
            'success': True,
            'suggested_tags': suggested_tags,
            'current_tags': existing_tags
        })
            
    except Exception as e:
        logger.error(f"Tag suggestion failed for note {note_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@notes_blueprint.route('/<note_id>/ai/summarize', methods=['POST'])
def ai_summarize_note(note_id):
    """AI ile not özetleme"""
    if not ai_integration:
        return jsonify({'success': False, 'error': 'AI entegrasyonu mevcut değil'}), 500
    
    data = request.get_json() or {}
    length = data.get('length', 'medium')
    
    try:
        note = notes_db.get_note(note_id)
        if not note:
            return jsonify({'success': False, 'error': 'Not bulunamadı'}), 404
        
        # Call with correct parameters
        summary = asyncio.run(ai_integration.summarize_content(note.title, note.content, length))
        
        return jsonify({
            'success': True,
            'summary': summary,
            'length': length
        })
            
    except Exception as e:
        logger.error(f"Summarization failed for note {note_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@notes_blueprint.route('/<note_id>/ai/improve-writing', methods=['POST'])
def ai_improve_writing(note_id):
    """AI ile yazım iyileştirme"""
    if not ai_integration:
        return jsonify({'success': False, 'error': 'AI entegrasyonu mevcut değil'}), 500
    
    try:
        note = notes_db.get_note(note_id)
        if not note:
            return jsonify({'success': False, 'error': 'Not bulunamadı'}), 404
        
        # Call AI integration method (returns dict directly)
        result = asyncio.run(ai_integration.improve_writing(note.content))
        
        return jsonify({
            'success': True,
            'improvements': result
        })
            
    except Exception as e:
        logger.error(f"Writing improvement failed for note {note_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@notes_blueprint.route('/<note_id>/ai/related', methods=['GET'])
def ai_find_related_notes(note_id):
    """AI ile ilgili notları bul"""
    if not ai_integration:
        return jsonify({'success': False, 'error': 'AI entegrasyonu mevcut değil'}), 500
    
    try:
        note = notes_db.get_note(note_id)
        if not note:
            return jsonify({'success': False, 'error': 'Not bulunamadı'}), 404
        
        # Aynı workspace'teki diğer notları al - convert to dict format
        all_notes_objects = notes_db.get_notes(note.workspace_id, limit=100)
        all_notes = [n.to_dict() for n in all_notes_objects]
        
        # Call with correct parameters
        related_notes = asyncio.run(ai_integration.find_related_notes(note.title, note.content, all_notes))
        
        return jsonify({
            'success': True,
            'related_notes': related_notes
        })
            
    except Exception as e:
        logger.error(f"Related notes search failed for note {note_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# File Upload Endpoints
@notes_blueprint.route('/<note_id>/files', methods=['POST'])
def upload_file_to_note(note_id):
    """Note'a dosya yükle"""
    try:
        # Note'un varlığını kontrol et
        note = notes_db.get_note(note_id)
        if not note:
            return jsonify({'success': False, 'error': 'Not bulunamadı'}), 404
        
        # Dosya kontrolü
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'Dosya seçilmedi'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'Dosya adı boş'}), 400
        
        # Dosya adını güvenli hale getir
        filename = secure_filename(file.filename)
        file_data = file.read()
        
        # Dosyayı yükle
        result = file_manager.upload_file(file_data, filename, note_id)
        
        if result['success']:
            logger.info(f"File uploaded to note {note_id}: {filename}")
            return jsonify({
                'success': True,
                'file_id': result['file_id'],
                'file_info': result['file_info'],
                'message': 'Dosya başarıyla yüklendi'
            })
        else:
            return jsonify({'success': False, 'error': result['error']})
            
    except Exception as e:
        logger.error(f"File upload failed for note {note_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@notes_blueprint.route('/<note_id>/files', methods=['GET'])
def get_note_files(note_id):
    """Note'un dosyalarını listele"""
    try:
        # Note'un varlığını kontrol et
        note = notes_db.get_note(note_id)
        if not note:
            return jsonify({'success': False, 'error': 'Not bulunamadı'}), 404
        
        files = file_manager.get_note_files(note_id)
        
        return jsonify({
            'success': True,
            'files': files,
            'count': len(files)
        })
        
    except Exception as e:
        logger.error(f"File listing failed for note {note_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@notes_blueprint.route('/files/<file_id>', methods=['GET'])
def download_file(file_id):
    """Dosyayı indir"""
    try:
        file_info = file_manager.get_file_info(file_id)
        if not file_info:
            return jsonify({'success': False, 'error': 'Dosya bulunamadı'}), 404
        
        file_path = file_manager.get_file_path(file_id)
        if not file_path or not file_path.exists():
            return jsonify({'success': False, 'error': 'Dosya fiziksel olarak bulunamadı'}), 404
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=file_info['original_filename'],
            mimetype=file_info.get('mime_type')
        )
        
    except Exception as e:
        logger.error(f"File download failed for file {file_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@notes_blueprint.route('/files/<file_id>/thumbnail', methods=['GET'])
def get_file_thumbnail(file_id):
    """Dosya thumbnail'ını getir"""
    try:
        file_info = file_manager.get_file_info(file_id)
        if not file_info:
            return jsonify({'success': False, 'error': 'Dosya bulunamadı'}), 404
        
        thumbnail_path = file_manager.get_thumbnail_path(file_id)
        if not thumbnail_path or not thumbnail_path.exists():
            return jsonify({'success': False, 'error': 'Thumbnail bulunamadı'}), 404
        
        return send_file(thumbnail_path, mimetype='image/jpeg')
        
    except Exception as e:
        logger.error(f"Thumbnail fetch failed for file {file_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@notes_blueprint.route('/files/<file_id>/info', methods=['GET'])
def get_file_info(file_id):
    """Dosya bilgilerini getir"""
    try:
        file_info = file_manager.get_file_info(file_id)
        if not file_info:
            return jsonify({'success': False, 'error': 'Dosya bulunamadı'}), 404
        
        return jsonify({
            'success': True,
            'file_info': file_info
        })
        
    except Exception as e:
        logger.error(f"File info fetch failed for file {file_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@notes_blueprint.route('/files/<file_id>', methods=['DELETE'])
def delete_file(file_id):
    """Dosyayı sil"""
    note_id = request.args.get('note_id')
    
    try:
        result = file_manager.delete_file(file_id, note_id)
        
        if result['success']:
            logger.info(f"File deleted: {file_id}")
            return jsonify(result)
        else:
            return jsonify(result), 404
            
    except Exception as e:
        logger.error(f"File deletion failed for file {file_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Storage Statistics
@notes_blueprint.route('/storage/stats', methods=['GET'])
def get_storage_stats():
    """Storage istatistiklerini getir"""
    try:
        stats = file_manager.get_storage_stats()
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        logger.error(f"Storage stats fetch failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# Export Endpoints
@notes_blueprint.route('/<note_id>/export/<format_type>', methods=['GET'])
def export_single_note(note_id, format_type):
    """Tek bir notu export et"""
    note = notes_db.get_note(note_id)
    if not note:
        return jsonify({'success': False, 'error': 'Not bulunamadı'}), 404
    
    try:
        # Export manager ile export et
        filepath = export_manager.export_single_note(note.to_dict(), format_type)
        
        # Dosya adını al
        filename = os.path.basename(filepath)
        
        return jsonify({
            'success': True,
            'download_url': f'/api/notes/download/{filename}',
            'file_path': filepath,
            'format': format_type
        })
        
    except Exception as e:
        logger.error(f"Note export failed for note {note_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@notes_blueprint.route('/export/formats', methods=['GET'])
def get_export_formats():
    """Kullanılabilir export formatlarını getir"""
    try:
        formats = export_manager.available_formats
        return jsonify({
            'success': True,
            'formats': list(formats.keys()),
            'format_details': formats
        })
    except Exception as e:
        logger.error(f"Export formats fetch failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500 