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
from ..logger import logger
import asyncio
import os
import tempfile

# Blueprint oluştur
notes_blueprint = Blueprint('notes', __name__, url_prefix='/api/notes')

# Database instance
notes_db = NotesDatabase()

# AI Integration (will be initialized from main app)
ai_integration = None

# Export Manager
export_manager = NotesExportManager()

def init_ai_integration(ai_adapter):
    """AI entegrasyonunu başlat"""
    global ai_integration
    ai_integration = NotesAIIntegration(ai_adapter)


@notes_blueprint.route('/workspaces', methods=['GET'])
def list_workspaces():
    """Kullanıcının workspace'lerini listele"""
    # TODO: Gerçek kullanıcı kimlik doğrulaması eklenecek
    user_id = request.args.get('user_id', 'default_user')
    
    workspaces = notes_db.list_workspaces(user_id)
    
    return jsonify({
        'success': True,
        'workspaces': [
            {
                'id': ws.id,
                'name': ws.name,
                'description': ws.description,
                'created_at': ws.created_at.isoformat() if ws.created_at else None
            }
            for ws in workspaces
        ]
    })


@notes_blueprint.route('/workspaces', methods=['POST'])
def create_workspace():
    """Yeni workspace oluştur"""
    data = request.get_json()
    
    # Validation
    if not data or 'name' not in data:
        return jsonify({'success': False, 'error': 'Workspace adı gerekli'}), 400
    
    # TODO: Gerçek kullanıcı kimlik doğrulaması eklenecek
    user_id = data.get('user_id', 'default_user')
    
    workspace = notes_db.create_workspace(
        name=data['name'],
        owner_id=user_id,
        description=data.get('description', '')
    )
    
    return jsonify({
        'success': True,
        'workspace': {
            'id': workspace.id,
            'name': workspace.name,
            'description': workspace.description
        }
    })


@notes_blueprint.route('/', methods=['GET'])
def list_notes():
    """Notları listele"""
    workspace_id = request.args.get('workspace_id')
    
    if not workspace_id:
        return jsonify({'success': False, 'error': 'Workspace ID gerekli'}), 400
    
    # Arama parametreleri
    query = request.args.get('q')
    tags = request.args.getlist('tags')
    parent_id = request.args.get('parent_id')
    created_by = request.args.get('created_by')
    include_archived = request.args.get('include_archived', 'false').lower() == 'true'
    limit = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))
    
    notes = notes_db.search_notes(
        workspace_id=workspace_id,
        query=query,
        tags=tags if tags else None,
        parent_id=parent_id,
        created_by=created_by,
        include_archived=include_archived,
        limit=limit,
        offset=offset
    )
    
    return jsonify({
        'success': True,
        'notes': [note.to_dict() for note in notes],
        'count': len(notes),
        'offset': offset,
        'limit': limit
    })


@notes_blueprint.route('/', methods=['POST'])
def create_note():
    """Yeni not oluştur"""
    data = request.get_json()
    
    # Validation
    required_fields = ['title', 'workspace_id']
    for field in required_fields:
        if not data or field not in data:
            return jsonify({'success': False, 'error': f'{field} gerekli'}), 400
    
    # TODO: Gerçek kullanıcı kimlik doğrulaması eklenecek
    created_by = data.get('created_by', 'default_user')
    
    note = notes_db.create_note(
        title=data['title'],
        workspace_id=data['workspace_id'],
        created_by=created_by,
        content=data.get('content', ''),
        parent_id=data.get('parent_id'),
        tags=data.get('tags', [])
    )
    
    return jsonify({
        'success': True,
        'note': note.to_dict()
    })


@notes_blueprint.route('/<note_id>', methods=['GET'])
def get_note(note_id):
    """Belirli bir notu getir"""
    increment_view = request.args.get('increment_view', 'true').lower() == 'true'
    
    note = notes_db.get_note(note_id, increment_view=increment_view)
    
    if not note:
        return jsonify({'success': False, 'error': 'Not bulunamadı'}), 404
    
    return jsonify({
        'success': True,
        'note': note.to_dict()
    })


@notes_blueprint.route('/<note_id>', methods=['PUT'])
def update_note(note_id):
    """Notu güncelle"""
    data = request.get_json()
    
    # TODO: Gerçek kullanıcı kimlik doğrulaması eklenecek
    edited_by = data.get('edited_by', 'default_user')
    
    note = notes_db.update_note(
        note_id=note_id,
        edited_by=edited_by,
        title=data.get('title'),
        content=data.get('content'),
        tags=data.get('tags'),
        ai_metadata=data.get('ai_metadata')
    )
    
    if not note:
        return jsonify({'success': False, 'error': 'Not bulunamadı'}), 404
    
    return jsonify({
        'success': True,
        'note': note.to_dict()
    })


@notes_blueprint.route('/<note_id>', methods=['DELETE'])
def delete_note(note_id):
    """Notu sil"""
    success = notes_db.delete_note(note_id)
    
    if not success:
        return jsonify({'success': False, 'error': 'Not bulunamadı'}), 404
    
    return jsonify({
        'success': True,
        'message': 'Not başarıyla silindi'
    })


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
    """Son güncellenen notları getir"""
    limit = int(request.args.get('limit', 10))
    
    notes = notes_db.get_recent_notes(workspace_id, limit=limit)
    
    return jsonify({
        'success': True,
        'notes': [note.to_dict() for note in notes]
    })


@notes_blueprint.route('/pinned/<workspace_id>', methods=['GET'])
def get_pinned_notes(workspace_id):
    """Sabitlenmiş notları getir"""
    notes = notes_db.get_pinned_notes(workspace_id)
    
    return jsonify({
        'success': True,
        'notes': [note.to_dict() for note in notes]
    })


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
    data = request.get_json()
    pinned = data.get('pinned', True)
    
    with notes_db.get_session() as session:
        note = session.query(Note).filter_by(id=note_id).first()
        
        if not note:
            return jsonify({'success': False, 'error': 'Not bulunamadı'}), 404
        
        note.is_pinned = pinned
        session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Not {"sabitlendi" if pinned else "sabitlemesi kaldırıldı"}'
    })


# AI Endpoints
@notes_blueprint.route('/<note_id>/ai/analyze', methods=['POST'])
def analyze_note_ai(note_id):
    """AI ile not analizi yap"""
    if not ai_integration:
        return jsonify({'success': False, 'error': 'AI entegrasyonu mevcut değil'}), 503
    
    note = notes_db.get_note(note_id)
    if not note:
        return jsonify({'success': False, 'error': 'Not bulunamadı'}), 404
    
    def run_analysis():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(
            ai_integration.analyze_note(note.title, note.content)
        )
    
    try:
        analysis = run_analysis()
        
        # AI metadata'yı not'a kaydet
        notes_db.update_note(
            note_id=note_id,
            edited_by='ai_system',
            ai_metadata={'analysis': analysis}
        )
        
        return jsonify({
            'success': True,
            'analysis': analysis
        })
        
    except Exception as e:
        logger.error(f"AI analysis failed for note {note_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@notes_blueprint.route('/<note_id>/ai/suggest-tags', methods=['POST'])
def suggest_tags_ai(note_id):
    """AI ile etiket önerileri al"""
    if not ai_integration:
        return jsonify({'success': False, 'error': 'AI entegrasyonu mevcut değil'}), 503
    
    note = notes_db.get_note(note_id)
    if not note:
        return jsonify({'success': False, 'error': 'Not bulunamadı'}), 404
    
    def run_suggestion():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(
            ai_integration.suggest_tags(note.title, note.content, note.tags)
        )
    
    try:
        suggested_tags = run_suggestion()
        
        return jsonify({
            'success': True,
            'suggested_tags': suggested_tags,
            'current_tags': [tag.name for tag in note.tags] if note.tags else []
        })
        
    except Exception as e:
        logger.error(f"Tag suggestion failed for note {note_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@notes_blueprint.route('/<note_id>/ai/summarize', methods=['POST'])
def summarize_note_ai(note_id):
    """AI ile not özetleme"""
    if not ai_integration:
        return jsonify({'success': False, 'error': 'AI entegrasyonu mevcut değil'}), 503
    
    data = request.get_json() or {}
    target_length = data.get('length', 'short')
    
    note = notes_db.get_note(note_id)
    if not note:
        return jsonify({'success': False, 'error': 'Not bulunamadı'}), 404
    
    def run_summarization():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(
            ai_integration.summarize_content(note.title, note.content, target_length)
        )
    
    try:
        summary = run_summarization()
        
        return jsonify({
            'success': True,
            'summary': summary,
            'length': target_length
        })
        
    except Exception as e:
        logger.error(f"Summarization failed for note {note_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@notes_blueprint.route('/<note_id>/ai/improve-writing', methods=['POST'])
def improve_writing_ai(note_id):
    """AI ile yazım iyileştirme"""
    if not ai_integration:
        return jsonify({'success': False, 'error': 'AI entegrasyonu mevcut değil'}), 503
    
    note = notes_db.get_note(note_id)
    if not note:
        return jsonify({'success': False, 'error': 'Not bulunamadı'}), 404
    
    def run_improvement():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(
            ai_integration.improve_writing(note.content)
        )
    
    try:
        improvements = run_improvement()
        
        return jsonify({
            'success': True,
            'improvements': improvements
        })
        
    except Exception as e:
        logger.error(f"Writing improvement failed for note {note_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@notes_blueprint.route('/<note_id>/ai/related', methods=['GET'])
def find_related_notes_ai(note_id):
    """AI ile ilgili notları bul"""
    if not ai_integration:
        return jsonify({'success': False, 'error': 'AI entegrasyonu mevcut değil'}), 503
    
    note = notes_db.get_note(note_id)
    if not note:
        return jsonify({'success': False, 'error': 'Not bulunamadı'}), 404
    
    # Workspace'deki diğer notları al
    all_notes = notes_db.search_notes(
        workspace_id=note.workspace_id,
        limit=50,
        include_archived=False
    )
    
    # Mevcut notu hariç tut
    other_notes = [n.to_dict() for n in all_notes if n.id != note_id]
    
    def run_related_search():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(
            ai_integration.find_related_notes(note.title, note.content, other_notes)
        )
    
    try:
        related_notes = run_related_search()
        
        return jsonify({
            'success': True,
            'related_notes': related_notes
        })
        
    except Exception as e:
        logger.error(f"Related notes search failed for note {note_id}: {e}")
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
            'message': f'Not {format_type} formatında export edildi',
            'filepath': filepath,
            'filename': filename,
            'download_url': f'/api/notes/download/{filename}'
        })
        
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Export failed for note {note_id}: {e}")
        return jsonify({'success': False, 'error': f'Export hatası: {str(e)}'}), 500


@notes_blueprint.route('/workspace/<workspace_id>/export', methods=['POST'])
def export_workspace_notes(workspace_id):
    """Workspace'deki notları export et"""
    data = request.get_json() or {}
    format_type = data.get('format', 'markdown')
    export_type = data.get('type', 'multiple')  # 'multiple' or 'summary'
    
    # Workspace'deki notları al
    notes = notes_db.search_notes(
        workspace_id=workspace_id,
        limit=1000,  # Maksimum 1000 not
        include_archived=False
    )
    
    if not notes:
        return jsonify({'success': False, 'error': 'Export edilecek not bulunamadı'}), 404
    
    try:
        notes_data = [note.to_dict() for note in notes]
        
        if export_type == 'summary':
            # Workspace özeti oluştur
            workspace = notes_db.get_workspace(workspace_id)
            workspace_name = workspace.name if workspace else f"Workspace_{workspace_id}"
            
            filepath = export_manager.export_workspace_summary(workspace_name, notes_data)
            filename = os.path.basename(filepath)
            
            return jsonify({
                'success': True,
                'message': f'Workspace özeti oluşturuldu',
                'filepath': filepath,
                'filename': filename,
                'download_url': f'/api/notes/download/{filename}',
                'notes_count': len(notes_data)
            })
        else:
            # Tüm notları export et
            exported_files = export_manager.export_multiple_notes(notes_data, format_type)
            
            return jsonify({
                'success': True,
                'message': f'{len(exported_files)} not {format_type} formatında export edildi',
                'exported_files': [os.path.basename(f) for f in exported_files],
                'download_urls': [f'/api/notes/download/{os.path.basename(f)}' for f in exported_files],
                'notes_count': len(exported_files)
            })
            
    except Exception as e:
        logger.error(f"Workspace export failed: {e}")
        return jsonify({'success': False, 'error': f'Export hatası: {str(e)}'}), 500


@notes_blueprint.route('/export/formats', methods=['GET'])
def get_export_formats():
    """Kullanılabilir export formatlarını döndür"""
    formats = export_manager.get_available_formats()
    
    format_descriptions = {
        'markdown': 'Markdown (.md) - GitHub flavored markdown format',
        'html': 'HTML (.html) - Web sayfası formatı',
        'json': 'JSON (.json) - Yapılandırılmış veri formatı',
        'txt': 'Plain Text (.txt) - Düz metin formatı'
    }
    
    available_formats = []
    for format_name, available in formats.items():
        if available:
            available_formats.append({
                'name': format_name,
                'description': format_descriptions.get(format_name, f'{format_name} format'),
                'extension': f'.{format_name}'
            })
    
    return jsonify({
        'success': True,
        'formats': available_formats,
        'count': len(available_formats)
    })


@notes_blueprint.route('/download/<filename>', methods=['GET'])
def download_exported_file(filename):
    """Export edilmiş dosyayı indir"""
    try:
        filepath = os.path.join(export_manager.output_dir, filename)
        
        if not os.path.exists(filepath):
            return jsonify({'success': False, 'error': 'Dosya bulunamadı'}), 404
        
        # Güvenlik kontrolü - sadece export dizinindeki dosyalar
        if not os.path.commonpath([filepath, export_manager.output_dir]) == export_manager.output_dir:
            return jsonify({'success': False, 'error': 'Geçersiz dosya yolu'}), 403
        
        return send_file(
            filepath,
            as_attachment=True,
            download_name=filename,
            mimetype='application/octet-stream'
        )
        
    except Exception as e:
        logger.error(f"File download failed: {e}")
        return jsonify({'success': False, 'error': f'İndirme hatası: {str(e)}'}), 500 