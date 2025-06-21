"""
Test Script - AI Not Alma Sistemi
=================================

Not alma sisteminin temel fonksiyonlarını test eder.
"""

import os
import sys
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


def test_ai_agent():
    """AI Agent'ı test et"""
    print("\n\n🤖 AI Agent Testleri Başlıyor...")
    
    # Config ve adapter hazırla
    config = SecureConfigManager()
    
    # Gemini anahtarı yoksa test'i atla
    if not config.get_api_key('gemini'):
        print("⚠️ Gemini API anahtarı bulunamadı, AI testleri atlanıyor")
        return
    
    adapter = UniversalAIAdapter(config)
    adapter.add_adapter('gemini', api_key=config.get_api_key('gemini'))
    
    # Database ve agent oluştur
    db = NotesDatabase(db_path="data/test_notes.db")
    organizer = NoteOrganizerAgent(adapter, db)
    
    # Test notu analiz et
    print("\n1️⃣ Not analizi yapılıyor...")
    analysis = organizer.analyze_note(
        note_content="""
        # React Hooks Kullanımı
        
        React Hooks, fonksiyonel componentlerde state ve lifecycle kullanmamızı sağlar.
        
        ## useState Hook
        State yönetimi için kullanılır. Örnek:
        ```javascript
        const [count, setCount] = useState(0);
        ```
        
        ## useEffect Hook  
        Side effect'ler için kullanılır. Component mount, update ve unmount durumlarında çalışır.
        """,
        note_title="React Hooks Tutorial",
        existing_tags=["react", "javascript"]
    )
    
    if analysis["success"]:
        print("✅ Not analizi tamamlandı:")
        if analysis["analysis"]:
            print(f"   - Önerilen etiketler: {analysis['analysis'].get('suggested_tags', [])}")
            print(f"   - Kategori: {analysis['analysis'].get('category', 'N/A')}")
            print(f"   - Anahtar kelimeler: {analysis['analysis'].get('keywords', [])}")
    else:
        print(f"❌ Not analizi başarısız: {analysis.get('error', 'Unknown error')}")


def main():
    """Ana test fonksiyonu"""
    print("🧪 AI Not Alma Sistemi Test Script'i")
    print("=" * 50)
    
    try:
        # Veritabanı testleri
        workspace, notes = test_database_operations()
        
        # AI Agent testleri
        test_ai_agent()
        
        print("\n\n✅ Tüm testler tamamlandı!")
        print("\n💡 Not sistemi başarıyla çalışıyor.")
        print("🚀 Web arayüzünü başlatmak için: python run_production.py")
        
    except Exception as e:
        print(f"\n\n❌ Test hatası: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 