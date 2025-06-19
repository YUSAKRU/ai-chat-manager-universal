/**
 * 🚀 AI ORCHESTRATOR MAIN APPLICATION v2.0
 * Modern UI interactions and enhanced functionality
 */

class AIOrchestrator {
    constructor() {
        this.socket = null;
        this.isConnected = false;
        this.currentConversation = [];
        this.activeSpecialists = [];
        this.analytics = {
            totalCost: 0,
            totalRequests: 0,
            successRate: 100,
            avgResponse: 0,
            tokens: {
                input: 0,
                output: 0,
                total: 0
            }
        };
        
        this.init();
    }

    /**
     * Initialize the orchestrator
     */
    init() {
        this.setupSocketConnection();
        this.bindEventListeners();
        this.startPeriodicUpdates();
        
        console.log('🚀 AI Orchestrator v2.0 initialized');
    }

    /**
     * Setup WebSocket connection
     */
    setupSocketConnection() {
        if (typeof io !== 'undefined') {
            this.socket = io();
            
            this.socket.on('connect', () => {
                this.isConnected = true;
                this.updateConnectionStatus(true);
                console.log('🔗 Socket connected');
            });

            this.socket.on('disconnect', () => {
                this.isConnected = false;
                this.updateConnectionStatus(false);
                console.log('🔌 Socket disconnected');
            });

            this.socket.on('analytics_update', (data) => {
                this.updateAnalytics(data);
            });

            this.socket.on('specialist_update', (data) => {
                this.updateSpecialists(data);
            });

            this.socket.on('conversation_update', (data) => {
                this.handleConversationUpdate(data);
            });
        }
    }

    /**
     * Bind event listeners
     */
    bindEventListeners() {
        // Tab switching with analytics refresh
        document.querySelectorAll('[data-bs-toggle="tab"]').forEach(tab => {
            tab.addEventListener('shown.bs.tab', (e) => {
                const targetId = e.target.getAttribute('data-bs-target');
                if (targetId === '#analytics') {
                    this.refreshAnalytics();
                }
            });
        });

        // Enhanced form submissions
        this.bindFormSubmissions();
        
        // Analytics interactions
        this.bindAnalyticsEvents();
        
        // Navigation enhancements
        this.bindNavigationEvents();
    }

    /**
     * Bind form submission handlers
     */
    bindFormSubmissions() {
        // Chat form
        const chatForm = document.getElementById('chat-form');
        if (chatForm) {
            chatForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleChatSubmission();
            });
        }

        // Message input with advanced features
        const messageInput = document.getElementById('messageInput');
        if (messageInput) {
            messageInput.addEventListener('input', (e) => {
                this.handleInputChange(e.target.value);
            });

            messageInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    if (e.target.closest('#chatContainer')) {
                        this.sendMessage();
                    } else {
                        this.handleChatSubmission();
                    }
                }
            });
        }
    }

    /**
     * Bind analytics events
     */
    bindAnalyticsEvents() {
        // Metric cards click handlers
        document.querySelectorAll('.metric-card').forEach(card => {
            card.addEventListener('click', () => {
                const type = card.classList.contains('cost') ? 'cost' :
                           card.classList.contains('requests') ? 'requests' :
                           card.classList.contains('success') ? 'success' : 'speed';
                this.showDetailedMetrics(type);
            });
        });

        // Token usage chart interactions
        const tokenChart = document.querySelector('.card-modern[data-animate]');
        if (tokenChart) {
            tokenChart.addEventListener('click', () => {
                this.showTokenBreakdown();
            });
        }
    }

    /**
     * Bind navigation events
     */
    bindNavigationEvents() {
        // Enhanced navbar interactions
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                // Add visual feedback
                if (window.animationUtils) {
                    window.animationUtils.pulse(e.target);
                }
            });
        });

        // Button enhancements
        document.querySelectorAll('.btn-modern').forEach(btn => {
            btn.addEventListener('mouseenter', (e) => {
                if (window.animationUtils) {
                    window.animationUtils.addHoverGlow(e.target);
                }
            });

            btn.addEventListener('mouseleave', (e) => {
                if (window.animationUtils) {
                    window.animationUtils.removeHoverGlow(e.target);
                }
            });
        });
    }

    /**
     * Handle chat form submission
     */
    async handleChatSubmission() {
        const chatInput = document.getElementById('chat-input');
        if (!chatInput) return;

        const message = chatInput.value.trim();
        if (!message) return;

        // Clear input and add message
        chatInput.value = '';
        this.addChatMessage(message, 'user');

        // Show typing indicator
        this.showTypingIndicator();

        try {
            // Simulate AI processing
            await new Promise(resolve => setTimeout(resolve, 1500));
            
            // Add AI response
            const responses = [
                "Bu gerçekten ilginç bir yaklaşım! Bu konuda daha detayına inelim.",
                "Harika bir proje fikri! Hemen teknik detayları planlamaya başlayalım.",
                "Bu konuda uzman ekibimi devreye sokacağım. Kapsamlı bir analiz yapalım.",
                "Mükemmel! Bu projeyi aşama aşama geliştirme stratejisi oluşturabiliriz."
            ];
            
            const randomResponse = responses[Math.floor(Math.random() * responses.length)];
            this.addChatMessage(randomResponse, 'assistant');
            
            // Update analytics
            this.incrementAnalytics();
            
        } catch (error) {
            console.error('Chat error:', error);
            this.addChatMessage('Üzgünüm, bir hata oluştu. Lütfen tekrar deneyin.', 'assistant');
        } finally {
            this.hideTypingIndicator();
        }
    }

    /**
     * Add message to chat
     */
    addChatMessage(message, type) {
        const messagesContainer = document.getElementById('chat-messages');
        if (!messagesContainer) return;

        // Clear empty state
        const emptyState = messagesContainer.querySelector('.text-center');
        if (emptyState) {
            messagesContainer.innerHTML = '';
        }

        const messageElement = document.createElement('div');
        messageElement.className = `message-bubble ${type} mb-3`;
        messageElement.innerHTML = `
            <div class="message-header">
                ${type === 'user' ? '👤 Siz' : '🤖 AI Assistant'}
            </div>
            <div class="message-content">${message}</div>
            <div class="message-time">${new Date().toLocaleTimeString()}</div>
        `;

        messagesContainer.appendChild(messageElement);

        // Animate message
        if (window.animationUtils) {
            window.animationUtils.animateMessage(messageElement, type);
        }

        // Scroll to bottom
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    /**
     * Show typing indicator
     */
    showTypingIndicator() {
        const messagesContainer = document.getElementById('chat-messages');
        if (!messagesContainer) return;

        const typingDiv = document.createElement('div');
        typingDiv.id = 'typing-indicator';
        typingDiv.className = 'thinking-indicator mb-3';
        typingDiv.innerHTML = `
            <div class="loading-dots">
                <span></span>
                <span></span>
                <span></span>
            </div>
            <span>AI düşünüyor...</span>
        `;

        messagesContainer.appendChild(typingDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    /**
     * Hide typing indicator
     */
    hideTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    /**
     * Update connection status
     */
    updateConnectionStatus(isConnected) {
        const statusDot = document.getElementById('status-indicator');
        const statusText = document.getElementById('connection-status');

        if (statusDot && statusText) {
            if (isConnected) {
                statusDot.className = 'status-dot online';
                statusText.textContent = 'Bağlı';
            } else {
                statusDot.className = 'status-dot offline';
                statusText.textContent = 'Bağlantı Kesildi';
            }
        }
    }

    /**
     * Update analytics data
     */
    updateAnalytics(data) {
        if (data) {
            Object.assign(this.analytics, data);
        }

        // Update UI elements
        this.updateMetricCards();
        this.updateTokenChart();
        this.updatePerformanceCharts();
    }

    /**
     * Update metric cards
     */
    updateMetricCards() {
        const elements = {
            'total-cost': `$${this.analytics.totalCost.toFixed(2)}`,
            'total-requests': this.analytics.totalRequests.toLocaleString(),
            'success-rate': `${this.analytics.successRate}%`,
            'avg-response': `${this.analytics.avgResponse.toFixed(1)}s`
        };

        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                // Animate number changes
                if (window.animationUtils && !isNaN(parseFloat(value))) {
                    window.animationUtils.countUp(element, 0, parseFloat(value), 1000);
                } else {
                    element.textContent = value;
                }
            }
        });

        // Update change indicators
        this.updateChangeIndicators();
    }

    /**
     * Update change indicators
     */
    updateChangeIndicators() {
        const changes = {
            'cost-change': '+12% bu ay',
            'requests-change': `${Math.floor(this.analytics.totalRequests / 60)} RPM`,
            'error-count': '0 hata',
            'fastest-model': 'Gemini 2.0 Flash'
        };

        Object.entries(changes).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value;
            }
        });
    }

    /**
     * Update token chart
     */
    updateTokenChart() {
        const { input, output, total } = this.analytics.tokens;
        
        const inputPercentage = total > 0 ? (input / total * 100).toFixed(0) : 0;
        const outputPercentage = total > 0 ? (output / total * 100).toFixed(0) : 0;

        const elements = {
            'total-tokens': total.toLocaleString(),
            'input-tokens': input.toLocaleString(),
            'output-tokens': output.toLocaleString(),
            'input-percentage': `${inputPercentage}%`,
            'output-percentage': `${outputPercentage}%`
        };

        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value;
            }
        });

        // Update progress bars
        const progressInput = document.getElementById('progress-input');
        const progressOutput = document.getElementById('progress-output');

        if (progressInput && progressOutput) {
            progressInput.style.width = `${inputPercentage}%`;
            progressOutput.style.width = `${outputPercentage}%`;
            progressInput.textContent = `${inputPercentage}%`;
            progressOutput.textContent = `${outputPercentage}%`;
        }
    }

    /**
     * Increment analytics for demo
     */
    incrementAnalytics() {
        this.analytics.totalRequests += 1;
        this.analytics.totalCost += Math.random() * 0.05;
        this.analytics.avgResponse = (Math.random() * 2 + 0.5);
        this.analytics.tokens.input += Math.floor(Math.random() * 100 + 50);
        this.analytics.tokens.output += Math.floor(Math.random() * 200 + 100);
        this.analytics.tokens.total = this.analytics.tokens.input + this.analytics.tokens.output;

        this.updateAnalytics();
    }

    /**
     * Refresh analytics data
     */
    async refreshAnalytics() {
        // Simulate loading
        const metricCards = document.querySelectorAll('.metric-card');
        metricCards.forEach(card => {
            card.style.opacity = '0.7';
        });

        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 500));

        // Restore and update
        metricCards.forEach(card => {
            card.style.opacity = '1';
        });

        this.updateAnalytics();
    }

    /**
     * Show detailed metrics
     */
    showDetailedMetrics(type) {
        console.log(`Showing detailed metrics for: ${type}`);
        
        // Create modal or detailed view
        const modalContent = {
            cost: 'Detaylı maliyet analizi',
            requests: 'API istek detayları',
            success: 'Başarı oranı metrikleri',
            speed: 'Performans analizi'
        };

        if (window.animationUtils) {
            // Show toast notification for demo
            const toastTitle = modalContent[type] || 'Detaylar';
            this.showNotification(toastTitle, 'Detaylı görünüm geliştiriliyor...');
        }
    }

    /**
     * Show token breakdown
     */
    showTokenBreakdown() {
        console.log('Showing token breakdown');
        this.showNotification('Token Analizi', 'Detaylı token kullanım analizi gösteriliyor...');
    }

    /**
     * Show notification
     */
    showNotification(title, message, type = 'info') {
        // Create and show a modern notification
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        notification.style.cssText = `
            top: 20px;
            right: 20px;
            z-index: 1080;
            min-width: 300px;
            box-shadow: var(--shadow-lg);
        `;
        
        notification.innerHTML = `
            <strong>${title}</strong>
            <div>${message}</div>
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        document.body.appendChild(notification);

        // Auto remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }

    /**
     * Handle input changes with suggestions
     */
    handleInputChange(value) {
        // Implement smart suggestions based on input
        if (value.length > 3) {
            this.suggestActions(value);
        }
    }

    /**
     * Suggest actions based on input
     */
    suggestActions(input) {
        const suggestions = {
            'proje': ['Yeni proje oluştur', 'Proje planı hazırla', 'Ekip atamaları yap'],
            'mobil': ['Mobil uygulama tasarla', 'React Native kurulu', 'App store stratejisi'],
            'web': ['Web sitesi oluştur', 'Frontend framework seç', 'Backend API tasarla'],
            'api': ['REST API tasarla', 'GraphQL şeması oluştur', 'API dokümantasyonu'],
            'database': ['Veritabanı tasarla', 'Schema oluştur', 'Optimizasyon önerileri']
        };

        const lowerInput = input.toLowerCase();
        for (const [keyword, actions] of Object.entries(suggestions)) {
            if (lowerInput.includes(keyword)) {
                this.showSuggestions(actions);
                break;
            }
        }
    }

    /**
     * Show action suggestions
     */
    showSuggestions(suggestions) {
        // Implementation for showing smart suggestions
        console.log('Suggestions:', suggestions);
    }

    /**
     * Start periodic updates
     */
    startPeriodicUpdates() {
        // Update analytics every 30 seconds
        setInterval(() => {
            if (this.isConnected) {
                this.refreshAnalytics();
            }
        }, 30000);

        // Update connection status every 5 seconds
        setInterval(() => {
            this.updateConnectionStatus(this.isConnected);
        }, 5000);
    }

    /**
     * Update performance charts
     */
    updatePerformanceCharts() {
        // Generate AI performance cards
        const container = document.getElementById('ai-cards-container');
        if (!container) return;

        const aiModels = [
            { name: 'Gemini 2.0 Flash', status: 'active', cost: 0.02, speed: 1.2 },
            { name: 'Gemini Pro', status: 'active', cost: 0.05, speed: 2.1 },
            { name: 'OpenAI GPT-4', status: 'standby', cost: 0.08, speed: 3.5 }
        ];

        container.innerHTML = '';
        aiModels.forEach((model, index) => {
            const card = document.createElement('div');
            card.className = 'col-12';
            card.innerHTML = `
                <div class="ai-card" data-animate="fadeInUp" data-delay="${(index + 1) * 100}">
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <h6 class="mb-0">${model.name}</h6>
                        <span class="badge ${model.status === 'active' ? 'bg-success' : 'bg-secondary'}">${model.status}</span>
                    </div>
                    <div class="row text-center">
                        <div class="col-6">
                            <div class="text-sm text-secondary">Maliyet</div>
                            <div class="font-semibold">$${model.cost.toFixed(3)}</div>
                        </div>
                        <div class="col-6">
                            <div class="text-sm text-secondary">Hız</div>
                            <div class="font-semibold">${model.speed}s</div>
                        </div>
                    </div>
                </div>
            `;
            container.appendChild(card);
        });

        // Trigger animations
        if (window.animationUtils) {
            const cards = container.querySelectorAll('.ai-card');
            window.animationUtils.staggerAnimation(cards, 'bounce-in', 100);
        }
    }
}

// Global functions for backward compatibility
window.showMemoryModal = function() {
    if (window.orchestrator) {
        window.orchestrator.showNotification('Hafıza', 'Konuşma geçmişi modalı geliştiriliyor...');
    }
};

window.showTasksModal = function() {
    if (window.orchestrator) {
        window.orchestrator.showNotification('Görevler', 'Görev listesi modalı geliştiriliyor...');
    }
};

window.startAIConversation = function() {
    if (window.orchestrator) {
        window.orchestrator.showNotification('AI Konuşması', 'Uzman koordinasyonu başlatılıyor...');
    }
};

window.pauseConversation = function() {
    if (window.orchestrator) {
        window.orchestrator.showNotification('Duraklat', 'Konuşma duraklatıldı.');
    }
};

window.clearConversation = function() {
    const messagesContainer = document.getElementById('live-chat-messages') || document.getElementById('chat-messages');
    if (messagesContainer) {
        messagesContainer.innerHTML = `
            <div class="text-center text-muted p-5">
                <div class="floating">
                    <i class="bi bi-robot" style="font-size: 48px; opacity: 0.3;"></i>
                </div>
                <p class="mt-3 mb-0">Konuşma temizlendi.</p>
                <small class="text-muted">Yeni bir konuşma başlatabilirsiniz.</small>
            </div>
        `;
    }
};

window.startConversation = function() {
    if (window.orchestrator) {
        window.orchestrator.showNotification('Yeni Konuşma', 'Yeni konuşma başlatılıyor...');
    }
};

window.clearHistory = function() {
    if (window.orchestrator) {
        window.orchestrator.showNotification('Geçmiş', 'Konuşma geçmişi temizlendi.');
    }
};

window.toggleInterventionPanel = function() {
    if (window.orchestrator) {
        window.orchestrator.showNotification('Müdahale', 'Yönetici müdahale paneli geliştiriliyor...');
    }
};

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.orchestrator = new AIOrchestrator();
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AIOrchestrator;
} 