/**
 * CANVAS WINDOW MANAGER
 * Modern floating windows with drag, resize and focus management
 */

class CanvasWindowManager {
    constructor() {
        this.windows = new Map();
        this.activeWindowId = null;
        this.zIndexCounter = 1000;
        this.container = null;
        
        this.init();
    }

    init() {
        // Canvas container oluştur
        this.container = document.getElementById('live-canvas-container');
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.id = 'live-canvas-container';
            document.body.appendChild(this.container);
        }

        // Global event listeners
        document.addEventListener('click', this.handleGlobalClick.bind(this));
        window.addEventListener('resize', this.handleWindowResize.bind(this));
    }

    /**
     * Yeni bir canvas penceresi oluştur
     */
    createWindow(options = {}) {
        const windowId = options.id || `canvas_window_${Date.now()}`;
        const title = options.title || 'Untitled Document';
        const width = options.width || 600;
        const height = options.height || 400;
        
        // Başlangıç pozisyonu (cascade effect)
        const windowCount = this.windows.size;
        const x = options.x || (100 + (windowCount * 30));
        const y = options.y || (100 + (windowCount * 30));

        // Window DOM structure oluştur
        const windowElement = this.createWindowElement(windowId, title, width, height, x, y);
        
        // Window data store et
        const windowData = {
            id: windowId,
            element: windowElement,
            title: title,
            isMaximized: false,
            isMinimized: false,
            originalBounds: { x, y, width, height },
            currentBounds: { x, y, width, height }
        };

        this.windows.set(windowId, windowData);
        this.container.appendChild(windowElement);

        // Interactions setup
        this.setupWindowInteractions(windowData);
        
        // Focus on new window
        this.focusWindow(windowId);

        // Entry animation
        windowElement.classList.add('entering');
        setTimeout(() => {
            windowElement.classList.remove('entering');
        }, 300);

        console.log(`🪟 Yeni canvas window: ${title} (${windowId})`);
        return windowData;
    }

    /**
     * Window DOM elementini oluştur
     */
    createWindowElement(windowId, title, width, height, x, y) {
        const windowEl = document.createElement('div');
        windowEl.className = 'canvas-window';
        windowEl.dataset.windowId = windowId;
        windowEl.style.width = `${width}px`;
        windowEl.style.height = `${height}px`;
        windowEl.style.left = `${x}px`;
        windowEl.style.top = `${y}px`;
        windowEl.style.zIndex = ++this.zIndexCounter;

        windowEl.innerHTML = `
            <div class="canvas-window-header">
                <h3 class="canvas-window-title">${title}</h3>
                <div class="canvas-window-controls">
                    <span class="canvas-status connected">●</span>
                    <button class="canvas-window-control minimize" data-action="minimize">—</button>
                    <button class="canvas-window-control maximize" data-action="maximize">⬜</button>
                    <button class="canvas-window-control close" data-action="close">✕</button>
                </div>
            </div>
            <div class="canvas-window-content">
                <div class="live-editor" id="editor-${windowId}">
                    <!-- Editor will be injected here -->
                </div>
            </div>
            <div class="resize-handle se"></div>
            <div class="resize-handle e"></div>
            <div class="resize-handle s"></div>
        `;

        return windowEl;
    }

    /**
     * Window interaction'larını setup et (drag, resize, controls)
     */
    setupWindowInteractions(windowData) {
        const { element, id } = windowData;
        const header = element.querySelector('.canvas-window-header');
        const controls = element.querySelectorAll('.canvas-window-control');
        const resizeHandles = element.querySelectorAll('.resize-handle');

        // Window controls
        controls.forEach(control => {
            control.addEventListener('click', (e) => {
                e.stopPropagation();
                const action = control.dataset.action;
                this.handleWindowControl(id, action);
            });
        });

        // Setup drag with interact.js (will be loaded)
        if (window.interact) {
            // Draggable
            interact(element).draggable({
                allowFrom: header,
                listeners: {
                    move: (event) => {
                        const { dx, dy } = event;
                        const currentX = parseFloat(element.style.left) || 0;
                        const currentY = parseFloat(element.style.top) || 0;
                        
                        const newX = currentX + dx;
                        const newY = Math.max(0, currentY + dy); // Don't go above screen
                        
                        element.style.left = `${newX}px`;
                        element.style.top = `${newY}px`;
                        
                        // Update bounds
                        windowData.currentBounds.x = newX;
                        windowData.currentBounds.y = newY;
                    }
                }
            });

            // Resizable
            interact(element).resizable({
                edges: { left: false, right: true, bottom: true, top: false },
                listeners: {
                    move: (event) => {
                        const { width, height } = event.rect;
                        
                        element.style.width = `${Math.max(300, width)}px`;
                        element.style.height = `${Math.max(200, height)}px`;
                        
                        // Update bounds
                        windowData.currentBounds.width = width;
                        windowData.currentBounds.height = height;
                    }
                }
            });
        }

        // Focus on click
        element.addEventListener('mousedown', () => {
            this.focusWindow(id);
        });
    }

    /**
     * Window kontrol butonlarını handle et
     */
    handleWindowControl(windowId, action) {
        const windowData = this.windows.get(windowId);
        if (!windowData) return;

        switch (action) {
            case 'minimize':
                this.minimizeWindow(windowId);
                break;
            case 'maximize':
                this.toggleMaximizeWindow(windowId);
                break;
            case 'close':
                this.closeWindow(windowId);
                break;
        }
    }

    /**
     * Pencereyi minimize et
     */
    minimizeWindow(windowId) {
        const windowData = this.windows.get(windowId);
        if (!windowData) return;

        const { element } = windowData;
        if (windowData.isMinimized) {
            // Restore
            element.style.display = 'flex';
            windowData.isMinimized = false;
        } else {
            // Minimize
            element.style.display = 'none';
            windowData.isMinimized = true;
        }
    }

    /**
     * Maximize/restore pencere
     */
    toggleMaximizeWindow(windowId) {
        const windowData = this.windows.get(windowId);
        if (!windowData) return;

        const { element } = windowData;
        
        if (windowData.isMaximized) {
            // Restore to original size
            const { x, y, width, height } = windowData.originalBounds;
            element.style.left = `${x}px`;
            element.style.top = `${y}px`;
            element.style.width = `${width}px`;
            element.style.height = `${height}px`;
            windowData.isMaximized = false;
        } else {
            // Maximize
            element.style.left = '20px';
            element.style.top = '20px';
            element.style.width = 'calc(100vw - 40px)';
            element.style.height = 'calc(100vh - 40px)';
            windowData.isMaximized = true;
        }
    }

    /**
     * Pencereyi kapat
     */
    closeWindow(windowId) {
        const windowData = this.windows.get(windowId);
        if (!windowData) return;

        const { element } = windowData;
        
        // Closing animation
        element.classList.add('leaving');
        
        setTimeout(() => {
            element.remove();
            this.windows.delete(windowId);
            
            // If this was active window, focus another
            if (this.activeWindowId === windowId) {
                const remainingWindows = Array.from(this.windows.keys());
                if (remainingWindows.length > 0) {
                    this.focusWindow(remainingWindows[remainingWindows.length - 1]);
                } else {
                    this.activeWindowId = null;
                }
            }
            
            console.log(`🗑️ Canvas window closed: ${windowId}`);
            
            // Event for cleanup
            window.dispatchEvent(new CustomEvent('canvas-window-closed', {
                detail: { windowId }
            }));
            
        }, 200);
    }

    /**
     * Pencereyi focus et
     */
    focusWindow(windowId) {
        const windowData = this.windows.get(windowId);
        if (!windowData) return;

        // Remove active class from all windows
        this.windows.forEach(data => {
            data.element.classList.remove('active');
        });

        // Add active class to current window
        windowData.element.classList.add('active');
        windowData.element.style.zIndex = ++this.zIndexCounter;
        
        this.activeWindowId = windowId;
        
        // Event for editor focus
        window.dispatchEvent(new CustomEvent('canvas-window-focused', {
            detail: { windowId }
        }));
    }

    /**
     * Window başlığını güncelle
     */
    updateWindowTitle(windowId, newTitle) {
        const windowData = this.windows.get(windowId);
        if (!windowData) return;

        const titleElement = windowData.element.querySelector('.canvas-window-title');
        if (titleElement) {
            titleElement.textContent = newTitle;
            windowData.title = newTitle;
        }
    }

    /**
     * Window status'unu güncelle (connected, saving, offline)
     */
    updateWindowStatus(windowId, status) {
        const windowData = this.windows.get(windowId);
        if (!windowData) return;

        const statusElement = windowData.element.querySelector('.canvas-status');
        if (statusElement) {
            statusElement.className = `canvas-status ${status}`;
            
            const statusText = {
                'connected': '●',
                'saving': '⏳',
                'offline': '⚠'
            };
            
            statusElement.textContent = statusText[status] || '●';
        }
    }

    /**
     * Global click handler
     */
    handleGlobalClick(event) {
        // Check if click is outside all windows
        const clickedWindow = event.target.closest('.canvas-window');
        if (!clickedWindow && this.activeWindowId) {
            // Unfocus active window if clicked outside
            const activeWindow = this.windows.get(this.activeWindowId);
            if (activeWindow) {
                activeWindow.element.classList.remove('active');
            }
        }
    }

    /**
     * Window resize handler
     */
    handleWindowResize() {
        // Reposition windows that are outside viewport
        this.windows.forEach((windowData) => {
            const { element } = windowData;
            const rect = element.getBoundingClientRect();
            
            if (rect.left < 0) {
                element.style.left = '20px';
            }
            if (rect.top < 0) {
                element.style.top = '20px';
            }
        });
    }

    /**
     * Aktif window'u al
     */
    getActiveWindow() {
        return this.windows.get(this.activeWindowId);
    }

    /**
     * Tüm window'ları al
     */
    getAllWindows() {
        return Array.from(this.windows.values());
    }

    /**
     * Window sayısını al
     */
    getWindowCount() {
        return this.windows.size;
    }
}

// Global instance
window.CanvasWindowManager = CanvasWindowManager; 