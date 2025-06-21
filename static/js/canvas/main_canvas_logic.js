/**
 * MAIN CANVAS LOGIC
 * Orchestrates Canvas Windows and Live Editors
 */

class CanvasController {
    constructor() {
        this.windowManager = null;
        this.editors = new Map();
        this.socket = null;
        this.apiBaseUrl = '/api/canvas';
        
        this.init();
    }

    async init() {
        try {
            console.log('🚀 Canvas Controller initializing...');
            
            // Initialize window manager
            this.windowManager = new CanvasWindowManager();
            
            // Setup WebSocket connection
            this.setupWebSocket();
            
            // Setup event listeners
            this.setupEventListeners();
            
            // Setup UI integration
            this.setupUIIntegration();
            
            console.log('✅ Canvas Controller ready!');
            
        } catch (error) {
            console.error('❌ Canvas Controller init failed:', error);
        }
    }

    /**
     * WebSocket bağlantısını setup et
     */
    setupWebSocket() {
        if (typeof io !== 'undefined') {
            this.socket = io();
            
            this.socket.on('connect', () => {
                console.log('🔌 Canvas WebSocket connected');
                this.updateAllConnectionStatus('connected');
            });
            
            this.socket.on('disconnect', () => {
                console.log('🔌 Canvas WebSocket disconnected');
                this.updateAllConnectionStatus('offline');
            });
            
            this.socket.on('canvas_event', (data) => {
                this.handleCanvasEvent(data);
            });
            
        } else {
            console.warn('⚠️ Socket.IO not available, running in offline mode');
        }
    }

    /**
     * Event listener'ları setup et
     */
    setupEventListeners() {
        // Window events
        window.addEventListener('canvas-window-closed', (event) => {
            const { windowId } = event.detail;
            this.cleanupEditor(windowId);
        });

        window.addEventListener('canvas-window-focused', (event) => {
            const { windowId } = event.detail;
            this.focusEditor(windowId);
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (event) => {
            this.handleKeyboardShortcuts(event);
        });

        // Page visibility
        document.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'visible') {
                this.syncAllDocuments();
            }
        });
    }

    /**
     * UI integration setup - connect with existing UI
     */
    setupUIIntegration() {
        // Find or create "New Live Document" button
        this.setupNewDocumentButton();
        
        // Update statistics
        this.updateCanvasStatistics();
    }

    /**
     * "New Live Document" butonunu setup et
     */
    setupNewDocumentButton() {
        // Ana sayfa document generation panel'ını güncelle
        const documentPanel = document.querySelector('.document-generation-panel');
        if (documentPanel) {
            // Add new button for live documents
            const liveDocButton = document.createElement('button');
            liveDocButton.className = 'primary-btn live-document-btn';
            liveDocButton.innerHTML = `
                <span class="btn-icon">📝</span>
                <span class="btn-text">Create Live Document</span>
                <span class="btn-description">Real-time collaborative editing</span>
            `;
            
            liveDocButton.addEventListener('click', () => {
                this.createNewLiveDocument();
            });
            
            // Insert button at the beginning
            documentPanel.insertBefore(liveDocButton, documentPanel.firstChild);
        }

        // Add floating action button if needed
        this.createFloatingActionButton();
    }

    /**
     * Floating action button oluştur
     */
    createFloatingActionButton() {
        const fab = document.createElement('button');
        fab.className = 'floating-action-btn';
        fab.innerHTML = '📝';
        fab.title = 'New Live Document';
        fab.style.cssText = `
            position: fixed;
            bottom: 30px;
            right: 30px;
            width: 56px;
            height: 56px;
            border-radius: 50%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
            color: white;
            font-size: 24px;
            cursor: pointer;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
            z-index: 1001;
            transition: all 0.3s ease;
        `;
        
        fab.addEventListener('click', () => {
            this.createNewLiveDocument();
        });
        
        fab.addEventListener('mouseenter', () => {
            fab.style.transform = 'scale(1.1)';
            fab.style.boxShadow = '0 12px 40px rgba(0, 0, 0, 0.3)';
        });
        
        fab.addEventListener('mouseleave', () => {
            fab.style.transform = 'scale(1)';
            fab.style.boxShadow = '0 8px 32px rgba(0, 0, 0, 0.2)';
        });
        
        document.body.appendChild(fab);
    }

    /**
     * Yeni live document oluştur
     */
    async createNewLiveDocument() {
        try {
            // Show loading state
            this.showNotification('Creating new document...', 'info');
            
            // Create document on backend
            const response = await fetch(`${this.apiBaseUrl}/documents`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    title: `New Document ${new Date().toLocaleTimeString()}`,
                    type: 'live_document'
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            
            // Create window with collaboration features
            await this.createLiveDocumentWindow(data.document_id, data.title);
            
        } catch (error) {
            console.error('❌ Document creation failed:', error);
            this.showNotification('Failed to create document', 'error');
        }
    }

    /**
     * Canvas event'lerini handle et
     */
    handleCanvasEvent(data) {
        switch (data.type) {
            case 'document_updated':
                this.handleDocumentUpdate(data);
                break;
            case 'collaborator_joined':
                this.handleCollaboratorJoined(data);
                break;
            case 'collaborator_left':
                this.handleCollaboratorLeft(data);
                break;
        }
    }

    /**
     * Document update handle et
     */
    handleDocumentUpdate(data) {
        const editor = this.editors.get(data.window_id);
        if (editor) {
            editor.handleRemoteContentChange(data.content);
        }
    }

    /**
     * Editor cleanup
     */
    cleanupEditor(windowId) {
        const editor = this.editors.get(windowId);
        if (editor) {
            editor.destroy();
            this.editors.delete(windowId);
            
            console.log(`🧹 Editor cleaned up: ${windowId}`);
        }
        
        this.updateCanvasStatistics();
    }

    /**
     * Editor focus
     */
    focusEditor(windowId) {
        const editor = this.editors.get(windowId);
        if (editor && editor.editor) {
            editor.editor.commands.focus();
        }
    }

    /**
     * Connection status'unu güncelle
     */
    updateAllConnectionStatus(status) {
        this.editors.forEach(editor => {
            editor.updateConnectionStatus(status);
        });
    }

    /**
     * Tüm document'leri sync et
     */
    syncAllDocuments() {
        this.editors.forEach((editor, windowId) => {
            const content = editor.getContent();
            if (content && content.trim()) {
                editor.saveContent(content);
            }
        });
    }

    /**
     * Keyboard shortcut'ları handle et
     */
    handleKeyboardShortcuts(event) {
        // Ctrl/Cmd + N: New document
        if ((event.ctrlKey || event.metaKey) && event.key === 'n') {
            event.preventDefault();
            this.createNewLiveDocument();
        }
        
        // Ctrl/Cmd + S: Save all
        if ((event.ctrlKey || event.metaKey) && event.key === 's') {
            event.preventDefault();
            this.syncAllDocuments();
            this.showNotification('All documents saved', 'success');
        }
    }

    /**
     * Canvas istatistiklerini güncelle
     */
    updateCanvasStatistics() {
        const stats = {
            activeWindows: this.windowManager.getWindowCount(),
            activeEditors: this.editors.size,
            connectedUsers: this.getConnectedUsersCount()
        };

        // Update UI statistics
        const canvasStatsEvent = new CustomEvent('canvas-stats-updated', {
            detail: stats
        });
        window.dispatchEvent(canvasStatsEvent);
    }

    /**
     * Connected user sayısını al
     */
    getConnectedUsersCount() {
        let totalUsers = 0;
        this.editors.forEach(editor => {
            totalUsers += editor.collaborators.size;
        });
        return totalUsers;
    }

    /**
     * Notification göster
     */
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `canvas-notification ${type}`;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 20px;
            background: ${type === 'error' ? '#ef4444' : type === 'success' ? '#10b981' : '#3b82f6'};
            color: white;
            border-radius: 8px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
            z-index: 2000;
            font-size: 14px;
            font-weight: 500;
            transform: translateX(100%);
            transition: transform 0.3s ease;
        `;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 100);
        
        // Remove after delay
        setTimeout(() => {
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 3000);
    }

    /**
     * Canvas'ı tamamen temizle
     */
    clearAllWindows() {
        this.editors.forEach((editor, windowId) => {
            this.windowManager.closeWindow(windowId);
        });
    }

    /**
     * Canvas durumunu al
     */
    getCanvasState() {
        return {
            windowCount: this.windowManager.getWindowCount(),
            editorCount: this.editors.size,
            isConnected: this.socket?.connected || false,
            windows: this.windowManager.getAllWindows().map(w => ({
                id: w.id,
                title: w.title,
                isMaximized: w.isMaximized,
                isMinimized: w.isMinimized
            }))
        };
    }

    // PHASE 6.1: Multi-user Collaboration Methods

    /**
     * Collaborative editor oluştur
     */
    createCollaborativeEditor(windowId, documentId) {
        const editor = new LiveEditor(windowId, `content_${windowId}`, this.socket);
        
        // Auto-join document if provided
        if (documentId && this.socket) {
            editor.joinDocument(documentId);
            
            // Enable collaborative UI
            setTimeout(() => {
                this.enableCollaborationForWindow(windowId);
            }, 500);
        }
        
        this.editors.set(windowId, editor);
        return editor;
    }

    /**
     * Window'u collaborative mode'a geçir
     */
    enableCollaborationForWindow(windowId) {
        const editor = this.editors.get(windowId);
        if (!editor) return;

        // Add collaborative styling
        const contentElement = document.getElementById(`content-${windowId}`);
        if (contentElement) {
            contentElement.classList.add('collaborative');
        }

        // Update status indicator
        const statusElement = document.getElementById(`status-${windowId}`);
        if (statusElement) {
            statusElement.classList.add('collaborative');
        }
        
        console.log(`👥 Collaboration enabled for window: ${windowId}`);
    }

    /**
     * Document'a katıl (existing document için)
     */
    async joinExistingDocument(documentId) {
        try {
            // Get document info
            const response = await fetch(`${this.apiBaseUrl}/documents/${documentId}`);
            if (!response.ok) {
                throw new Error('Document not found');
            }

            const doc = await response.json();
            
            // Create collaborative window
            const windowId = `join_doc_${documentId}`;
            const window = this.windowManager.createWindow({
                id: windowId,
                title: `📄 ${doc.title || 'Shared Document'}`,
                width: 800,
                height: 600,
                type: 'collaborative_document'
            });

            // Create collaborative editor
            const editor = this.createCollaborativeEditor(windowId, documentId);
            
            // Set existing content
            if (doc.content) {
                editor.setContent(doc.content);
            }
            
            this.showNotification(`Joined document "${doc.title}"`, 'success');
            
            return { windowId, editor };
            
        } catch (error) {
            console.error('❌ Failed to join document:', error);
            this.showNotification('Failed to join document', 'error');
            throw error;
        }
    }

    /**
     * Aktif collaboration statistics
     */
    getCollaborationStatistics() {
        let totalUsers = 0;
        let collaborativeDocuments = 0;

        this.editors.forEach((editor, windowId) => {
            if (editor.getActiveUserCount && editor.getActiveUserCount() > 0) {
                totalUsers += editor.getActiveUserCount();
                collaborativeDocuments++;
            }
        });

        return {
            total_users: totalUsers,
            collaborative_documents: collaborativeDocuments,
            total_windows: this.editors.size
        };
    }

    /**
     * Workspace presence güncellemesi
     */
    updateWorkspacePresence() {
        const stats = this.getCollaborationStatistics();
        
        // Broadcast workspace presence
        if (this.socket) {
            this.socket.emit('workspace_presence', {
                user_count: stats.total_users,
                document_count: stats.collaborative_documents
            });
        }
        
        // Update UI indicators
        this.updateCanvasStatistics();
    }

    /**
     * Collaboration event'lerini handle et
     */
    handleCollaborationEvent(event) {
        switch (event.type) {
            case 'user_joined_workspace':
                this.showNotification(`👤 ${event.user_name} joined`, 'info');
                break;
            case 'user_left_workspace':
                this.showNotification(`👋 ${event.user_name} left`, 'info');
                break;
            case 'document_shared':
                this.showNotification(`📄 "${event.document_title}" shared`, 'success');
                break;
            default:
                console.log('Collaboration event:', event);
        }
    }
}

// Global initialization
document.addEventListener('DOMContentLoaded', () => {
    // Initialize canvas controller
    window.canvasController = new CanvasController();
    
    console.log('🎨 Canvas system ready!');
});

// Global exports
window.CanvasController = CanvasController; 