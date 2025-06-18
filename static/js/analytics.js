/**
 * Analytics Dashboard - Real-time Updates
 */

// SocketIO bağlantısı
const socket = io();

// Analytics verileri için global state
let analyticsData = {
    summary: {
        total_cost: 0,
        total_requests: 0,
        success_rate: 100,
        avg_response_time: 0,
        total_tokens: 0,
        total_errors: 0
    },
    adapters: {},
    token_usage: {
        total: 0,
        input: 0,
        output: 0
    }
};

// SocketIO event listeners
socket.on('connect', () => {
    console.log('Connected to server');
    updateConnectionStatus(true);
    // İlk bağlantıda analytics verilerini iste
    socket.emit('request_analytics');
});

socket.on('disconnect', () => {
    console.log('Disconnected from server');
    updateConnectionStatus(false);
});

socket.on('analytics_update', (data) => {
    console.log('Analytics update received:', data);
    analyticsData = data;
    updateAnalyticsDashboard();
});

socket.on('ai_response', (data) => {
    console.log('AI response received:', data);
    addChatMessage(data);
});

socket.on('conversation_message', (data) => {
    console.log('Conversation message:', data);
    addConversationMessage(data);
});

socket.on('conversation_started', (data) => {
    console.log('Conversation started:', data);
    clearChatMessages();
    addSystemMessage('Konuşma başlatıldı: ' + data.prompt);
});

socket.on('conversation_completed', (data) => {
    console.log('Conversation completed:', data);
    addSystemMessage('Konuşma tamamlandı. Toplam tur: ' + data.total_turns);
});

socket.on('conversation_error', (data) => {
    console.error('Conversation error:', data);
    addSystemMessage('Hata: ' + data.error, 'error');
});

// Analytics Dashboard güncelleme fonksiyonları
function updateAnalyticsDashboard() {
    updatePrimaryMetrics();
    updateTokenUsage();
    updateAICards();
}

function updatePrimaryMetrics() {
    const summary = analyticsData.summary;
    
    // Toplam Maliyet
    document.getElementById('total-cost').textContent = `$${summary.total_cost.toFixed(2)}`;
    document.getElementById('cost-change').textContent = summary.total_cost > 0 ? 'Aktif' : 'Başlangıç';
    
    // Toplam İstek
    document.getElementById('total-requests').textContent = summary.total_requests.toString();
    const rpm = calculateRPM();
    document.getElementById('requests-change').textContent = `${rpm} RPM`;
    
    // Başarı Oranı
    document.getElementById('success-rate').textContent = `${summary.success_rate}%`;
    document.getElementById('error-count').textContent = `${summary.total_errors} hata`;
    if (summary.total_errors > 0) {
        document.getElementById('error-count').classList.add('negative');
    } else {
        document.getElementById('error-count').classList.remove('negative');
    }
    
    // Ortalama Yanıt
    document.getElementById('avg-response').textContent = `${summary.avg_response_time.toFixed(1)}s`;
    
    // En hızlı model
    const fastestModel = getFastestModel();
    document.getElementById('fastest-model').textContent = fastestModel || 'Bekleniyor';
}

function updateTokenUsage() {
    const tokenUsage = analyticsData.token_usage;
    const total = tokenUsage.total || 1; // Division by zero koruması
    
    // Token sayıları
    document.getElementById('total-tokens').textContent = tokenUsage.total.toLocaleString();
    document.getElementById('input-tokens').textContent = tokenUsage.input.toLocaleString();
    document.getElementById('output-tokens').textContent = tokenUsage.output.toLocaleString();
    
    // Yüzdeler
    const inputPercentage = Math.round((tokenUsage.input / total) * 100);
    const outputPercentage = Math.round((tokenUsage.output / total) * 100);
    
    document.getElementById('input-percentage').textContent = `${inputPercentage}%`;
    document.getElementById('output-percentage').textContent = `${outputPercentage}%`;
    
    // Progress bar
    document.getElementById('progress-input').style.width = `${inputPercentage}%`;
    document.getElementById('progress-output').style.width = `${outputPercentage}%`;
    
    // Progress bar içindeki yazılar
    if (inputPercentage > 10) {
        document.getElementById('progress-input').textContent = `${inputPercentage}%`;
    } else {
        document.getElementById('progress-input').textContent = '';
    }
    
    if (outputPercentage > 10) {
        document.getElementById('progress-output').textContent = `${outputPercentage}%`;
    } else {
        document.getElementById('progress-output').textContent = '';
    }
}

function updateAICards() {
    const container = document.getElementById('ai-cards-container');
    container.innerHTML = '';
    
    // Her adapter için kart oluştur
    Object.values(analyticsData.adapters).forEach(adapter => {
        const card = createAICard(adapter);
        container.appendChild(card);
    });
    
    // Eğer adapter yoksa
    if (Object.keys(analyticsData.adapters).length === 0) {
        container.innerHTML = `
            <div class="col-12 text-center text-muted p-5">
                <i class="bi bi-robot" style="font-size: 48px;"></i>
                <p class="mt-3">Henüz AI adapter tanımlı değil.</p>
            </div>
        `;
    }
}

function createAICard(adapter) {
    const isActive = adapter.is_available;
    const cardClass = isActive ? 'ai-card' : 'ai-card inactive';
    const statusClass = isActive ? 'status-dot' : 'status-dot inactive';
    const statusText = isActive ? 'Aktif' : 'Pasif';
    
    const col = document.createElement('div');
    col.className = 'col-md-6 col-lg-4';
    
    col.innerHTML = `
        <div class="${cardClass}">
            <div class="d-flex justify-content-between align-items-start mb-3">
                <div>
                    <h6 class="mb-1">${adapter.type.toUpperCase()}</h6>
                    <small class="text-muted">${adapter.model}</small>
                </div>
                <div class="ai-status">
                    <span class="${statusClass}"></span>
                    <span>${statusText}</span>
                </div>
            </div>
            
            ${adapter.role ? `<div class="badge bg-primary mb-3">${formatRoleName(adapter.role)}</div>` : ''}
            
            <div class="row g-2">
                <div class="col-4">
                    <div class="ai-stat">
                        <div class="ai-stat-label">İstek</div>
                        <div class="ai-stat-value">${adapter.stats.requests || 0}</div>
                    </div>
                </div>
                <div class="col-4">
                    <div class="ai-stat">
                        <div class="ai-stat-label">Token</div>
                        <div class="ai-stat-value">${formatNumber(adapter.stats.tokens || 0)}</div>
                    </div>
                </div>
                <div class="col-4">
                    <div class="ai-stat">
                        <div class="ai-stat-label">Maliyet</div>
                        <div class="ai-stat-value">$${(adapter.stats.cost || 0).toFixed(2)}</div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    return col;
}

// Yardımcı fonksiyonlar
function updateConnectionStatus(connected) {
    const statusEl = document.getElementById('connection-status');
    if (connected) {
        statusEl.innerHTML = '<i class="bi bi-circle-fill text-success"></i> Bağlı';
    } else {
        statusEl.innerHTML = '<i class="bi bi-circle-fill text-danger"></i> Bağlantı kesildi';
    }
}

function calculateRPM() {
    // Basit RPM hesaplaması (son 1 dakika)
    // Şimdilik sabit değer, ileride gerçek hesaplama eklenecek
    return Math.floor(analyticsData.summary.total_requests / 10);
}

function getFastestModel() {
    let fastestModel = null;
    let lowestTime = Infinity;
    
    Object.values(analyticsData.adapters).forEach(adapter => {
        // Mock response time (ileride gerçek veri eklenecek)
        const responseTime = 1.5 + Math.random() * 2;
        if (responseTime < lowestTime) {
            lowestTime = responseTime;
            fastestModel = adapter.model;
        }
    });
    
    return fastestModel;
}

function formatRoleName(role) {
    const roleNames = {
        'project_manager': 'Proje Yöneticisi',
        'lead_developer': 'Lead Developer',
        'boss': 'Patron'
    };
    return roleNames[role] || role;
}

function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}

// Chat fonksiyonları
function addChatMessage(data) {
    const messagesContainer = document.getElementById('chat-messages');
    
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message';
    
    const time = new Date(data.timestamp).toLocaleTimeString('tr-TR');
    
    messageDiv.innerHTML = `
        <div class="message-header">
            <div class="message-role">${formatRoleName(data.role_id)}</div>
            <div class="message-time">${time}</div>
        </div>
        <div class="message-content">
            <p class="mb-2"><strong>Kullanıcı:</strong> ${data.user_message}</p>
            <p class="mb-0"><strong>AI:</strong> ${data.ai_response}</p>
        </div>
        <div class="mt-2">
            <small class="text-muted">
                Model: ${data.model} | 
                Tokens: ${data.usage?.total_tokens || 0} | 
                Cost: $${(data.usage?.cost || 0).toFixed(4)}
            </small>
        </div>
    `;
    
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function addConversationMessage(data) {
    const messagesContainer = document.getElementById('chat-messages');
    
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message';
    
    const time = new Date(data.timestamp).toLocaleTimeString('tr-TR');
    
    messageDiv.innerHTML = `
        <div class="message-header">
            <div class="message-role">${data.speaker_name}</div>
            <div class="message-time">${time} - Tur ${data.turn}</div>
        </div>
        <div class="message-content">
            <p class="mb-0">${data.message}</p>
        </div>
        <div class="mt-2">
            <small class="text-muted">
                Model: ${data.model} | 
                Tokens: ${data.usage?.total_tokens || 0} | 
                Cost: $${(data.usage?.cost || 0).toFixed(4)}
            </small>
        </div>
    `;
    
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function addSystemMessage(message, type = 'info') {
    const messagesContainer = document.getElementById('chat-messages');
    
    const messageDiv = document.createElement('div');
    messageDiv.className = 'alert alert-' + (type === 'error' ? 'danger' : 'info');
    messageDiv.textContent = message;
    
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function clearChatMessages() {
    const messagesContainer = document.getElementById('chat-messages');
    messagesContainer.innerHTML = '';
}

// Form işlemleri
document.getElementById('chat-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    
    if (!message) return;
    
    try {
        const response = await fetch('/api/ai/send_message', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                role_id: 'project_manager',
                message: message,
                context: 'Web UI üzerinden gönderildi'
            })
        });
        
        if (response.ok) {
            input.value = '';
            addSystemMessage('Mesaj gönderildi, yanıt bekleniyor...');
        } else {
            const error = await response.json();
            addSystemMessage('Hata: ' + (error.error || 'Bilinmeyen hata'), 'error');
        }
    } catch (error) {
        addSystemMessage('Hata: ' + error.message, 'error');
    }
});

// Konuşma başlatma
async function startConversation() {
    const prompt = document.getElementById('initial-prompt').value.trim();
    const maxTurns = parseInt(document.getElementById('max-turns').value);
    
    if (!prompt) {
        alert('Lütfen bir başlangıç prompt\'u girin.');
        return;
    }
    
    try {
        const response = await fetch('/api/ai/conversation', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                prompt: prompt,
                max_turns: maxTurns
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            console.log('Conversation started:', data);
        } else {
            const error = await response.json();
            alert('Hata: ' + (error.error || 'Bilinmeyen hata'));
        }
    } catch (error) {
        alert('Hata: ' + error.message);
    }
}

// Geçmişi temizle
function clearHistory() {
    if (confirm('Tüm konuşma geçmişi silinecek. Emin misiniz?')) {
        clearChatMessages();
        addSystemMessage('Konuşma geçmişi temizlendi.');
    }
}

// İlk yükleme
document.addEventListener('DOMContentLoaded', () => {
    console.log('Analytics dashboard loaded');
    
    // İlk analytics verilerini yükle
    fetch('/api/analytics')
        .then(response => response.json())
        .then(data => {
            if (!data.error) {
                analyticsData = data;
                updateAnalyticsDashboard();
            }
        })
        .catch(error => console.error('Failed to load initial analytics:', error));
});

// Periyodik güncelleme (her 30 saniyede bir)
setInterval(() => {
    socket.emit('request_analytics');
}, 30000);

// === CANLI KONUŞMA YÖNETİMİ ===

let conversationState = {
    isActive: false,
    isPaused: false,
    currentTurn: 0,
    maxTurns: 3,
    sessionId: null
};

// Konuşma başlatma
async function startAIConversation() {
    if (conversationState.isActive) return;
    
    const initialPrompt = "AI destekli bir proje geliştiriyoruz. Bu projenin temel hedeflerini ve yaklaşımını tartışalım.";
    
    try {
        // UI güncellemeleri
        updateConversationUI('starting');
        clearLiveChatMessages();
        
        const response = await fetch('/api/ai/conversation', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                prompt: initialPrompt,
                max_turns: conversationState.maxTurns
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            conversationState.isActive = true;
            conversationState.sessionId = Date.now().toString();
            updateConversationUI('active');
            
            addLiveChatSystemMessage(`🚀 AI konuşması başladı: "${initialPrompt}"`);
        } else {
            throw new Error('Konuşma başlatılamadı');
        }
        
    } catch (error) {
        console.error('Conversation start error:', error);
        addLiveChatSystemMessage(`❌ Hata: ${error.message}`, 'error');
        updateConversationUI('idle');
    }
}

// Konuşma duraklat
function pauseConversation() {
    if (!conversationState.isActive) return;
    
    conversationState.isPaused = !conversationState.isPaused;
    updateConversationUI(conversationState.isPaused ? 'paused' : 'active');
    
    addLiveChatSystemMessage(
        conversationState.isPaused ? '⏸️ Konuşma duraklatıldı' : '▶️ Konuşma devam ediyor'
    );
}

// Konuşmayı temizle
function clearConversation() {
    conversationState.isActive = false;
    conversationState.isPaused = false;
    conversationState.currentTurn = 0;
    conversationState.sessionId = null;
    
    clearLiveChatMessages();
    updateConversationUI('idle');
    addLiveChatSystemMessage('🗑️ Konuşma geçmişi temizlendi');
}

// Canlı konuşma mesajlarını temizle
function clearLiveChatMessages() {
    const container = document.getElementById('live-chat-messages');
    container.innerHTML = `
        <div class="text-center text-muted p-4">
            <i class="bi bi-robot" style="font-size: 48px; opacity: 0.3;"></i>
            <p class="mt-2 mb-0">AI konuşması başlatılmayı bekliyor...</p>
            <small>Yukarıdaki "Başlat" butonuna tıklayın</small>
        </div>
    `;
}

// UI durumunu güncelle
function updateConversationUI(state) {
    const startBtn = document.getElementById('start-conversation');
    const pauseBtn = document.getElementById('pause-conversation');
    const clearBtn = document.getElementById('clear-conversation');
    const statusIndicator = document.querySelector('.status-indicator');
    const turnCounter = document.getElementById('turn-counter');
    
    switch (state) {
        case 'idle':
            startBtn.disabled = false;
            pauseBtn.disabled = true;
            clearBtn.disabled = false;
            statusIndicator.innerHTML = '<i class="bi bi-circle-fill text-secondary"></i> Beklemede';
            turnCounter.textContent = 'Tur: 0/0';
            break;
            
        case 'starting':
            startBtn.disabled = true;
            pauseBtn.disabled = true;
            clearBtn.disabled = false;
            statusIndicator.innerHTML = '<i class="bi bi-circle-fill text-warning"></i> Başlatılıyor...';
            break;
            
        case 'active':
            startBtn.disabled = true;
            pauseBtn.disabled = false;
            pauseBtn.innerHTML = '<i class="bi bi-pause-fill"></i> Duraklat';
            clearBtn.disabled = false;
            statusIndicator.innerHTML = '<i class="bi bi-circle-fill text-success"></i> Aktif';
            turnCounter.textContent = `Tur: ${conversationState.currentTurn}/${conversationState.maxTurns}`;
            break;
            
        case 'paused':
            pauseBtn.innerHTML = '<i class="bi bi-play-fill"></i> Devam';
            statusIndicator.innerHTML = '<i class="bi bi-circle-fill text-warning"></i> Duraklatıldı';
            break;
    }
}

// Canlı konuşma mesajı ekle
function addLiveConversationMessage(data) {
    const container = document.getElementById('live-chat-messages');
    
    // İlk mesajsa placeholder'ı kaldır
    if (container.querySelector('.text-center')) {
        container.innerHTML = '';
    }
    
    const messageDiv = document.createElement('div');
    const roleClass = data.speaker === 'project_manager' ? 'pm' : 'ld';
    const roleIcon = data.speaker === 'project_manager' ? '👔' : '💻';
    const roleName = data.speaker_name || (data.speaker === 'project_manager' ? 'Proje Yöneticisi' : 'Lead Developer');
    
    messageDiv.className = `ai-message ${data.speaker}`;
    messageDiv.innerHTML = `
        <div class="message-bubble ${roleClass}">
            <div class="message-header-inline">
                <div class="role-icon ${roleClass}">${roleIcon}</div>
                <span class="role-name">${roleName}</span>
                <span class="turn-info">Tur ${data.turn}</span>
            </div>
            <div class="message-content">${data.message}</div>
        </div>
    `;
    
    container.appendChild(messageDiv);
    
    // Auto scroll to bottom
    container.scrollTop = container.scrollHeight;
    
    // Turn counter güncelle
    conversationState.currentTurn = data.turn;
    updateConversationUI('active');
}

// Sistem mesajı ekle (live chat'e)
function addLiveChatSystemMessage(message, type = 'info') {
    const container = document.getElementById('live-chat-messages');
    
    // İlk mesajsa placeholder'ı kaldır
    if (container.querySelector('.text-center')) {
        container.innerHTML = '';
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.className = 'text-center my-2';
    
    const alertClass = type === 'error' ? 'alert-danger' : 'alert-info';
    messageDiv.innerHTML = `
        <div class="alert ${alertClass} py-2 px-3 d-inline-block mb-0" style="font-size: 12px;">
            ${message}
        </div>
    `;
    
    container.appendChild(messageDiv);
    container.scrollTop = container.scrollHeight;
}

// SocketIO event listeners için güncellemeler
socket.on('conversation_started', (data) => {
    console.log('Conversation started:', data);
    addLiveChatSystemMessage(`🚀 Konuşma başladı: "${data.prompt}"`);
    conversationState.maxTurns = data.max_turns;
    updateConversationUI('active');
});

socket.on('conversation_turn', (data) => {
    console.log('Conversation turn:', data);
    const roleIcon = data.phase === 'pm_thinking' ? '👔' : '💻';
    const roleName = data.phase === 'pm_thinking' ? 'Proje Yöneticisi' : 'Lead Developer';
    
    addLiveChatSystemMessage(`${roleIcon} ${roleName} düşünüyor... <span class="thinking-indicator">💭</span>`);
});

socket.on('conversation_message', (data) => {
    console.log('Conversation message:', data);
    addLiveConversationMessage(data);
});

socket.on('conversation_completed', (data) => {
    console.log('Conversation completed:', data);
    addLiveChatSystemMessage(`✅ Konuşma tamamlandı! Toplam ${data.total_turns} tur gerçekleştirildi.`);
    conversationState.isActive = false;
    updateConversationUI('idle');
});

socket.on('conversation_error', (data) => {
    console.error('Conversation error:', data);
    addLiveChatSystemMessage(`❌ Konuşma hatası: ${data.error}`, 'error');
    conversationState.isActive = false;
    updateConversationUI('idle');
}); 