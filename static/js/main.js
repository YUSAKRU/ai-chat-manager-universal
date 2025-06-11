// main.js - Chrome Profil seçimi ve toast bildirimleri

document.addEventListener('DOMContentLoaded', () => {
    // --- Element referansları ---
    const profileModalEl = document.getElementById('profileSelectionModal');
    if (!profileModalEl) return; // Eski sayfa sürümlerinde modal yoksa çık

    const profileModal = new bootstrap.Modal(profileModalEl);
    const pmSelect = document.getElementById('pm-profile-select');
    const ldSelect = document.getElementById('ld-profile-select');
    const saveBtn = document.getElementById('save-profiles-btn');

    const toastEl = document.getElementById('notification-toast');
    const toast = new bootstrap.Toast(toastEl);
    const toastTitle = document.getElementById('toast-title');
    const toastBody = document.getElementById('toast-body');

    // Yardımcı – toast göster
    function showToast(title, message, isError = false) {
        toastTitle.textContent = title;
        toastBody.textContent = message;
        const header = toastEl.querySelector('.toast-header');
        header.classList.toggle('bg-danger', isError);
        header.classList.toggle('text-white', isError);
        toast.show();
    }

    // Dropdownları doldur
    async function loadProfiles() {
        try {
            const res = await fetch('/api/chrome_profiles/list');
            if (!res.ok) throw new Error('Profil listesi alınamadı');
            const data = await res.json();
            const profiles = data.profiles || [];

            // Select öğelerini temizle
            pmSelect.innerHTML = '<option selected disabled value="">Bir profil seçin...</option>';
            ldSelect.innerHTML = '<option selected disabled value="">Bir profil seçin...</option>';
            profiles.forEach(p => {
                const optionPM = document.createElement('option');
                optionPM.value = p.name;
                optionPM.textContent = p.display_name;

                const optionLD = optionPM.cloneNode(true);

                pmSelect.appendChild(optionPM);
                ldSelect.appendChild(optionLD);
            });
            saveBtn.disabled = true; // seçim bekleniyor
        } catch (err) {
            console.error(err);
            pmSelect.innerHTML = '<option selected disabled value="">Hata!</option>';
            ldSelect.innerHTML = '<option selected disabled value="">Hata!</option>';
            showToast('Hata', err.message, true);
        }
    }

    // Modal açılırken profilleri yükle
    profileModalEl.addEventListener('show.bs.modal', loadProfiles);

    // Select değişiminde butonu aktif et
    [pmSelect, ldSelect].forEach(sel => sel.addEventListener('change', () => {
        saveBtn.disabled = !(pmSelect.value && ldSelect.value);
    }));

    // Kaydet butonu
    saveBtn.addEventListener('click', async () => {
        const mapping = {
            project_manager: pmSelect.value,
            lead_developer: ldSelect.value
        };

        try {
            const res = await fetch('/api/chrome_profiles/select', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(mapping)
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.error || 'Bilinmeyen hata');

            // UI güncelle
            document.getElementById('pm-profile-display').textContent = data.selected_profiles.project_manager;
            document.getElementById('ld-profile-display').textContent = data.selected_profiles.lead_developer;
            showToast('Başarılı', 'Profiller kaydedildi ✅');
            profileModal.hide();

            // Tarayıcı başlat butonunu aktif et
            const startBrowsersBtn = document.getElementById('start-browsers-btn');
            if (startBrowsersBtn) {
                startBrowsersBtn.disabled = false;
            }
        } catch (err) {
            console.error(err);
            showToast('Kaydetme Hatası', err.message, true);
        }
    });

    // ----------------------------------------------
    // 🔄 Tarayıcı Başlatma & Durum Logu
    // ----------------------------------------------
    const startBrowsersBtn = document.getElementById('start-browsers-btn');
    const stopBrowsersBtn = document.getElementById('stop-browsers-btn');
    const statusLog = document.getElementById('status-log');

    // Socket.IO bağlantısı (varsa global socket kullan, yoksa yeni oluştur)
    const socketGlobal = window.socket || io();

    function logStatus(message, level = 'info') {
        if (!statusLog) return;
        if (statusLog.querySelector('.text-muted')) {
            statusLog.innerHTML = '';
        }
        const p = document.createElement('p');
        p.textContent = message;
        if (level === 'error') p.className = 'text-danger';
        if (level === 'success') p.className = 'text-success';
        if (level === 'final') p.className = 'text-primary fw-bold';
        statusLog.appendChild(p);
        statusLog.scrollTop = statusLog.scrollHeight;
    }

    if (startBrowsersBtn && stopBrowsersBtn) {
        startBrowsersBtn.addEventListener('click', async () => {
            startBrowsersBtn.disabled = true;
            startBrowsersBtn.textContent = 'Başlatılıyor...';
            logStatus('Kullanıcı tarayıcıları başlatma komutu verdi.', 'info');
            try {
                const res = await fetch('/api/browsers/start', { method: 'POST' });
                if (!res.ok) {
                    throw new Error('Başlatma isteği başarısız');
                }
            } catch (err) {
                logStatus(`❌ Hata: ${err.message}`, 'error');
                startBrowsersBtn.disabled = false;
                startBrowsersBtn.textContent = 'Tarayıcıları Başlat';
            }
        });
    }

    // Sunucudan gelen status_update eventleri
    socketGlobal.on('status_update', data => {
        logStatus(data.message, data.level);
        if (startBrowsersBtn && stopBrowsersBtn) {
            if (data.level === 'final') {
                startBrowsersBtn.textContent = 'Sistem Hazır ✅';
                startBrowsersBtn.style.display = 'none';
                stopBrowsersBtn.style.display = 'inline-block';
                stopBrowsersBtn.disabled = false;
            } else if (data.level === 'error') {
                startBrowsersBtn.disabled = false;
                startBrowsersBtn.textContent = 'Tekrar Dene';
                stopBrowsersBtn.style.display = 'none';
            }
        }
    });

    // Sistemin resetlenmesi
    socketGlobal.on('system_reset', data => {
        logStatus(data.message, 'info');
        if (startBrowsersBtn && stopBrowsersBtn) {
            startBrowsersBtn.textContent = 'Tarayıcıları Başlat';
            startBrowsersBtn.style.display = 'inline-block';
            startBrowsersBtn.disabled = false;

            stopBrowsersBtn.style.display = 'none';
            stopBrowsersBtn.disabled = true;
        }
    });

    // Stop button handler
    if (stopBrowsersBtn) {
        stopBrowsersBtn.addEventListener('click', async () => {
            stopBrowsersBtn.disabled = true;
            stopBrowsersBtn.textContent = 'Durduruluyor...';
            logStatus('Kullanıcı tarayıcıları durdurma komutu verdi.', 'info');
            try {
                const res = await fetch('/api/browsers/stop', { method: 'POST' });
                if (!res.ok) throw new Error('Durdurma isteği hatalı');
            } catch (err) {
                logStatus(`❌ Hata: ${err.message}`, 'error');
                stopBrowsersBtn.disabled = false;
                stopBrowsersBtn.textContent = 'Tarayıcıları Durdur';
            }
        });
    }

    // -------------------------------------------------
    // 📋 Görev Panosu & Memory Bank Viewer
    // -------------------------------------------------

    const taskListDiv = document.getElementById('task-list');
    const memoryFileList = document.getElementById('memory-file-list');
    const memoryModal = new bootstrap.Modal(document.getElementById('memoryFileModal'));
    const memoryContentEl = document.getElementById('memory-file-content');
    const memoryModalLabel = document.getElementById('memoryFileModalLabel');
    const memoryFileEditor = document.getElementById('memory-file-editor');
    const saveMemoryBtn = document.getElementById('save-memory-btn');
    const previewChangesBtn = document.getElementById('preview-changes-btn');
    const diffModal = new bootstrap.Modal(document.getElementById('diffModal'));
    let currentEditingFile = null;

    async function loadTasks() {
        if (!taskListDiv) return;
        try {
            const res = await fetch('/api/tasks');
            const tasks = await res.json();
            taskListDiv.innerHTML = '';
            if (tasks.length === 0) {
                taskListDiv.innerHTML = '<p class="text-muted">Gösterilecek görev yok.</p>';
                return;
            }
            tasks.forEach(t => {
                const isCompleted = t.status === 'completed';
                const checkedAttr = isCompleted ? 'checked' : '';
                const cls = isCompleted ? 'text-decoration-line-through text-muted' : '';
                taskListDiv.insertAdjacentHTML('beforeend', `
                    <div class="form-check">
                        <input class="form-check-input task-checkbox" type="checkbox" ${checkedAttr} data-task-text="${t.text.replace(/"/g,'&quot;')}">
                        <label class="form-check-label ${cls}">${t.text}</label>
                    </div>`);
            });
        } catch (err) {
            taskListDiv.innerHTML = '<p class="text-danger">Görevler yüklenemedi.</p>';
            console.error(err);
        }
    }

    async function loadMemoryFiles() {
        if (!memoryFileList) return;
        try {
            const res = await fetch('/api/memory/list');
            const files = await res.json();
            memoryFileList.innerHTML = '';
            if (!Array.isArray(files) || files.length === 0) {
                memoryFileList.innerHTML = '<li class="list-group-item text-muted">Bellekte dosya yok.</li>';
                return;
            }
            files.forEach(f => {
                const li = document.createElement('li');
                li.className = 'list-group-item list-group-item-action';
                li.textContent = f;
                li.dataset.filename = f;
                li.style.cursor = 'pointer';
                memoryFileList.appendChild(li);
            });
        } catch (err) {
            memoryFileList.innerHTML = '<li class="list-group-item text-danger">Dosyalar yüklenemedi.</li>';
            console.error(err);
        }
    }

    if (memoryFileList) {
        memoryFileList.addEventListener('click', async e => {
            const target = e.target;
            if (target && target.dataset.filename) {
                const fname = target.dataset.filename;
                memoryModalLabel.textContent = `Dosya: ${fname}`;
                memoryContentEl.textContent = 'İçerik yükleniyor...';
                memoryModal.show();
                try {
                    const res = await fetch(`/api/memory/view/${fname}`);
                    const data = await res.json();
                    if (data.error) throw new Error(data.error);
                    // open editor modal instead
                    memoryFileEditor.value = data.content;
                    saveMemoryBtn.disabled = true;
                    currentEditingFile = fname;
                } catch (err) {
                    showToast('Hata', err.message, true);
                }
            }
        });
    }

    // Preview changes button
    if (previewChangesBtn) {
        previewChangesBtn.addEventListener('click', async () => {
            if (!currentEditingFile) return;
            const newContent = memoryFileEditor.value;
            try {
                const res = await fetch('/api/memory/diff', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ filename: currentEditingFile, content: newContent })
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data.error || 'Sunucu hatası');
                document.getElementById('diff-content').textContent = data.diff || 'Değişiklik bulunamadı.';
                saveMemoryBtn.disabled = !data.diff;
                diffModal.show();
            } catch (err) {
                showToast('Önizleme Hatası', err.message, true);
            }
        });
    }

    // Save memory button
    if (saveMemoryBtn) {
        saveMemoryBtn.addEventListener('click', async () => {
            if (!currentEditingFile) return;
            saveMemoryBtn.disabled = true;
            saveMemoryBtn.textContent = 'Kaydediliyor...';
            const newContent = memoryFileEditor.value;
            try {
                const res = await fetch('/api/memory/update', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ filename: currentEditingFile, content: newContent })
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data.error || 'Sunucu hatası');
                showToast('Başarılı', data.message, false);
                memoryModal.hide();
                diffModal.hide();
                loadMemoryFiles();
            } catch (err) {
                showToast('Kaydetme Hatası', err.message, true);
            } finally {
                saveMemoryBtn.textContent = 'Değişiklikleri Kaydet';
            }
        });
    }

    // Sayfa yüklenince ilk çağrı
    loadTasks();
    loadMemoryFiles();

    // Görev checkbox click listener (event delegation)
    if (taskListDiv) {
        taskListDiv.addEventListener('click', async e => {
            if (e.target && e.target.classList.contains('task-checkbox')) {
                const cb = e.target;
                const taskText = cb.dataset.taskText;
                const newStatus = cb.checked ? 'completed' : 'pending';
                const label = cb.nextElementSibling;
                label.classList.toggle('text-decoration-line-through', cb.checked);
                label.classList.toggle('text-muted', cb.checked);

                try {
                    const res = await fetch('/api/tasks/update', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ text: taskText, status: newStatus })
                    });
                    const data = await res.json();
                    if (!res.ok) throw new Error(data.error || 'Sunucu hatası');
                    showToast('Görev Güncellendi', `${taskText.substring(0,30)}...`, false);
                } catch (err) {
                    // rollback
                    cb.checked = !cb.checked;
                    label.classList.toggle('text-decoration-line-through', cb.checked);
                    label.classList.toggle('text-muted', cb.checked);
                    showToast('Hata', err.message, true);
                }
            }
        });
    }
}); 