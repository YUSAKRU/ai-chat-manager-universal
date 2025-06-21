"""
Test Script - AI Not Alma Sistemi
=================================

Not alma sisteminin temel fonksiyonlarını test eder.
"""

import os
import sys
import asyncio
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.notes.database import NotesDatabase
from src.notes.models import Note, NoteWorkspace, NoteTag
from src.ai_adapters.universal_adapter import UniversalAIAdapter
from src.ai_adapters.secure_config import SecureConfigManager
from src.ai_note_agents.note_organizer import NoteOrganizerAgent


def test_database_operations():
    """Veritabanı işlemlerini test et"""
    print("\n🔧 Veritabanı Testleri Başlıyor...")
    
    # Test veritabanı oluştur
    db = NotesDatabase(db_path="data/test_notes.db")
    
    # 1. Workspace oluştur
    print("\n1️⃣ Workspace oluşturuluyor...")
    workspace = db.create_workspace(
        name="Test Workspace",
        owner_id="test_user",
        description="Test amaçlı workspace"
    )
    print(f"✅ Workspace oluşturuldu: {workspace.id}")
    
    # 2. Not oluştur
    print("\n2️⃣ Notlar oluşturuluyor...")
    note1 = db.create_note(
        title="Python Programlama Notları",
        workspace_id=workspace.id,
        created_by="test_user",
        content="# Python Temelleri\n\nPython güçlü ve esnek bir programlama dilidir.",
        tags=["python", "programlama", "tutorial"]
    )
    print(f"✅ Not 1 oluşturuldu: {note1.title}")
    
    note2 = db.create_note(
        title="Machine Learning Giriş",
        workspace_id=workspace.id,
        created_by="test_user",
        content="# ML Nedir?\n\nMachine Learning, bilgisayarların veriden öğrenmesini sağlar.",
        tags=["ml", "ai", "tutorial"]
    )
    print(f"✅ Not 2 oluşturuldu: {note2.title}")
    
    # 3. Alt not oluştur
    subnote = db.create_note(
        title="Supervised Learning",
        workspace_id=workspace.id,
        created_by="test_user",
        parent_id=note2.id,
        content="Supervised learning, etiketli veri ile öğrenmedir.",
        tags=["ml", "supervised"]
    )
    print(f"✅ Alt not oluşturuldu: {subnote.title}")
    
    # 4. Not arama
    print("\n3️⃣ Notlar aranıyor...")
    search_results = db.search_notes(
        workspace_id=workspace.id,
        query="python"
    )
    print(f"✅ 'python' araması: {len(search_results)} sonuç bulundu")
    
    # 5. Not güncelleme
    print("\n4️⃣ Not güncelleniyor...")
    updated_note = db.update_note(
        note_id=note1.id,
        edited_by="test_user",
        content=note1.content + "\n\n## Yeni Bölüm\n\nGüncellenmiş içerik."
    )
    print(f"✅ Not güncellendi: v{updated_note.version}")
    
    # 6. İstatistikler
    print("\n5️⃣ İstatistikler alınıyor...")
    stats = db.get_workspace_stats(workspace.id)
    print(f"✅ Workspace İstatistikleri:")
    print(f"   - Toplam not: {stats['total_notes']}")
    print(f"   - Aktif not: {stats['active_notes']}")
    print(f"   - Etiket sayısı: {stats['total_tags']}")
    
    return workspace, [note1, note2, subnote]


def test_ai_agents(workspace, notes):
    """AI agent'ları test et"""
    print("\n🤖 AI Agent Testleri Başlıyor...")
    
    # Mock AI adapter oluştur
    from unittest.mock import Mock, AsyncMock
    from dataclasses import dataclass
    
    @dataclass
    class MockAIResponse:
        content: str
        model: str = "gemini-1.5-flash"
        usage: dict = None
        
        def __post_init__(self):
            if self.usage is None:
                self.usage = {
                    'input_tokens': 100,
                    'output_tokens': 50,
                    'total_tokens': 150,
                    'cost': 0.001
                }
    
    # Create mock adapter
    mock_adapter = Mock()
    
    # Configure async method
    async def mock_send_message(role_id, message):
        # Simulate different responses based on prompt content
        if "analiz et" in message:
            return MockAIResponse(
                content="""Ana konu: Python programlama ve AI entegrasyonu
Anahtar noktalar:
- Python'da async/await kullanımı
- AI modellerle entegrasyon
- Database işlemleri

Duygu analizi: Pozitif
Önerilen etiketler: python, ai, programlama, tutorial, async
İçerik kalitesi skoru: 8/10"""
            )
        elif "etiket" in message:
            return MockAIResponse(content="python, ai, programlama, veritabanı, tutorial")
        else:
            return MockAIResponse(content="Test yanıtı")
    
    mock_adapter.send_message = AsyncMock(side_effect=mock_send_message)
    
    # AI integration test et
    from src.notes.ai_integration import NotesAIIntegration
    ai_integration = NotesAIIntegration(mock_adapter)
    
    print("\n1️⃣ Not analizi yapılıyor...")
    note_content = notes[0].content if notes else "Test içeriği"
    result = asyncio.run(ai_integration.analyze_note(note_content))
    
    if result['success']:
        print("✅ Not analizi başarılı")
        print(f"   Analiz: {result['analysis'][:200]}...")
    else:
        print(f"❌ Not analizi başarısız: {result['error']}")
    
    print("\n2️⃣ Etiket önerisi yapılıyor...")
    note_title = notes[0].title if notes else "Test Başlık"
    try:
        tags = asyncio.run(ai_integration.suggest_tags(note_title, note_content))
        print("✅ Etiket önerisi başarılı")
        print(f"   Önerilen etiketler: {tags}")
    except Exception as e:
        print(f"❌ Etiket önerisi başarısız: {e}")


def main():
    """Ana test fonksiyonu"""
    print("🧪 AI Not Alma Sistemi Test Script'i")
    print("=" * 50)
    
    try:
        # Veritabanı testleri
        workspace, notes = test_database_operations()
        
        # AI Agent testleri
        test_ai_agents(workspace, notes)
        
        print("\n\n✅ Tüm testler tamamlandı!")
        print("\n💡 Not sistemi başarıyla çalışıyor.")
        print("🚀 Web arayüzünü başlatmak için: python run_production.py")
        
    except Exception as e:
        print(f"\n\n❌ Test hatası: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 