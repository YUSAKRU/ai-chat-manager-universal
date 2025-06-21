/**
 * LIVE EDITOR
 * Tiptap-based collaborative editor with real-time sync
 */

class LiveEditor {
    constructor(windowId, containerId, socket) {
        this.windowId = windowId;
        this.containerId = containerId;
        this.socket = socket;
        this.editor = null;
        this.documentId = null;
        this.isConnected = false;
        this.lastSavedContent = '';
        this.saveTimeout = null;
        this.collaborators = new Map();
        
        // PHASE 6.1: Multi-user collaboration
        this.currentUsers = new Map();  // Active users in document
        this.remoteCursors = new Map(); // Remote user cursors
        this.userInfo = {
            name: `User_${Math.random().toString(36).substr(2, 6)}`,
            color: this.generateUserColor()
        };
        this.mouseMoveThrottle = null;
        this.isJoinedDocument = false;
        
        // PHASE 6.2: Document Conflict Resolution
        this.otEngine = null; // Will be initialized with OT engine
        this.lastContent = '';
        this.operationBuffer = [];
        this.isApplyingRemoteChanges = false;
        
        this.init();
    }

    async init() {
        try {
            await this.setupEditor();
            this.setupWebSocketListeners();
            this.setupAutoSave();
            this.initializeOTEngine(); // PHASE 6.2: Initialize OT engine
            console.log(`📝 Live Editor initialized for window: ${this.windowId}`);
        } catch (error) {
            console.error('❌ LiveEditor init failed:', error);
            this.showError('Editor initialization failed');
        }
    }

    /**
     * Tiptap editor'ı setup et
     */
    async setupEditor() {
        const container = document.getElementById(this.containerId);
        if (!container) {
            throw new Error(`Container not found: ${this.containerId}`);
        }

        // Editor container oluştur
        container.innerHTML = `
            <div class="live-editor-toolbar">
                <button class="editor-tool-btn" data-tool="bold"><strong>B</strong></button>
                <button class="editor-tool-btn" data-tool="italic"><em>I</em></button>
                <button class="editor-tool-btn" data-tool="heading1">H1</button>
                <button class="editor-tool-btn" data-tool="heading2">H2</button>
                <button class="editor-tool-btn" data-tool="bulletList">•</button>
                <button class="editor-tool-btn" data-tool="orderedList">1.</button>
                <button class="editor-tool-btn" data-tool="blockquote">❝</button>
                <button class="editor-tool-btn" data-tool="code">‹›</button>
                <div style="flex: 1;"></div>
                <div class="user-presence" id="presence-${this.windowId}">
                    <!-- Active users will appear here -->
                </div>
                <span class="canvas-status connected" id="status-${this.windowId}">●</span>
            </div>
            <div class="live-editor-content" id="content-${this.windowId}">
                <!-- Tiptap editor will be mounted here -->
                <div class="remote-cursors" id="cursors-${this.windowId}">
                    <!-- Remote user cursors will appear here -->
                </div>
            </div>
        `;

        // Check if Tiptap is available (CDN loaded)
        if (typeof window.Editor === 'undefined') {
            // Create basic textarea fallback
            this.createFallbackEditor();
            return;
        }

        // Initialize Tiptap editor
        this.editor = new window.Editor({
            element: document.getElementById(`content-${this.windowId}`),
            extensions: [
                window.StarterKit,
                window.Collaboration.configure({
                    document: this.documentId
                }),
                window.CollaborationCursor.configure({
                    provider: this.createCollaborationProvider(),
                    user: {
                        name: 'User',
                        color: this.generateUserColor()
                    }
                })
            ],
            content: '<p>Start typing...</p>',
            onUpdate: ({ editor }) => {
                this.handleContentChange(editor.getHTML());
            },
            onSelectionUpdate: ({ editor }) => {
                this.updateToolbarState(editor);
            },
            onFocus: () => {
                this.updateConnectionStatus('connected');
            }
        });

        // Setup toolbar
        this.setupToolbar();
    }

    /**
     * Fallback editor (basic textarea) for when Tiptap is not available
     */
    createFallbackEditor() {
        const contentDiv = document.getElementById(`content-${this.windowId}`);
        contentDiv.innerHTML = `
            <textarea 
                class="fallback-editor" 
                style="width: 100%; height: 100%; border: none; outline: none; resize: none; font-family: inherit; font-size: 14px; line-height: 1.6; padding: 0;"
                placeholder="Start typing...">
            </textarea>
        `;

        const textarea = contentDiv.querySelector('textarea');
        textarea.addEventListener('input', (e) => {
            this.handleContentChange(e.target.value);
        });

        // Hide toolbar for fallback
        const toolbar = document.querySelector(`#${this.containerId} .live-editor-toolbar`);
        if (toolbar) {
            toolbar.style.display = 'none';
        }
        
        console.log('⚠️ Using fallback editor (Tiptap not available)');
    }

    /**
     * Toolbar setup
     */
    setupToolbar() {
        const toolbar = document.querySelector(`#${this.containerId} .live-editor-toolbar`);
        if (!toolbar || !this.editor) return;

        const toolButtons = toolbar.querySelectorAll('.editor-tool-btn');
        
        toolButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                const tool = button.dataset.tool;
                this.executeTool(tool);
            });
        });
    }

    /**
     * Editor tool'larını execute et
     */
    executeTool(tool) {
        if (!this.editor) return;

        switch (tool) {
            case 'bold':
                this.editor.chain().focus().toggleBold().run();
                break;
            case 'italic':
                this.editor.chain().focus().toggleItalic().run();
                break;
            case 'heading1':
                this.editor.chain().focus().toggleHeading({ level: 1 }).run();
                break;
            case 'heading2':
                this.editor.chain().focus().toggleHeading({ level: 2 }).run();
                break;
            case 'bulletList':
                this.editor.chain().focus().toggleBulletList().run();
                break;
            case 'orderedList':
                this.editor.chain().focus().toggleOrderedList().run();
                break;
            case 'blockquote':
                this.editor.chain().focus().toggleBlockquote().run();
                break;
            case 'code':
                this.editor.chain().focus().toggleCode().run();
                break;
        }

        this.updateToolbarState(this.editor);
    }

    /**
     * Toolbar state'ini güncelle
     */
    updateToolbarState(editor) {
        const toolbar = document.querySelector(`#${this.containerId} .live-editor-toolbar`);
        if (!toolbar) return;

        const buttons = toolbar.querySelectorAll('.editor-tool-btn');
        
        buttons.forEach(button => {
            const tool = button.dataset.tool;
            let isActive = false;

            switch (tool) {
                case 'bold':
                    isActive = editor.isActive('bold');
                    break;
                case 'italic':
                    isActive = editor.isActive('italic');
                    break;
                case 'heading1':
                    isActive = editor.isActive('heading', { level: 1 });
                    break;
                case 'heading2':
                    isActive = editor.isActive('heading', { level: 2 });
                    break;
                case 'bulletList':
                    isActive = editor.isActive('bulletList');
                    break;
                case 'orderedList':
                    isActive = editor.isActive('orderedList');
                    break;
                case 'blockquote':
                    isActive = editor.isActive('blockquote');
                    break;
                case 'code':
                    isActive = editor.isActive('code');
                    break;
            }

            button.classList.toggle('active', isActive);
        });
    }

    /**
     * WebSocket listeners setup
     */
    setupWebSocketListeners() {
        if (!this.socket) return;

        this.socket.on('document_updated', (data) => {
            if (data.window_id === this.windowId) {
                this.handleRemoteContentChange(data.content);
            }
        });

        this.socket.on('collaborator_joined', (data) => {
            if (data.window_id === this.windowId) {
                this.addCollaborator(data.user);
            }
        });

        this.socket.on('collaborator_left', (data) => {
            if (data.window_id === this.windowId) {
                this.removeCollaborator(data.user_id);
            }
        });

        this.socket.on('connection_status', (data) => {
            this.updateConnectionStatus(data.status);
        });

        // PHASE 6.1: Multi-user collaboration events
        this.socket.on('user_joined', (data) => {
            this.userInfo = data.user;
            this.updateUserPresence(data.users_in_room);
            console.log('👥 Joined document room:', data);
        });

        this.socket.on('user_joined_room', (data) => {
            this.updateUserPresence(data.users_in_room);
            console.log('👤 New user joined:', data.user);
        });

        this.socket.on('user_left_room', (data) => {
            this.updateUserPresence(data.users_in_room);
            this.removeRemoteCursor(data.user_id);
            console.log('👋 User left:', data.user_name);
        });

        this.socket.on('cursor_updated', (data) => {
            this.updateRemoteCursor(data);
        });

        this.socket.on('selection_updated', (data) => {
            this.updateRemoteSelection(data);
        });
    }

    /**
     * Content değişikliklerini handle et
     */
    handleContentChange(content) {
        if (content === this.lastSavedContent) return;

        this.updateConnectionStatus('saving');
        
        // Debounced save
        clearTimeout(this.saveTimeout);
        this.saveTimeout = setTimeout(() => {
            this.saveContent(content);
        }, 500);
    }

    /**
     * Remote content değişikliklerini handle et
     */
    handleRemoteContentChange(content) {
        if (!this.editor || content === this.lastSavedContent) return;

        // Prevent infinite loop
        this.lastSavedContent = content;
        
        // Update editor content without triggering update event
        this.editor.commands.setContent(content, false);
    }

    /**
     * İçeriği kaydet (WebSocket ile backend'e gönder)
     */
    saveContent(content) {
        if (!this.socket) return;

        this.socket.emit('document_change', {
            window_id: this.windowId,
            document_id: this.documentId,
            content: content,
            timestamp: Date.now()
        });

        this.lastSavedContent = content;
        this.updateConnectionStatus('connected');
    }

    /**
     * Auto-save setup
     */
    setupAutoSave() {
        // Save every 30 seconds
        setInterval(() => {
            if (this.editor) {
                const content = this.editor.getHTML();
                if (content !== this.lastSavedContent) {
                    this.saveContent(content);
                }
            }
        }, 30000);
    }

    /**
     * Connection status güncelle
     */
    updateConnectionStatus(status) {
        const statusElement = document.getElementById(`status-${this.windowId}`);
        if (statusElement) {
            statusElement.className = `canvas-status ${status}`;
        }

        // Update window manager status
        if (window.canvasManager) {
            window.canvasManager.updateWindowStatus(this.windowId, status);
        }
    }

    /**
     * Collaborator ekle
     */
    addCollaborator(user) {
        this.collaborators.set(user.id, user);
        console.log(`👥 Collaborator joined: ${user.name}`);
    }

    /**
     * Collaborator kaldır
     */
    removeCollaborator(userId) {
        this.collaborators.delete(userId);
        console.log(`👥 Collaborator left: ${userId}`);
    }

    /**
     * User color generate et
     */
    generateUserColor() {
        const colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#FF9FF3', '#54A0FF'];
        return colors[Math.floor(Math.random() * colors.length)];
    }

    /**
     * Collaboration provider oluştur (Yjs integration için)
     */
    createCollaborationProvider() {
        // Placeholder for Yjs provider
        return {
            on: () => {},
            off: () => {},
            emit: () => {}
        };
    }

    /**
     * Document ID set et
     */
    setDocumentId(documentId) {
        this.documentId = documentId;
    }

    /**
     * Editor content al
     */
    getContent() {
        if (this.editor) {
            return this.editor.getHTML();
        }
        
        // Fallback editor
        const textarea = document.querySelector(`#content-${this.windowId} textarea`);
        return textarea ? textarea.value : '';
    }

    /**
     * Editor content set et
     */
    setContent(content) {
        if (this.editor) {
            this.editor.commands.setContent(content);
        } else {
            // Fallback editor
            const textarea = document.querySelector(`#content-${this.windowId} textarea`);
            if (textarea) {
                textarea.value = content;
            }
        }
        
        this.lastSavedContent = content;
    }

    /**
     * Error göster
     */
    showError(message) {
        const container = document.getElementById(this.containerId);
        if (container) {
            container.innerHTML = `
                <div style="padding: 20px; text-align: center; color: #ef4444;">
                    <p>⚠️ ${message}</p>
                    <button onclick="location.reload()" style="margin-top: 10px; padding: 8px 16px; background: #3b82f6; color: white; border: none; border-radius: 4px; cursor: pointer;">
                        Retry
                    </button>
                </div>
            `;
        }
    }

    /**
     * Cleanup
     */
    destroy() {
        // Leave document room if joined
        if (this.isJoinedDocument && this.socket && this.documentId) {
            this.socket.emit('leave_document', { document_id: this.documentId });
        }
        
        if (this.editor) {
            this.editor.destroy();
        }
        
        if (this.socket) {
            // Phase 6.1 events cleanup
            this.socket.off('user_joined');
            this.socket.off('user_joined_room');
            this.socket.off('user_left_room');
            this.socket.off('cursor_updated');
            this.socket.off('selection_updated');
        }
        
        clearTimeout(this.saveTimeout);
        clearTimeout(this.mouseMoveThrottle);
        this.collaborators.clear();
        this.currentUsers.clear();
        this.remoteCursors.clear();
        
        console.log(`🧹 LiveEditor destroyed: ${this.windowId}`);
    }

    // PHASE 6.1: Multi-user Collaboration Methods
    
    /**
     * Document room'a katıl
     */
    joinDocument(documentId) {
        if (!this.socket || !documentId) return;
        
        this.documentId = documentId;
        this.socket.emit('join_document', {
            document_id: documentId,
            user_name: this.userInfo.name
        });
        this.isJoinedDocument = true;
        
        // Setup mouse tracking
        this.setupMouseTracking();
    }

    /**
     * Mouse tracking setup et
     */
    setupMouseTracking() {
        const editorElement = document.getElementById(`content-${this.windowId}`);
        if (!editorElement) return;

        editorElement.addEventListener('mousemove', (e) => {
            // Throttle mouse movements
            if (this.mouseMoveThrottle) return;
            
            this.mouseMoveThrottle = setTimeout(() => {
                this.mouseMoveThrottle = null;
                
                if (this.socket && this.documentId && this.isJoinedDocument) {
                    const rect = editorElement.getBoundingClientRect();
                    const position = {
                        x: e.clientX - rect.left,
                        y: e.clientY - rect.top,
                        relativeX: (e.clientX - rect.left) / rect.width,
                        relativeY: (e.clientY - rect.top) / rect.height
                    };
                    
                    this.socket.emit('cursor_moved', {
                        document_id: this.documentId,
                        position: position
                    });
                }
            }, 50); // 50ms throttle
        });
    }

    /**
     * User presence UI güncellemesi
     */
    updateUserPresence(users) {
        const presenceElement = document.getElementById(`presence-${this.windowId}`);
        if (!presenceElement) return;

        // Clear current users
        this.currentUsers.clear();
        
        // Update users
        users.forEach(user => this.currentUsers.set(user.session_id, user));

        // Render presence indicators
        presenceElement.innerHTML = users.map(user => `
            <div class="user-avatar" style="background-color: ${user.color};" title="${user.name}">
                ${user.name.charAt(0).toUpperCase()}
            </div>
        `).join('');

        // Update window title if current user is in list
        const currentUser = users.find(u => u.session_id === this.userInfo.session_id);
        if (currentUser && window.canvasManager) {
            const userCount = users.length;
            const title = userCount > 1 ? `Document (${userCount} users)` : 'Document';
            window.canvasManager.updateWindowTitle(this.windowId, title);
        }
    }

    /**
     * Remote cursor güncelle
     */
    updateRemoteCursor(data) {
        const cursorsContainer = document.getElementById(`cursors-${this.windowId}`);
        if (!cursorsContainer) return;

        let cursorElement = cursorsContainer.querySelector(`[data-user-id="${data.user_id}"]`);
        
        if (!cursorElement) {
            cursorElement = document.createElement('div');
            cursorElement.className = 'remote-cursor';
            cursorElement.setAttribute('data-user-id', data.user_id);
            cursorElement.innerHTML = `
                <div class="cursor-pointer" style="border-left-color: ${data.user_color};"></div>
                <div class="cursor-label" style="background-color: ${data.user_color};">${data.user_name}</div>
            `;
            cursorsContainer.appendChild(cursorElement);
        }

        // Update position
        const position = data.position;
        cursorElement.style.left = `${position.x}px`;
        cursorElement.style.top = `${position.y}px`;
        cursorElement.style.display = 'block';

        // Store cursor reference
        this.remoteCursors.set(data.user_id, cursorElement);

        // Hide cursor after inactivity
        clearTimeout(cursorElement.hideTimeout);
        cursorElement.hideTimeout = setTimeout(() => {
            cursorElement.style.display = 'none';
        }, 3000);
    }

    /**
     * Remote cursor kaldır
     */
    removeRemoteCursor(userId) {
        const cursorsContainer = document.getElementById(`cursors-${this.windowId}`);
        if (!cursorsContainer) return;

        const cursorElement = cursorsContainer.querySelector(`[data-user-id="${userId}"]`);
        if (cursorElement) {
            cursorElement.remove();
        }

        this.remoteCursors.delete(userId);
    }

    /**
     * Remote selection güncelle
     */
    updateRemoteSelection(data) {
        // TODO: Implement text selection highlighting
        console.log('Remote selection updated:', data);
    }

    /**
     * Aktif kullanıcı sayısını al
     */
    getActiveUserCount() {
        return this.currentUsers.size;
    }

    /**
     * User info güncelle
     */
    updateUserInfo(name, color) {
        this.userInfo.name = name;
        this.userInfo.color = color || this.userInfo.color;
    }

    // PHASE 6.2: Document Conflict Resolution Methods

    /**
     * Initialize Operational Transform engine
     */
    initializeOTEngine() {
        if (typeof window.OperationalTransform !== 'undefined') {
            this.otEngine = new window.OperationalTransform();
            this.setupOTWebSocketListeners();
            console.log('🧠 OT Engine initialized for LiveEditor');
        } else {
            console.warn('⚠️ OperationalTransform not available, using fallback sync');
        }
    }

    /**
     * Handle local content changes with OT
     */
    handleLocalContentChange(newContent) {
        if (this.isApplyingRemoteChanges) {
            return;
        }

        if (!this.otEngine) {
            this.handleContentChange(newContent);
            return;
        }

        const operations = this.calculateContentDiff(this.lastContent, newContent);
        
        if (operations.length > 0) {
            console.log('📝 Local content changed, operations:', operations);
            
            operations.forEach(op => {
                this.otEngine.sendOperation(op, (operation) => {
                    this.sendOperationToServer(operation);
                });
            });
        }

        this.lastContent = newContent;
    }

    /**
     * Calculate content diff to generate operations
     */
    calculateContentDiff(oldContent, newContent) {
        const operations = [];
        
        if (oldContent === newContent) {
            return operations;
        }

        // Simple diff algorithm
        let i = 0;
        while (i < Math.min(oldContent.length, newContent.length) && 
               oldContent[i] === newContent[i]) {
            i++;
        }

        const prefixLength = i;

        let oldSuffix = oldContent.length - 1;
        let newSuffix = newContent.length - 1;
        
        while (oldSuffix >= prefixLength && 
               newSuffix >= prefixLength && 
               oldContent[oldSuffix] === newContent[newSuffix]) {
            oldSuffix--;
            newSuffix--;
        }

        const deletedLength = oldSuffix - prefixLength + 1;
        const insertedText = newContent.slice(prefixLength, newSuffix + 1);

        if (deletedLength > 0) {
            operations.push(window.OperationalTransform.delete(prefixLength, deletedLength));
        }

        if (insertedText.length > 0) {
            operations.push(window.OperationalTransform.insert(insertedText, prefixLength));
        }

        return operations;
    }

    /**
     * Send operation to server
     */
    sendOperationToServer(operation) {
        if (this.socket && this.isJoinedDocument) {
            this.socket.emit('document_operation', {
                document_id: this.documentId,
                operation: operation,
                user_id: this.socket.id,
                user_name: this.userInfo.name
            });
        }
    }

    /**
     * Handle remote operation
     */
    handleRemoteOperation(data) {
        if (!this.otEngine) {
            return;
        }

        try {
            const result = this.otEngine.receiveOperation(data.operation, data.user_id);
            this.applyRemoteContentChange(result.newContent);
            
            const conflict = this.otEngine.detectConflict(
                data.operation, 
                this.operationBuffer[this.operationBuffer.length - 1]
            );
            
            if (conflict.hasConflict) {
                this.handleConflict(conflict);
            }
            
        } catch (error) {
            console.error('❌ Error handling remote operation:', error);
        }
    }

    /**
     * Apply remote content changes
     */
    applyRemoteContentChange(newContent) {
        this.isApplyingRemoteChanges = true;
        
        try {
            if (this.editor && this.editor.setContent) {
                this.editor.setContent(newContent);
            } else {
                const textarea = document.querySelector(`#content-${this.windowId} textarea`);
                if (textarea) {
                    textarea.value = newContent;
                }
            }
            
            this.lastContent = newContent;
            
        } finally {
            this.isApplyingRemoteChanges = false;
        }
    }

    /**
     * Handle conflicts
     */
    handleConflict(conflict) {
        console.warn('⚠️ Conflict detected:', conflict);
        this.showConflictDialog(conflict);
    }

    /**
     * Show conflict dialog
     */
    showConflictDialog(conflict) {
        const conflictDialog = document.createElement('div');
        conflictDialog.className = 'conflict-dialog';
        conflictDialog.innerHTML = `
            <div class="conflict-dialog-content">
                <h3>🔥 Document Conflict</h3>
                <p><strong>Type:</strong> ${conflict.type}</p>
                <p><strong>Description:</strong> ${conflict.description}</p>
                <div class="conflict-actions">
                    <button onclick="this.parentElement.parentElement.parentElement.remove()" class="btn btn-secondary">
                        Dismiss
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(conflictDialog);
        
        setTimeout(() => {
            if (conflictDialog.parentNode) {
                conflictDialog.remove();
            }
        }, 10000);
    }

    /**
     * Setup OT WebSocket listeners
     */
    setupOTWebSocketListeners() {
        if (!this.socket) return;

        this.socket.on('remote_operation', (data) => {
            this.handleRemoteOperation(data);
        });

        this.socket.on('operation_ack', (data) => {
            if (this.otEngine) {
                this.otEngine.acknowledgeOperation(data.operation_id);
            }
        });

        this.socket.on('conflict_detected', (data) => {
            this.handleConflict(data.conflict);
        });
    }
}

// Global export
window.LiveEditor = LiveEditor; 