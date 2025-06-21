/**
 * AI-Powered Notes App
 * ====================
 * 
 * Not alma uygulaması için JavaScript modülü
 */

class NotesApp {
    constructor() {
        this.currentWorkspace = null;
        this.currentNote = null;
        this.notes = [];
        this.autoSaveTimeout = null;
        this.apiBaseUrl = '/api/notes';
        this.exportFormats = [];
        
        this.init();
    }
    
    async init() {
        console.log('🚀 Notes App başlatılıyor...');
        
        // Event listeners
        this.setupEventListeners();
        
        // İlk workspace ve notları yükle
        await this.loadWorkspaces();
        await this.loadNotes();
        
        // Export formatlarını yükle
        await this.loadExportFormats();
        
        console.log('✅ Notes App hazır!');
    }
    
    setupEventListeners() {
        // Arama
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => this.handleSearch(e.target.value));
        }
        
        // Not başlığı değişikliği
        const noteTitle = document.getElementById('noteTitle');
        if (noteTitle) {
            noteTitle.addEventListener('input', () => this.handleTitleChange());
        }
        
        // Editor değişikliği
        const noteEditor = document.getElementById('noteEditor');
        if (noteEditor) {
            noteEditor.addEventListener('input', () => this.handleContentChange());
            noteEditor.addEventListener('paste', (e) => this.handlePaste(e));
        }
        
        // Klavye kısayolları
        document.addEventListener('keydown', (e) => this.handleKeyboardShortcuts(e));
        
        // Otomatik kaydetme
        this.setupAutoSave();
    }
    
    // Workspace İşlemleri
    async loadWorkspaces() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/workspaces?user_id=default_user`);
            const data = await response.json();
            
            if (data.success && data.workspaces.length > 0) {
                this.currentWorkspace = data.workspaces[0].id;
                console.log(`✅ Workspace yüklendi: ${this.currentWorkspace}`);
            } else {
                // Varsayılan workspace oluştur
                await this.createDefaultWorkspace();
            }
        } catch (error) {
            console.error('❌ Workspace yükleme hatası:', error);
            this.showStatus('Workspace yüklenemedi', 'error');
        }
    }
    
    async createDefaultWorkspace() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/workspaces`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name: 'Benim Notlarım',
                    description: 'Varsayılan not çalışma alanı',
                    user_id: 'default_user'
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.currentWorkspace = data.workspace.id;
                console.log('✅ Varsayılan workspace oluşturuldu');
            }
        } catch (error) {
            console.error('❌ Workspace oluşturma hatası:', error);
        }
    }
    
    // Not İşlemleri
    async loadNotes() {
        if (!this.currentWorkspace) return;
        
        try {
            // Skeleton loading göster
            this.showSkeletonLoading('pinnedNotes', 2);
            this.showSkeletonLoading('recentNotes', 3);
            this.showSkeletonLoading('allNotes', 5);
            
            // Paralel olarak tüm API çağrılarını yap
            const [pinnedResponse, recentResponse, allResponse] = await Promise.all([
                fetch(`${this.apiBaseUrl}/pinned/${this.currentWorkspace}`),
                fetch(`${this.apiBaseUrl}/recent/${this.currentWorkspace}?limit=10`),
                fetch(`${this.apiBaseUrl}/?workspace_id=${this.currentWorkspace}&limit=50`)
            ]);
            
            const [pinnedData, recentData, allData] = await Promise.all([
                pinnedResponse.json(),
                recentResponse.json(),
                allResponse.json()
            ]);
            
            // Render işlemleri
            if (pinnedData.success) {
                this.renderNotes(pinnedData.notes, 'pinnedNotes');
            } else {
                this.renderEmptyState('pinnedNotes', 'Sabitlenmiş not yok', 'Önemli notlarınızı sabitleyebilirsiniz');
            }
            
            if (recentData.success) {
                this.renderNotes(recentData.notes, 'recentNotes');
            } else {
                this.renderEmptyState('recentNotes', 'Son not yok', 'Henüz not oluşturmadınız');
            }
            
            if (allData.success) {
                this.notes = allData.notes;
                this.renderNotes(allData.notes, 'allNotes');
                
                // İlk notu aç
                if (this.notes.length > 0 && !this.currentNote) {
                    this.openNote(this.notes[0]);
                } else if (this.notes.length === 0) {
                    this.renderEmptyState('allNotes', 'Henüz not yok', 'İlk notunuzu oluşturarak başlayın', 'createNewNote()');
                }
            }
            
            this.showStatus('Notlar yüklendi', 'success', `${this.notes.length} not bulundu`);
            
        } catch (error) {
            console.error('❌ Notlar yükleme hatası:', error);
            this.showStatus('Notlar yüklenemedi', 'error', 'Bağlantı sorunu olabilir');
            
            // Error states göster
            this.renderErrorState('pinnedNotes', 'Yükleme hatası');
            this.renderErrorState('recentNotes', 'Yükleme hatası');
            this.renderErrorState('allNotes', 'Yükleme hatası');
        }
    }
    
    renderNotes(notes, containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        if (notes.length === 0) {
            container.innerHTML = '<div class="text-muted text-center p-3">Henüz not yok</div>';
            return;
        }
        
        container.innerHTML = notes.map(note => this.createNoteHTML(note)).join('');
    }
    
    createNoteHTML(note) {
        const truncatedContent = this.stripHTML(note.content).substring(0, 100);
        const formattedDate = this.formatDate(note.updated_at);
        const isActive = this.currentNote && this.currentNote.id === note.id ? 'active' : '';
        
        const tagsHTML = note.tags ? note.tags.map(tag => 
            `<span class="note-tag">${tag}</span>`
        ).join('') : '';
        
        return `
            <div class="note-item ${isActive}" onclick="notesApp.openNote(${JSON.stringify(note).replace(/"/g, '&quot;')})">
                <div class="note-title">${note.title || 'Başlıksız'}</div>
                <div class="note-preview">${truncatedContent}</div>
                <div class="note-meta">
                    <div class="note-tags">${tagsHTML}</div>
                    <div class="note-date">${formattedDate}</div>
                </div>
            </div>
        `;
    }
    
    async openNote(note) {
        try {
            this.currentNote = note;
            
            // UI'ı güncelle
            this.updateActiveNote();
            
            // Not detaylarını yükle
            const response = await fetch(`${this.apiBaseUrl}/${note.id}?increment_view=true`);
            const data = await response.json();
            
            if (data.success) {
                const fullNote = data.note;
                
                // Editor'ı güncelle
                document.getElementById('noteTitle').value = fullNote.title || '';
                document.getElementById('noteEditor').innerHTML = fullNote.content || '<p>Notunuzu yazmaya başlayın...</p>';
                
                this.currentNote = fullNote;
                console.log(`📖 Not açıldı: ${fullNote.title}`);
            }
            
        } catch (error) {
            console.error('❌ Not açma hatası:', error);
            this.showStatus('Not açılamadı', 'error');
        }
    }
    
    updateActiveNote() {
        // Önceki aktif not'u kaldır
        document.querySelectorAll('.note-item').forEach(item => {
            item.classList.remove('active');
        });
        
        // Yeni aktif not'u işaretle
        if (this.currentNote) {
            const activeNoteElement = document.querySelector(`[onclick*="${this.currentNote.id}"]`);
            if (activeNoteElement) {
                activeNoteElement.classList.add('active');
            }
        }
    }
    
    async saveNote() {
        if (!this.currentNote) return;
        
        try {
            this.showSaveIndicator('saving');
            
            const title = document.getElementById('noteTitle').value;
            const content = document.getElementById('noteEditor').innerHTML;
            
            const response = await fetch(`${this.apiBaseUrl}/${this.currentNote.id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    title: title,
                    content: content,
                    edited_by: 'default_user'
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.currentNote = data.note;
                this.showSaveIndicator('saved');
                
                // Listeyi session reload yapmadan güncelle
                this.updateNoteInLists(data.note);
                
                // Word count ve son düzenleme bilgisi
                const wordCount = this.getWordCount(content);
                this.showStatus('Kaydedildi', 'success', `${wordCount} kelime, ${new Date().toLocaleTimeString('tr-TR', {hour: '2-digit', minute: '2-digit'})}`);
            } else {
                this.showSaveIndicator('error', 'Kaydetme başarısız');
                this.showStatus('Kaydetme başarısız', 'error', data.error);
            }
            
        } catch (error) {
            console.error('❌ Kaydetme hatası:', error);
            this.showSaveIndicator('error', 'Bağlantı hatası');
            this.showStatus('Kaydetme başarısız', 'error', 'Bağlantı sorunu');
        }
    }
    
    // UI İşlemleri
    async createNewNote() {
        try {
            if (!this.currentWorkspace) {
                await this.loadWorkspaces();
            }
            
            const response = await fetch(`${this.apiBaseUrl}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    title: 'Yeni Not',
                    content: '<p>Notunuzu yazmaya başlayın...</p>',
                    workspace_id: this.currentWorkspace,
                    created_by: 'default_user'
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                await this.loadNotes();
                this.openNote(data.note);
                
                // Başlığa odaklan
                const titleInput = document.getElementById('noteTitle');
                titleInput.select();
                
                this.showStatus('Yeni not oluşturuldu', 'success');
            }
            
        } catch (error) {
            console.error('❌ Not oluşturma hatası:', error);
            this.showStatus('Not oluşturulamadı', 'error');
        }
    }
    
    // Arama
    async handleSearch(query) {
        if (!query.trim()) {
            this.showSearchLoading(false);
            await this.loadNotes();
            return;
        }
        
        try {
            this.showSearchLoading(true);
            
            const response = await fetch(`${this.apiBaseUrl}/?workspace_id=${this.currentWorkspace}&q=${encodeURIComponent(query)}`);
            const data = await response.json();
            
            if (data.success) {
                this.renderNotes(data.notes, 'allNotes');
                
                // Arama sonuçları bilgisi
                const resultCount = data.notes.length;
                if (resultCount > 0) {
                    this.showStatus('Arama tamamlandı', 'success', `"${query}" için ${resultCount} sonuç bulundu`);
                    
                    // Diğer bölümleri temizle  
                    this.renderEmptyState('pinnedNotes', 'Arama modunda', 'Sabitlenmiş notlar gizlendi');
                    this.renderEmptyState('recentNotes', 'Arama modunda', 'Son notlar gizlendi');
                } else {
                    this.renderEmptyState('allNotes', 'Sonuç bulunamadı', `"${query}" ile eşleşen not bulunamadı`, 'clearSearch()');
                    this.showStatus('Sonuç bulunamadı', 'warning', `"${query}" için herhangi bir sonuç bulunamadı`);
                }
            } else {
                this.showStatus('Arama hatası', 'error', data.error);
            }
            
        } catch (error) {
            console.error('❌ Arama hatası:', error);
            this.showStatus('Arama hatası', 'error', 'Bağlantı sorunu');
        } finally {
            this.showSearchLoading(false);
        }
    }
    
    // Event Handlers
    handleTitleChange() {
        this.scheduleAutoSave();
    }
    
    handleContentChange() {
        this.scheduleAutoSave();
    }
    
    handlePaste(e) {
        // Paste işleminden sonra otomatik kaydet
        setTimeout(() => {
            this.scheduleAutoSave();
        }, 100);
    }
    
    handleKeyboardShortcuts(e) {
        // Ctrl+S - Kaydet
        if (e.ctrlKey && e.key === 's') {
            e.preventDefault();
            this.saveNote();
        }
        
        // Ctrl+N - Yeni not
        if (e.ctrlKey && e.key === 'n') {
            e.preventDefault();
            this.createNewNote();
        }
        
        // Ctrl+F - Arama
        if (e.ctrlKey && e.key === 'f') {
            e.preventDefault();
            document.getElementById('searchInput').focus();
        }
    }
    
    // Otomatik Kaydetme
    setupAutoSave() {
        // Her 30 saniyede otomatik kaydet
        setInterval(() => {
            if (this.currentNote) {
                this.saveNote();
            }
        }, 30000);
    }
    
    scheduleAutoSave() {
        // Kullanıcı yazmayı bıraktıktan 2 saniye sonra kaydet
        clearTimeout(this.autoSaveTimeout);
        this.autoSaveTimeout = setTimeout(() => {
            if (this.currentNote) {
                this.saveNote();
            }
        }, 2000);
    }
    
    // Advanced UI Helper'ları
    showLoading(show, text = 'Yükleniyor...', subtext = '') {
        const overlay = document.getElementById('loadingOverlay');
        if (!overlay) return;
        
        if (show) {
            const loadingText = overlay.querySelector('.loading-text');
            const loadingSubtext = overlay.querySelector('.loading-subtext');
            
            if (loadingText) loadingText.textContent = text;
            if (loadingSubtext) loadingSubtext.textContent = subtext;
            
            overlay.classList.add('show');
        } else {
            overlay.classList.remove('show');
        }
    }
    
    showSkeletonLoading(containerId, count = 3) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        const skeletons = Array.from({length: count}, () => `
            <div class="skeleton-note skeleton">
                <div class="skeleton-title skeleton"></div>
                <div class="skeleton-content skeleton"></div>
                <div class="skeleton-meta skeleton"></div>
            </div>
        `).join('');
        
        container.innerHTML = skeletons;
    }
    
    showStatus(message, type = 'info', details = '', duration = 4000) {
        const container = document.getElementById('statusContainer') || this.createStatusContainer();
        
        const statusId = 'status-' + Date.now();
        const statusElement = document.createElement('div');
        statusElement.className = `status-message ${type}`;
        statusElement.id = statusId;
        
        // Icon mapping
        const icons = {
            success: '✅',
            error: '❌', 
            warning: '⚠️',
            info: 'ℹ️'
        };
        
        statusElement.innerHTML = `
            <div class="status-header">
                <span class="status-icon">${icons[type] || 'ℹ️'}</span>
                ${message}
            </div>
            ${details ? `<div class="status-body">${details}</div>` : ''}
        `;
        
        container.appendChild(statusElement);
        
        // Show animation
        setTimeout(() => statusElement.classList.add('show'), 10);
        
        // Auto remove
        setTimeout(() => {
            statusElement.classList.remove('show');
            setTimeout(() => {
                if (statusElement.parentNode) {
                    statusElement.parentNode.removeChild(statusElement);
                }
            }, 300);
        }, duration);
        
        return statusId;
    }
    
    createStatusContainer() {
        const container = document.createElement('div');
        container.id = 'statusContainer';
        container.className = 'status-container';
        document.body.appendChild(container);
        return container;
    }
    
    showSaveIndicator(state = 'saving', message = '') {
        const indicator = document.getElementById('saveIndicator') || this.createSaveIndicator();
        
        const states = {
            saving: { text: message || 'Kaydediliyor...', icon: '<div class="save-spinner"></div>' },
            saved: { text: message || 'Kaydedildi', icon: '✅' },
            error: { text: message || 'Kaydetme hatası', icon: '❌' }
        };
        
        const currentState = states[state] || states.saving;
        indicator.className = `save-indicator ${state} show`;
        indicator.innerHTML = `${currentState.icon} ${currentState.text}`;
        
        // Auto hide for saved/error states
        if (state !== 'saving') {
            setTimeout(() => {
                indicator.classList.remove('show');
            }, 2000);
        }
    }
    
    createSaveIndicator() {
        const indicator = document.createElement('div');
        indicator.id = 'saveIndicator';
        indicator.className = 'save-indicator';
        document.body.appendChild(indicator);
        return indicator;
    }
    
    showAIProgress(operation, progress = 0) {
        const progressEl = document.getElementById('aiProgress') || this.createAIProgress();
        
        const operations = {
            analyze: 'AI Analiz ediyor...',
            summarize: 'Özet oluşturuyor...',
            suggest_tags: 'Etiket öneriyor...',
            improve_writing: 'Yazımı iyileştiriyor...',
            find_related: 'İlgili notlar buluyor...'
        };
        
        progressEl.querySelector('.ai-progress-text').textContent = operations[operation] || operation;
        progressEl.querySelector('.ai-progress-fill').style.width = `${progress}%`;
        progressEl.classList.add('show');
        
        return progressEl;
    }
    
    hideAIProgress() {
        const progressEl = document.getElementById('aiProgress');
        if (progressEl) {
            progressEl.classList.remove('show');
        }
    }
    
    createAIProgress() {
        const progress = document.createElement('div');
        progress.id = 'aiProgress';
        progress.className = 'ai-progress';
        progress.innerHTML = `
            <div class="ai-progress-header">
                <span>🤖</span>
                AI Çalışıyor
            </div>
            <div class="ai-progress-bar">
                <div class="ai-progress-fill" style="width: 0%"></div>
            </div>
            <div class="ai-progress-text">İşlem başlatılıyor...</div>
        `;
        document.body.appendChild(progress);
        return progress;
    }
    
    showSearchLoading(show) {
        const searchBox = document.querySelector('.search-box');
        let loadingEl = searchBox.querySelector('.search-loading');
        
        if (show && !loadingEl) {
            loadingEl = document.createElement('div');
            loadingEl.className = 'search-loading';
            searchBox.appendChild(loadingEl);
        }
        
        if (loadingEl) {
            loadingEl.classList.toggle('show', show);
        }
    }
    
    // Utility Functions
    stripHTML(html) {
        const div = document.createElement('div');
        div.innerHTML = html;
        return div.textContent || div.innerText || '';
    }
    
    formatDate(dateString) {
        if (!dateString) return '';
        
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);
        
        if (diffMins < 1) return 'Şimdi';
        if (diffMins < 60) return `${diffMins} dk önce`;
        if (diffHours < 24) return `${diffHours} sa önce`;
        if (diffDays < 7) return `${diffDays} gün önce`;
        
        return date.toLocaleDateString('tr-TR');
    }
    
    getWordCount(content) {
        const text = this.stripHTML(content);
        return text.trim() ? text.trim().split(/\s+/).length : 0;
    }
    
    updateNoteInLists(note) {
        // Mevcut listelerdeki notu güncelle
        const noteElements = document.querySelectorAll(`[onclick*="${note.id}"]`);
        noteElements.forEach(element => {
            const titleEl = element.querySelector('.note-title');
            if (titleEl) titleEl.textContent = note.title || 'Başlıksız';
            
            const previewEl = element.querySelector('.note-preview');
            if (previewEl) {
                const truncatedContent = this.stripHTML(note.content).substring(0, 100);
                previewEl.textContent = truncatedContent;
            }
            
            const dateEl = element.querySelector('.note-date');
            if (dateEl) dateEl.textContent = this.formatDate(note.updated_at);
        });
    }
    
    renderEmptyState(containerId, title, description, actionFunction = null) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        const actionButton = actionFunction ? 
            `<button class="empty-action" onclick="${actionFunction}">
                <i class="fas fa-plus"></i>
                ${actionFunction === 'createNewNote()' ? 'Yeni Not Oluştur' : 'Temizle'}
            </button>` : '';
        
        container.innerHTML = `
            <div class="empty-state fade-in">
                <div class="empty-icon">
                    <i class="fas fa-file-alt"></i>
                </div>
                <div class="empty-title">${title}</div>
                <div class="empty-description">${description}</div>
                ${actionButton}
            </div>
        `;
    }
    
    renderErrorState(containerId, message) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        container.innerHTML = `
            <div class="empty-state fade-in">
                <div class="empty-icon">
                    <i class="fas fa-exclamation-triangle" style="color: #e74c3c;"></i>
                </div>
                <div class="empty-title">Hata</div>
                <div class="empty-description">${message}</div>
                <button class="empty-action" onclick="notesApp.loadNotes()">
                    <i class="fas fa-redo"></i>
                    Tekrar Dene
                </button>
            </div>
        `;
    }
    
    clearSearch() {
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            searchInput.value = '';
            this.loadNotes();
        }
    }
    
    // Export formatlarını yükle
    async loadExportFormats() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/export/formats`);
            const data = await response.json();
            
            if (data.success) {
                this.exportFormats = data.formats;
                console.log('✅ Export formatları yüklendi:', this.exportFormats);
            }
        } catch (error) {
            console.error('❌ Export formatları yüklenemedi:', error);
        }
    }
}

// AI İşlemleri
async function aiAnalyzeNote() {
    if (!notesApp.currentNote) {
        notesApp.showStatus('Önce bir not seçin', 'warning');
        return;
    }
    
    try {
        // AI progress göster
        notesApp.showAIProgress('analyze', 10);
        
        const response = await fetch(`${notesApp.apiBaseUrl}/${notesApp.currentNote.id}/ai/analyze`, {
            method: 'POST'
        });
        
        // Progress güncelle
        notesApp.showAIProgress('analyze', 50);
        
        const data = await response.json();
        
        // Progress tamamla
        notesApp.showAIProgress('analyze', 100);
        
        if (data.success) {
            const analysis = data.analysis;
            notesApp.showStatus('Analiz tamamlandı', 'success', `Kategori: ${analysis.category} | Duygu: ${analysis.sentiment}`);
            
            // Analysis sonuçlarını göster
            console.log('📊 AI Analiz Sonuçları:', analysis);
            showAnalysisModal(analysis);
        } else {
            notesApp.showStatus('Analiz başarısız', 'error', data.error);
        }
    } catch (error) {
        console.error('AI analiz hatası:', error);
        notesApp.showStatus('AI analiz hatası', 'error', 'Bağlantı sorunu');
    } finally {
        setTimeout(() => notesApp.hideAIProgress(), 1000);
    }
}

async function aiSummarize() {
    if (!notesApp.currentNote) {
        notesApp.showStatus('Önce bir not seçin', 'warning');
        return;
    }
    
    try {
        notesApp.showAIProgress('summarize', 15);
        
        const response = await fetch(`${notesApp.apiBaseUrl}/${notesApp.currentNote.id}/ai/summarize`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ length: 'medium' })
        });
        
        notesApp.showAIProgress('summarize', 70);
        const data = await response.json();
        notesApp.showAIProgress('summarize', 100);
        
        if (data.success) {
            const wordCount = data.summary.length;
            notesApp.showStatus('Özet oluşturuldu', 'success', `${wordCount} karakter özet hazır`);
            
            console.log('📄 AI Özet:', data.summary);
            showSummaryModal(data.summary);
        } else {
            notesApp.showStatus('Özet oluşturulamadı', 'error', data.error);
        }
    } catch (error) {
        console.error('AI özet hatası:', error);
        notesApp.showStatus('AI özet hatası', 'error', 'Bağlantı sorunu');
    } finally {
        setTimeout(() => notesApp.hideAIProgress(), 1000);
    }
}

async function aiExpand() {
    if (!notesApp.currentNote) {
        notesApp.showStatus('Önce bir not seçin', 'warning');
        return;
    }
    
    notesApp.showStatus('AI içerik genişletiyor...', 'info');
    
    // TODO: AI genişletme API'si implement edilecek
    setTimeout(() => {
        notesApp.showStatus('İçerik genişletildi', 'success');
    }, 2000);
}

async function aiFindRelated() {
    if (!notesApp.currentNote) {
        notesApp.showStatus('Önce bir not seçin', 'warning');
        return;
    }
    
    notesApp.showStatus('İlgili notlar aranıyor...', 'info');
    
    try {
        const response = await fetch(`${notesApp.apiBaseUrl}/${notesApp.currentNote.id}/ai/related`);
        
        const data = await response.json();
        
        if (data.success) {
            const relatedCount = data.related_notes.length;
            notesApp.showStatus(`✅ ${relatedCount} ilgili not bulundu!`, 'success');
            
            console.log('🔗 İlgili Notlar:', data.related_notes);
            
            if (relatedCount > 0) {
                showRelatedNotesModal(data.related_notes);
            } else {
                notesApp.showStatus('ℹ️ İlgili not bulunamadı', 'info');
            }
        } else {
            notesApp.showStatus(`❌ İlgili not araması başarısız: ${data.error}`, 'error');
        }
    } catch (error) {
        console.error('AI ilgili not arama hatası:', error);
        notesApp.showStatus('❌ AI ilgili not arama hatası', 'error');
    }
}

async function aiSuggestTags() {
    if (!notesApp.currentNote) {
        notesApp.showStatus('Önce bir not seçin', 'warning');
        return;
    }
    
    notesApp.showStatus('AI etiket öneriyor...', 'info');
    
    try {
        const response = await fetch(`${notesApp.apiBaseUrl}/${notesApp.currentNote.id}/ai/suggest-tags`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            notesApp.showStatus(`✅ ${data.suggested_tags.length} etiket önerisi hazır!`, 'success');
            
            console.log('🏷️ Önerilen Etiketler:', data.suggested_tags);
            console.log('🏷️ Mevcut Etiketler:', data.current_tags);
            
            showTagSuggestionsModal(data.suggested_tags, data.current_tags);
        } else {
            notesApp.showStatus(`❌ Etiket önerisi alınamadı: ${data.error}`, 'error');
        }
    } catch (error) {
        console.error('AI etiket önerisi hatası:', error);
        notesApp.showStatus('❌ AI etiket önerisi hatası', 'error');
    }
}

async function aiImproveWriting() {
    if (!notesApp.currentNote) {
        notesApp.showStatus('Önce bir not seçin', 'warning');
        return;
    }
    
    notesApp.showStatus('AI yazımı iyileştiriyor...', 'info');
    
    try {
        const response = await fetch(`${notesApp.apiBaseUrl}/${notesApp.currentNote.id}/ai/improve-writing`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            const improvements = data.improvements;
            notesApp.showStatus(`✅ ${improvements.changes.length} iyileştirme önerisi hazır!`, 'success');
            
            console.log('✍️ Yazım İyileştirmeleri:', improvements);
            
            showWritingImprovementsModal(improvements);
        } else {
            notesApp.showStatus(`❌ Yazım iyileştirme başarısız: ${data.error}`, 'error');
        }
    } catch (error) {
        console.error('AI yazım iyileştirme hatası:', error);
        notesApp.showStatus('❌ AI yazım iyileştirme hatası', 'error');
    }
}

// UI Toggle Functions
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('collapsed');
}

function toggleAIPanel() {
    const aiPanel = document.getElementById('aiPanel');
    aiPanel.classList.toggle('collapsed');
}

function toggleWorkspaces() {
    // TODO: Workspace seçici dropdown implement edilecek
    console.log('Workspace selector');
}

// Global Functions
function createNewNote() {
    notesApp.createNewNote();
}

function saveNote() {
    notesApp.saveNote();
}

// Modal Functions for AI Results
function showAnalysisModal(analysis) {
    const modalHtml = `
        <div class="ai-result-modal" onclick="closeModal(event)">
            <div class="modal-content" onclick="event.stopPropagation()">
                <div class="modal-header">
                    <h3>📊 AI Analiz Sonuçları</h3>
                    <button onclick="closeModal()" class="close-btn">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="analysis-item"><strong>Kategori:</strong> ${analysis.category}</div>
                    <div class="analysis-item"><strong>Duygu Durumu:</strong> ${analysis.sentiment}</div>
                    <div class="analysis-item"><strong>Zorluk Seviyesi:</strong> ${analysis.difficulty}</div>
                    <div class="analysis-item"><strong>Tahmini Okuma Süresi:</strong> ${analysis.estimated_read_time} dakika</div>
                    <div class="analysis-item"><strong>Özet:</strong> ${analysis.summary}</div>
                    <div class="analysis-item"><strong>Anahtar Kelimeler:</strong> ${analysis.keywords.join(', ')}</div>
                    <div class="analysis-item"><strong>Güven Oranı:</strong> %${Math.round(analysis.confidence * 100)}</div>
                </div>
            </div>
        </div>
    `;
    showModal(modalHtml);
}

function showSummaryModal(summary) {
    const modalHtml = `
        <div class="ai-result-modal" onclick="closeModal(event)">
            <div class="modal-content" onclick="event.stopPropagation()">
                <div class="modal-header">
                    <h3>📄 AI Özet</h3>
                    <button onclick="closeModal()" class="close-btn">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="summary-content">${summary}</div>
                </div>
            </div>
        </div>
    `;
    showModal(modalHtml);
}

function showTagSuggestionsModal(suggestedTags, currentTags) {
    const modalHtml = `
        <div class="ai-result-modal" onclick="closeModal(event)">
            <div class="modal-content" onclick="event.stopPropagation()">
                <div class="modal-header">
                    <h3>🏷️ Etiket Önerileri</h3>
                    <button onclick="closeModal()" class="close-btn">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="tags-section">
                        <h4>Önerilen Etiketler:</h4>
                        <div class="tags-list">
                            ${suggestedTags.map(tag => `<span class="suggested-tag" onclick="addTag('${tag}')">${tag}</span>`).join('')}
                        </div>
                    </div>
                    ${currentTags.length > 0 ? `
                    <div class="tags-section">
                        <h4>Mevcut Etiketler:</h4>
                        <div class="tags-list">
                            ${currentTags.map(tag => `<span class="current-tag">${tag}</span>`).join('')}
                        </div>
                    </div>
                    ` : ''}
                </div>
            </div>
        </div>
    `;
    showModal(modalHtml);
}

function showRelatedNotesModal(relatedNotes) {
    const modalHtml = `
        <div class="ai-result-modal" onclick="closeModal(event)">
            <div class="modal-content" onclick="event.stopPropagation()">
                <div class="modal-header">
                    <h3>🔗 İlgili Notlar</h3>
                    <button onclick="closeModal()" class="close-btn">&times;</button>
                </div>
                <div class="modal-body">
                    ${relatedNotes.map(item => `
                        <div class="related-note" onclick="openRelatedNote('${item.note.id}')">
                            <div class="note-title">${item.note.title}</div>
                            <div class="similarity-score">Benzerlik: %${Math.round(item.similarity_score * 100)}</div>
                            <div class="common-keywords">Ortak kelimeler: ${item.common_keywords.join(', ')}</div>
                        </div>
                    `).join('')}
                </div>
            </div>
        </div>
    `;
    showModal(modalHtml);
}

function showWritingImprovementsModal(improvements) {
    const modalHtml = `
        <div class="ai-result-modal" onclick="closeModal(event)">
            <div class="modal-content" onclick="event.stopPropagation()">
                <div class="modal-header">
                    <h3>✍️ Yazım İyileştirmeleri</h3>
                    <button onclick="closeModal()" class="close-btn">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="improvement-section">
                        <h4>İyileştirilmiş Metin:</h4>
                        <div class="improved-text">${improvements.improved_text}</div>
                    </div>
                    ${improvements.changes.length > 0 ? `
                    <div class="improvement-section">
                        <h4>Yapılan Değişiklikler:</h4>
                        ${improvements.changes.map(change => `
                            <div class="change-item">
                                <span class="change-type">${change.type}:</span> ${change.description}
                            </div>
                        `).join('')}
                    </div>
                    ` : ''}
                    ${improvements.suggestions.length > 0 ? `
                    <div class="improvement-section">
                        <h4>Öneriler:</h4>
                        <ul>
                            ${improvements.suggestions.map(suggestion => `<li>${suggestion}</li>`).join('')}
                        </ul>
                    </div>
                    ` : ''}
                </div>
            </div>
        </div>
    `;
    showModal(modalHtml);
}

function showModal(html) {
    // Remove existing modal
    const existingModal = document.querySelector('.ai-result-modal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Add modal styles if not exists
    if (!document.querySelector('#ai-modal-styles')) {
        const styles = document.createElement('style');
        styles.id = 'ai-modal-styles';
        styles.textContent = `
            .ai-result-modal {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.5);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 10000;
            }
            .modal-content {
                background: white;
                border-radius: 12px;
                max-width: 600px;
                width: 90%;
                max-height: 80vh;
                overflow-y: auto;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
            }
            .modal-header {
                padding: 20px;
                border-bottom: 1px solid #eee;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .modal-body {
                padding: 20px;
            }
            .close-btn {
                background: none;
                border: none;
                font-size: 24px;
                cursor: pointer;
                color: #999;
            }
            .analysis-item {
                margin-bottom: 12px;
                padding: 8px;
                background: #f8f9fa;
                border-radius: 6px;
            }
            .suggested-tag, .current-tag {
                display: inline-block;
                padding: 4px 8px;
                margin: 4px;
                border-radius: 4px;
                font-size: 12px;
                cursor: pointer;
            }
            .suggested-tag {
                background: #007bff;
                color: white;
            }
            .current-tag {
                background: #6c757d;
                color: white;
            }
            .related-note {
                padding: 12px;
                border: 1px solid #eee;
                border-radius: 6px;
                margin-bottom: 10px;
                cursor: pointer;
            }
            .related-note:hover {
                background: #f8f9fa;
            }
        `;
        document.head.appendChild(styles);
    }
    
    // Add modal to body
    document.body.insertAdjacentHTML('beforeend', html);
}

function closeModal(event) {
    if (event) event.stopPropagation();
    const modal = document.querySelector('.ai-result-modal');
    if (modal) {
        modal.remove();
    }
}

function addTag(tag) {
    console.log('Etiket ekleniyor:', tag);
    // TODO: Implement tag adding functionality
    notesApp.showStatus(`Etiket "${tag}" eklendi`, 'success');
}

function openRelatedNote(noteId) {
    console.log('İlgili not açılıyor:', noteId);
    // Find and open the related note
    const relatedNote = notesApp.notes.find(n => n.id === noteId);
    if (relatedNote) {
        notesApp.openNote(relatedNote);
        closeModal();
    }
}

// Export İşlemleri
async function exportCurrentNote(format = 'markdown') {
    if (!notesApp.currentNote) {
        notesApp.showStatus('Önce bir not seçin', 'warning');
        return;
    }
    
    notesApp.showStatus(`${format.toUpperCase()} formatına export ediliyor...`, 'info');
    
    try {
        const response = await fetch(`${notesApp.apiBaseUrl}/${notesApp.currentNote.id}/export/${format}`);
        const data = await response.json();
        
        if (data.success) {
            notesApp.showStatus(`✅ Not ${format} formatında export edildi!`, 'success');
            
            // Dosyayı indir
            window.open(data.download_url, '_blank');
        } else {
            notesApp.showStatus(`❌ Export başarısız: ${data.error}`, 'error');
        }
    } catch (error) {
        console.error('Export hatası:', error);
        notesApp.showStatus('❌ Export hatası', 'error');
    }
}

async function exportWorkspace(format = 'markdown', type = 'multiple') {
    if (!notesApp.currentWorkspace) {
        notesApp.showStatus('Workspace bulunamadı', 'warning');
        return;
    }
    
    const exportText = type === 'summary' ? 'özet' : 'tüm notlar';
    notesApp.showStatus(`Workspace ${exportText} export ediliyor...`, 'info');
    
    try {
        const response = await fetch(`${notesApp.apiBaseUrl}/workspace/${notesApp.currentWorkspace}/export`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ format, type })
        });
        
        const data = await response.json();
        
        if (data.success) {
            notesApp.showStatus(`✅ Workspace export edildi! (${data.notes_count} not)`, 'success');
            
            if (data.download_url) {
                // Tek dosya
                window.open(data.download_url, '_blank');
            } else if (data.download_urls) {
                // Birden fazla dosya - ilkini aç
                data.download_urls.forEach((url, index) => {
                    setTimeout(() => window.open(url, '_blank'), index * 500);
                });
            }
        } else {
            notesApp.showStatus(`❌ Export başarısız: ${data.error}`, 'error');
        }
    } catch (error) {
        console.error('Workspace export hatası:', error);
        notesApp.showStatus('❌ Workspace export hatası', 'error');
    }
}

async function showExportModal() {
    if (!notesApp.currentNote) {
        notesApp.showStatus('Önce bir not seçin', 'warning');
        return;
    }
    
    // Export formatlarını yükle
    if (notesApp.exportFormats.length === 0) {
        await notesApp.loadExportFormats();
    }
    
    const formatOptions = notesApp.exportFormats.map(format => 
        `<option value="${format.name}">${format.description}</option>`
    ).join('');
    
    const modalHTML = `
        <div class="modal-header">
            <h3>📄 Export Note</h3>
            <button class="modal-close" onclick="closeModal()">&times;</button>
        </div>
        <div class="modal-body">
            <div class="export-section">
                <h4>Mevcut Not</h4>
                <p><strong>${notesApp.currentNote.title}</strong></p>
                
                <div class="form-group">
                    <label for="exportFormat">Format:</label>
                    <select id="exportFormat" class="form-control">
                        ${formatOptions}
                    </select>
                </div>
                
                <button class="btn btn-primary" onclick="exportSelectedNote()">
                    📥 Export Et
                </button>
            </div>
            
            <hr>
            
            <div class="export-section">
                <h4>Workspace Export</h4>
                <p>Tüm workspace'i export et</p>
                
                <div class="form-group">
                    <label for="workspaceExportFormat">Format:</label>
                    <select id="workspaceExportFormat" class="form-control">
                        ${formatOptions}
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="exportType">Tip:</label>
                    <select id="exportType" class="form-control">
                        <option value="multiple">Tüm Notlar (Ayrı dosyalar)</option>
                        <option value="summary">Workspace Özeti</option>
                    </select>
                </div>
                
                <button class="btn btn-secondary" onclick="exportSelectedWorkspace()">
                    📦 Workspace Export Et
                </button>
            </div>
        </div>
    `;
    
    showModal(modalHTML);
}

function exportSelectedNote() {
    const format = document.getElementById('exportFormat').value;
    exportCurrentNote(format);
    closeModal();
}

function exportSelectedWorkspace() {
    const format = document.getElementById('workspaceExportFormat').value;
    const type = document.getElementById('exportType').value;
    exportWorkspace(format, type);
    closeModal();
}

// Initialize App
let notesApp;
document.addEventListener('DOMContentLoaded', () => {
    notesApp = new NotesApp();
});
