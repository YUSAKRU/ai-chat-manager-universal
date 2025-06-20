"""
🎨 Canvas Interface - Floating Window Management
===============================================

Kullanıcı arayüzü için floating window sistemi:
- Resizable/draggable document windows
- Multi-document tab management
- Rich text editor integration
- Real-time collaboration UI components
"""

from typing import Dict, List, Optional, Any
from datetime import datetime


class CanvasWindow:
    """Canvas floating window tanımı"""
    
    def __init__(self, window_id: str, document_id: str, title: str):
        self.window_id = window_id
        self.document_id = document_id
        self.title = title
        self.position = {'x': 100, 'y': 100}
        self.size = {'width': 600, 'height': 400}
        self.is_minimized = False
        self.is_maximized = False
        self.z_index = 1000
        self.created_at = datetime.now().isoformat()
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            'window_id': self.window_id,
            'document_id': self.document_id,
            'title': self.title,
            'position': self.position,
            'size': self.size,
            'is_minimized': self.is_minimized,
            'is_maximized': self.is_maximized,
            'z_index': self.z_index,
            'created_at': self.created_at
        }


class CanvasInterface:
    """Canvas Interface Management"""
    
    def __init__(self):
        self.active_windows: Dict[str, CanvasWindow] = {}
        self.next_z_index = 1000
        self.max_windows = 5  # Maximum simultaneous windows
        
        print("🎨 Canvas Interface başlatıldı!")
    
    def create_window(self, document_id: str, title: str) -> str:
        """Yeni floating window oluştur"""
        
        # Maximum window check
        if len(self.active_windows) >= self.max_windows:
            oldest_window_id = min(self.active_windows.keys(), 
                                 key=lambda x: self.active_windows[x].created_at)
            self.close_window(oldest_window_id)
        
        # Window ID oluştur
        window_id = f"canvas_window_{int(datetime.now().timestamp())}"
        
        # Window objesi oluştur
        window = CanvasWindow(window_id, document_id, title)
        
        # Cascade positioning
        offset = len(self.active_windows) * 30
        window.position = {'x': 100 + offset, 'y': 100 + offset}
        
        # Z-index ayarla
        window.z_index = self.next_z_index
        self.next_z_index += 1
        
        # Window'u kaydet
        self.active_windows[window_id] = window
        
        print(f"🪟 Yeni canvas window: {title} ({window_id})")
        
        return window_id
    
    def close_window(self, window_id: str) -> bool:
        """Window'u kapat"""
        if window_id in self.active_windows:
            window = self.active_windows[window_id]
            del self.active_windows[window_id]
            print(f"❌ Canvas window kapatıldı: {window.title}")
            return True
        return False
    
    def minimize_window(self, window_id: str) -> bool:
        """Window'u minimize et"""
        if window_id in self.active_windows:
            self.active_windows[window_id].is_minimized = True
            print(f"➖ Window minimize edildi: {window_id}")
            return True
        return False
    
    def restore_window(self, window_id: str) -> bool:
        """Window'u restore et"""
        if window_id in self.active_windows:
            window = self.active_windows[window_id]
            window.is_minimized = False
            window.is_maximized = False
            return True
        return False
    
    def maximize_window(self, window_id: str) -> bool:
        """Window'u maximize et"""
        if window_id in self.active_windows:
            window = self.active_windows[window_id]
            window.is_maximized = True
            window.is_minimized = False
            return True
        return False
    
    def update_window_position(self, window_id: str, x: int, y: int) -> bool:
        """Window pozisyonunu güncelle"""
        if window_id in self.active_windows:
            self.active_windows[window_id].position = {'x': x, 'y': y}
            return True
        return False
    
    def update_window_size(self, window_id: str, width: int, height: int) -> bool:
        """Window boyutunu güncelle"""
        if window_id in self.active_windows:
            self.active_windows[window_id].size = {'width': width, 'height': height}
            return True
        return False
    
    def bring_to_front(self, window_id: str) -> bool:
        """Window'u öne getir"""
        if window_id in self.active_windows:
            self.active_windows[window_id].z_index = self.next_z_index
            self.next_z_index += 1
            return True
        return False
    
    def get_window_info(self, window_id: str) -> Optional[Dict[str, Any]]:
        """Window bilgilerini getir"""
        if window_id in self.active_windows:
            return self.active_windows[window_id].to_dict()
        return None
    
    def list_active_windows(self) -> List[Dict[str, Any]]:
        """Aktif window'ları listele"""
        return [window.to_dict() for window in self.active_windows.values()]
    
    def get_window_by_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Document ID'sine göre window bul"""
        for window in self.active_windows.values():
            if window.document_id == document_id:
                return window.to_dict()
        return None
    
    def generate_canvas_html(self) -> str:
        """Canvas HTML template oluştur"""
        
        html_template = """
<!-- 🎨 Live Document Canvas Container -->
<div id="documentCanvasContainer" class="canvas-container">
    
    <!-- Canvas Toolbar -->
    <div id="canvasToolbar" class="canvas-toolbar">
        <div class="toolbar-section">
            <button id="createDocumentBtn" class="btn btn-primary btn-sm">
                <i class="fas fa-plus"></i> Yeni Belge
            </button>
            <button id="openDocumentBtn" class="btn btn-secondary btn-sm">
                <i class="fas fa-folder-open"></i> Belge Aç
            </button>
        </div>
        
        <div class="toolbar-section">
            <span id="activeWindowsCount" class="badge badge-info">0 aktif pencere</span>
        </div>
        
        <div class="toolbar-section">
            <button id="minimizeAllBtn" class="btn btn-sm btn-outline-secondary">
                <i class="fas fa-window-minimize"></i> Tümünü Küçült
            </button>
            <button id="closeAllBtn" class="btn btn-sm btn-outline-danger">
                <i class="fas fa-times"></i> Tümünü Kapat
            </button>
        </div>
    </div>
    
    <!-- Canvas Area -->
    <div id="canvasArea" class="canvas-area">
        <!-- Floating windows will be dynamically created here -->
    </div>
    
    <!-- Minimized Windows Dock -->
    <div id="minimizedDock" class="minimized-dock">
        <!-- Minimized windows appear here -->
    </div>
    
</div>

<!-- Document Window Template -->
<template id="documentWindowTemplate">
    <div class="document-window" data-window-id="">
        
        <!-- Window Header -->
        <div class="window-header">
            <div class="window-title">
                <i class="fas fa-file-alt"></i>
                <span class="title-text">Belge Başlığı</span>
                <span class="document-status"></span>
            </div>
            
            <div class="window-controls">
                <button class="window-btn minimize-btn" title="Küçült">
                    <i class="fas fa-window-minimize"></i>
                </button>
                <button class="window-btn maximize-btn" title="Büyüt">
                    <i class="fas fa-window-maximize"></i>
                </button>
                <button class="window-btn close-btn" title="Kapat">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        </div>
        
        <!-- Window Content -->
        <div class="window-content">
            
            <!-- Document Toolbar -->
            <div class="document-toolbar">
                <div class="toolbar-group">
                    <button class="doc-btn" data-action="bold" title="Kalın">
                        <i class="fas fa-bold"></i>
                    </button>
                    <button class="doc-btn" data-action="italic" title="İtalik">
                        <i class="fas fa-italic"></i>
                    </button>
                    <button class="doc-btn" data-action="heading" title="Başlık">
                        <i class="fas fa-heading"></i>
                    </button>
                </div>
                
                <div class="toolbar-group">
                    <button class="doc-btn" data-action="list" title="Liste">
                        <i class="fas fa-list-ul"></i>
                    </button>
                    <button class="doc-btn" data-action="link" title="Bağlantı">
                        <i class="fas fa-link"></i>
                    </button>
                    <button class="doc-btn" data-action="table" title="Tablo">
                        <i class="fas fa-table"></i>
                    </button>
                </div>
                
                <div class="toolbar-group">
                    <span class="version-info">v<span class="version-number">1</span></span>
                    <span class="collaborators-count">👥 <span class="count">0</span></span>
                </div>
            </div>
            
            <!-- Rich Text Editor -->
            <div class="document-editor" contenteditable="true" 
                 data-document-id="" 
                 placeholder="Belge içeriğinizi buraya yazın...">
            </div>
            
            <!-- Collaboration Indicators -->
            <div class="collaboration-indicators">
                <div class="active-users"></div>
                <div class="ai-activity"></div>
            </div>
            
        </div>
        
        <!-- Window Resize Handles -->
        <div class="resize-handle resize-n"></div>
        <div class="resize-handle resize-s"></div>
        <div class="resize-handle resize-w"></div>
        <div class="resize-handle resize-e"></div>
        <div class="resize-handle resize-nw"></div>
        <div class="resize-handle resize-ne"></div>
        <div class="resize-handle resize-sw"></div>
        <div class="resize-handle resize-se"></div>
        
    </div>
</template>
"""
        
        return html_template.strip()
    
    def generate_canvas_css(self) -> str:
        """Canvas CSS stillerini oluştur"""
        
        css_styles = """
/* 🎨 Live Document Canvas Styles */

.canvas-container {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    z-index: 1000;
    background: rgba(0, 0, 0, 0.1);
    backdrop-filter: blur(2px);
    display: none; /* Initially hidden */
    pointer-events: none;
}

.canvas-container.active {
    display: block;
    pointer-events: auto;
}

/* Canvas Toolbar */
.canvas-toolbar {
    position: absolute;
    top: 20px;
    left: 50%;
    transform: translateX(-50%);
    background: rgba(255, 255, 255, 0.95);
    border-radius: 25px;
    padding: 10px 20px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
    display: flex;
    align-items: center;
    gap: 20px;
    backdrop-filter: blur(10px);
    z-index: 2000;
}

.toolbar-section {
    display: flex;
    align-items: center;
    gap: 10px;
}

/* Canvas Area */
.canvas-area {
    position: relative;
    width: 100%;
    height: 100%;
    overflow: hidden;
}

/* Document Window */
.document-window {
    position: absolute;
    background: white;
    border-radius: 12px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
    min-width: 400px;
    min-height: 300px;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    transition: all 0.3s ease;
    border: 1px solid rgba(255, 255, 255, 0.2);
}

.document-window:hover {
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.25);
}

.document-window.minimized {
    display: none;
}

.document-window.maximized {
    top: 20px !important;
    left: 20px !important;
    width: calc(100vw - 40px) !important;
    height: calc(100vh - 40px) !important;
}

/* Window Header */
.window-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 12px 16px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    cursor: move;
    user-select: none;
}

.window-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 600;
}

.document-status {
    font-size: 0.8em;
    opacity: 0.8;
    margin-left: 8px;
}

.window-controls {
    display: flex;
    gap: 5px;
}

.window-btn {
    background: rgba(255, 255, 255, 0.2);
    border: none;
    color: white;
    width: 28px;
    height: 28px;
    border-radius: 6px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s;
}

.window-btn:hover {
    background: rgba(255, 255, 255, 0.3);
    transform: scale(1.1);
}

.close-btn:hover {
    background: #e74c3c;
}

/* Window Content */
.window-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
}

/* Document Toolbar */
.document-toolbar {
    background: #f8f9fa;
    border-bottom: 1px solid #dee2e6;
    padding: 8px 12px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 10px;
}

.toolbar-group {
    display: flex;
    align-items: center;
    gap: 5px;
}

.doc-btn {
    background: white;
    border: 1px solid #dee2e6;
    color: #495057;
    width: 32px;
    height: 32px;
    border-radius: 6px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s;
}

.doc-btn:hover {
    background: #e9ecef;
    border-color: #adb5bd;
}

.doc-btn.active {
    background: #007bff;
    color: white;
    border-color: #007bff;
}

.version-info, .collaborators-count {
    font-size: 0.85em;
    color: #6c757d;
    font-weight: 500;
}

/* Rich Text Editor */
.document-editor {
    flex: 1;
    padding: 20px;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    font-size: 14px;
    line-height: 1.6;
    overflow-y: auto;
    outline: none;
    background: white;
}

.document-editor:empty:before {
    content: attr(placeholder);
    color: #adb5bd;
    font-style: italic;
}

/* Collaboration Indicators */
.collaboration-indicators {
    background: #f8f9fa;
    border-top: 1px solid #dee2e6;
    padding: 8px 12px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.8em;
}

.active-users {
    display: flex;
    gap: 5px;
}

.user-indicator {
    background: #28a745;
    color: white;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 0.75em;
}

.ai-activity {
    color: #6c757d;
    font-style: italic;
}

/* Resize Handles */
.resize-handle {
    position: absolute;
    background: transparent;
}

.resize-n, .resize-s {
    height: 6px;
    left: 6px;
    right: 6px;
    cursor: ns-resize;
}

.resize-n { top: -3px; }
.resize-s { bottom: -3px; }

.resize-w, .resize-e {
    width: 6px;
    top: 6px;
    bottom: 6px;
    cursor: ew-resize;
}

.resize-w { left: -3px; }
.resize-e { right: -3px; }

.resize-nw, .resize-ne, .resize-sw, .resize-se {
    width: 12px;
    height: 12px;
    cursor: nwse-resize;
}

.resize-nw { top: -6px; left: -6px; cursor: nw-resize; }
.resize-ne { top: -6px; right: -6px; cursor: ne-resize; }
.resize-sw { bottom: -6px; left: -6px; cursor: sw-resize; }
.resize-se { bottom: -6px; right: -6px; cursor: se-resize; }

/* Minimized Dock */
.minimized-dock {
    position: absolute;
    bottom: 20px;
    left: 50%;
    transform: translateX(-50%);
    background: rgba(255, 255, 255, 0.95);
    border-radius: 25px;
    padding: 10px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
    display: flex;
    gap: 10px;
    backdrop-filter: blur(10px);
    z-index: 2000;
}

.minimized-window {
    background: #667eea;
    color: white;
    padding: 8px 16px;
    border-radius: 15px;
    cursor: pointer;
    transition: all 0.2s;
    font-size: 0.9em;
    white-space: nowrap;
}

.minimized-window:hover {
    background: #764ba2;
    transform: scale(1.05);
}

/* Animations */
@keyframes windowAppear {
    from {
        opacity: 0;
        transform: scale(0.8) translateY(20px);
    }
    to {
        opacity: 1;
        transform: scale(1) translateY(0);
    }
}

.document-window {
    animation: windowAppear 0.3s ease-out;
}

/* Responsive */
@media (max-width: 768px) {
    .canvas-toolbar {
        width: calc(100% - 40px);
        left: 20px;
        transform: none;
        flex-direction: column;
        gap: 10px;
    }
    
    .document-window {
        min-width: 300px;
    }
    
    .document-window.maximized {
        top: 10px !important;
        left: 10px !important;
        width: calc(100vw - 20px) !important;
        height: calc(100vh - 20px) !important;
    }
}
"""
        
        return css_styles.strip()
    
    def generate_canvas_javascript(self) -> str:
        """Canvas JavaScript fonksiyonlarını oluştur"""
        
        js_code = """
// 🎨 Live Document Canvas JavaScript

class DocumentCanvas {
    constructor() {
        this.activeWindows = new Map();
        this.dragState = null;
        this.resizeState = null;
        this.isCanvasActive = false;
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.setupSocketEvents();
        console.log('🎨 Document Canvas initialized');
    }
    
    setupEventListeners() {
        // Canvas toggle
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'd') {
                e.preventDefault();
                this.toggleCanvas();
            }
        });
        
        // Canvas toolbar events
        const toolbar = document.getElementById('canvasToolbar');
        if (toolbar) {
            toolbar.addEventListener('click', (e) => {
                const btn = e.target.closest('button');
                if (!btn) return;
                
                switch (btn.id) {
                    case 'createDocumentBtn':
                        this.createNewDocument();
                        break;
                    case 'openDocumentBtn':
                        this.openExistingDocument();
                        break;
                    case 'minimizeAllBtn':
                        this.minimizeAllWindows();
                        break;
                    case 'closeAllBtn':
                        this.closeAllWindows();
                        break;
                }
            });
        }
        
        // Global mouse events for drag/resize
        document.addEventListener('mousemove', (e) => {
            this.handleMouseMove(e);
        });
        
        document.addEventListener('mouseup', (e) => {
            this.handleMouseUp(e);
        });
    }
    
    setupSocketEvents() {
        if (typeof socket !== 'undefined') {
            // Document changes
            socket.on('document_changed', (data) => {
                this.handleDocumentChange(data);
            });
            
            // User activity
            socket.on('user_joined_document', (data) => {
                this.updateCollaborators(data.document_id);
            });
            
            socket.on('user_left_document', (data) => {
                this.updateCollaborators(data.document_id);
            });
            
            // AI activity
            socket.on('ai_document_activity', (data) => {
                this.showAIActivity(data);
            });
        }
    }
    
    toggleCanvas() {
        const container = document.getElementById('documentCanvasContainer');
        if (!container) return;
        
        this.isCanvasActive = !this.isCanvasActive;
        container.classList.toggle('active', this.isCanvasActive);
        
        if (this.isCanvasActive) {
            this.updateWindowCount();
        }
    }
    
    createWindow(documentId, title, position = null, size = null) {
        const template = document.getElementById('documentWindowTemplate');
        if (!template) return null;
        
        const windowElement = template.content.cloneNode(true);
        const windowDiv = windowElement.querySelector('.document-window');
        
        // Generate window ID
        const windowId = 'window_' + Date.now();
        windowDiv.dataset.windowId = windowId;
        
        // Set title
        const titleSpan = windowDiv.querySelector('.title-text');
        titleSpan.textContent = title;
        
        // Set document ID
        const editor = windowDiv.querySelector('.document-editor');
        editor.dataset.documentId = documentId;
        
        // Set position
        if (position) {
            windowDiv.style.left = position.x + 'px';
            windowDiv.style.top = position.y + 'px';
        } else {
            const offset = this.activeWindows.size * 30;
            windowDiv.style.left = (100 + offset) + 'px';
            windowDiv.style.top = (100 + offset) + 'px';
        }
        
        // Set size
        if (size) {
            windowDiv.style.width = size.width + 'px';
            windowDiv.style.height = size.height + 'px';
        }
        
        // Setup window events
        this.setupWindowEvents(windowDiv);
        
        // Add to canvas
        const canvasArea = document.getElementById('canvasArea');
        canvasArea.appendChild(windowDiv);
        
        // Store reference
        this.activeWindows.set(windowId, {
            element: windowDiv,
            documentId: documentId,
            title: title
        });
        
        this.updateWindowCount();
        this.bringToFront(windowId);
        
        // Join document room
        if (typeof socket !== 'undefined') {
            socket.emit('join_document', {
                document_id: documentId,
                user_id: 'human_user'
            });
        }
        
        return windowId;
    }
    
    setupWindowEvents(windowElement) {
        const windowId = windowElement.dataset.windowId;
        
        // Header drag
        const header = windowElement.querySelector('.window-header');
        header.addEventListener('mousedown', (e) => {
            if (e.target.closest('.window-controls')) return;
            this.startDrag(windowId, e);
        });
        
        // Control buttons
        const controls = windowElement.querySelector('.window-controls');
        controls.addEventListener('click', (e) => {
            const btn = e.target.closest('.window-btn');
            if (!btn) return;
            
            if (btn.classList.contains('close-btn')) {
                this.closeWindow(windowId);
            } else if (btn.classList.contains('minimize-btn')) {
                this.minimizeWindow(windowId);
            } else if (btn.classList.contains('maximize-btn')) {
                this.toggleMaximize(windowId);
            }
        });
        
        // Resize handles
        const resizeHandles = windowElement.querySelectorAll('.resize-handle');
        resizeHandles.forEach(handle => {
            handle.addEventListener('mousedown', (e) => {
                this.startResize(windowId, e, handle.className);
            });
        });
        
        // Editor events
        const editor = windowElement.querySelector('.document-editor');
        editor.addEventListener('input', (e) => {
            this.handleEditorChange(windowId, e);
        });
        
        // Click to bring to front
        windowElement.addEventListener('mousedown', () => {
            this.bringToFront(windowId);
        });
    }
    
    closeWindow(windowId) {
        const windowData = this.activeWindows.get(windowId);
        if (!windowData) return;
        
        // Leave document room
        if (typeof socket !== 'undefined') {
            socket.emit('leave_document', {
                document_id: windowData.documentId,
                user_id: 'human_user'
            });
        }
        
        // Remove element
        windowData.element.remove();
        
        // Remove from map
        this.activeWindows.delete(windowId);
        
        this.updateWindowCount();
    }
    
    minimizeWindow(windowId) {
        const windowData = this.activeWindows.get(windowId);
        if (!windowData) return;
        
        windowData.element.classList.add('minimized');
        this.addToMinimizedDock(windowId, windowData.title);
    }
    
    restoreWindow(windowId) {
        const windowData = this.activeWindows.get(windowId);
        if (!windowData) return;
        
        windowData.element.classList.remove('minimized');
        this.removeFromMinimizedDock(windowId);
        this.bringToFront(windowId);
    }
    
    addToMinimizedDock(windowId, title) {
        const dock = document.getElementById('minimizedDock');
        
        const minimizedElement = document.createElement('div');
        minimizedElement.className = 'minimized-window';
        minimizedElement.dataset.windowId = windowId;
        minimizedElement.textContent = title;
        
        minimizedElement.addEventListener('click', () => {
            this.restoreWindow(windowId);
        });
        
        dock.appendChild(minimizedElement);
    }
    
    removeFromMinimizedDock(windowId) {
        const dock = document.getElementById('minimizedDock');
        const minimized = dock.querySelector(`[data-window-id="${windowId}"]`);
        if (minimized) {
            minimized.remove();
        }
    }
    
    bringToFront(windowId) {
        const windowData = this.activeWindows.get(windowId);
        if (!windowData) return;
        
        // Find highest z-index
        let maxZ = 1000;
        this.activeWindows.forEach(data => {
            const z = parseInt(data.element.style.zIndex) || 1000;
            if (z > maxZ) maxZ = z;
        });
        
        // Set this window's z-index higher
        windowData.element.style.zIndex = maxZ + 1;
    }
    
    updateWindowCount() {
        const countElement = document.getElementById('activeWindowsCount');
        if (countElement) {
            const count = this.activeWindows.size;
            countElement.textContent = `${count} aktif pencere`;
        }
    }
    
    handleDocumentChange(data) {
        // Find window with this document
        for (const [windowId, windowData] of this.activeWindows) {
            if (windowData.documentId === data.document_id) {
                const editor = windowData.element.querySelector('.document-editor');
                // Update editor content if needed
                // (implement operational transform here)
                break;
            }
        }
    }
    
    createNewDocument() {
        // Implementation for creating new document
        const title = prompt('Belge başlığını girin:', 'Yeni Belge');
        if (title) {
            // Create document via API
            fetch('/api/canvas/documents', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title, content: '', type: 'markdown' })
            })
            .then(response => response.json())
            .then(data => {
                this.createWindow(data.document_id, title);
            });
        }
    }
    
    openExistingDocument() {
        // Implementation for opening existing document
        console.log('Open existing document dialog');
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.documentCanvas = new DocumentCanvas();
});
"""
        
        return js_code.strip()
    
    def get_canvas_statistics(self) -> Dict[str, Any]:
        """Canvas istatistikleri"""
        return {
            'active_windows': len(self.active_windows),
            'max_windows': self.max_windows,
            'next_z_index': self.next_z_index,
            'windows_details': [w.to_dict() for w in self.active_windows.values()]
        } 