/* ─── Görev Yönetimi Modülü ─── */
const TasksPage = {
    async render() {
        let stats = {};
        try { stats = await api.get('/tasks/stats'); } catch(e) {}
        return `<div class="stats-grid">
            <div class="stat-card purple"><div class="stat-icon">📋</div><div class="stat-value">${stats.total||0}</div><div class="stat-label">Toplam Görev</div></div>
            <div class="stat-card yellow"><div class="stat-icon">⏳</div><div class="stat-value">${stats.todo||0}</div><div class="stat-label">Yapılacak</div></div>
            <div class="stat-card teal"><div class="stat-icon">🔄</div><div class="stat-value">${stats.in_progress||0}</div><div class="stat-label">Devam Eden</div></div>
            <div class="stat-card pink"><div class="stat-icon">✅</div><div class="stat-value">${stats.done||0}</div><div class="stat-label">Tamamlanan</div></div>
        </div>
        <div class="filter-bar">
            <select class="form-select" id="task-status-filter"><option value="">Tüm Durumlar</option><option value="todo">Yapılacak</option><option value="in_progress">Devam Eden</option><option value="done">Tamamlanan</option></select>
            <select class="form-select" id="task-category-filter"><option value="">Tüm Kategoriler</option><option value="depo">Depo</option><option value="kargo">Kargo</option><option value="siparis">Sipariş</option><option value="genel">Genel</option></select>
            <div class="spacer"></div>
            <button class="btn btn-secondary" onclick="TasksPage.generateDaily()">🤖 Günlük Görev Oluştur</button>
            <button class="btn btn-primary" onclick="TasksPage.showAddModal()">+ Yeni Görev</button>
        </div>
        <div id="tasks-container">Yükleniyor...</div>`;
    },
    async afterRender() {
        this.loadTasks();
        document.getElementById('task-status-filter').addEventListener('change', () => this.loadTasks());
        document.getElementById('task-category-filter').addEventListener('change', () => this.loadTasks());
    },
    async loadTasks() {
        const el = document.getElementById('tasks-container');
        const status = document.getElementById('task-status-filter').value;
        const category = document.getElementById('task-category-filter').value;
        try {
            let url = '/tasks/?limit=50';
            if (status) url += `&status=${status}`;
            if (category) url += `&category=${category}`;
            const data = await api.get(url);
            if (!data.tasks?.length) { el.innerHTML = UI.emptyState('✅','Görev yok','Tüm görevler tamamlanmış'); return; }
            el.innerHTML = data.tasks.map(t => {
                const checkClass = t.status==='done'?'done':t.status==='in_progress'?'in-progress':'';
                const nextStatus = t.status==='todo'?'in_progress':t.status==='in_progress'?'done':null;
                return `<div class="task-item">
                    <div class="task-check ${checkClass}" onclick="${nextStatus?`TasksPage.updateTaskStatus(${t.id},'${nextStatus}')`:''}" title="${nextStatus?'Durumu ilerlet':'Tamamlandı'}">${t.status==='done'?'✓':t.status==='in_progress'?'●':''}</div>
                    <div class="task-info">
                        <div class="task-title" style="${t.status==='done'?'text-decoration:line-through;opacity:.6':''}">${t.title}</div>
                        <div class="task-meta">
                            <span>👤 ${t.assigned_to||'Atanmamış'}</span>
                            <span>${UI.badge(t.priority)}</span>
                            ${t.due_date?`<span>📅 ${UI.formatDate(t.due_date)}</span>`:''}
                            ${t.is_auto_generated?'<span style="color:var(--accent)">🤖 AI</span>':''}
                        </div>
                    </div>
                    <button class="btn-icon" onclick="TasksPage.deleteTask(${t.id})" title="Sil">🗑️</button>
                </div>`;
            }).join('');
        } catch(e) { el.innerHTML = '<p style="color:var(--danger)">Yüklenemedi</p>'; }
    },
    async updateTaskStatus(id, status) {
        try {
            await api.patch(`/tasks/${id}`, { status });
            UI.toast(`Görev ${status==='done'?'tamamlandı':'güncellendi'}`, 'success');
            this.loadTasks();
        } catch(e) { UI.toast(e.message,'error'); }
    },
    async deleteTask(id) {
        try { await api.delete(`/tasks/${id}`); UI.toast('Görev silindi','success'); this.loadTasks(); } catch(e) { UI.toast(e.message,'error'); }
    },
    async generateDaily() {
        try {
            const res = await api.post('/tasks/generate-daily');
            UI.toast(`${res.generated} günlük görev oluşturuldu`, 'success');
            this.loadTasks();
        } catch(e) { UI.toast(e.message,'error'); }
    },
    showAddModal() {
        UI.modal('Yeni Görev',
            `<div class="form-group"><label class="form-label">Başlık</label><input class="form-input" id="task-title"></div>
            <div class="form-group"><label class="form-label">Açıklama</label><textarea class="form-textarea" id="task-desc"></textarea></div>
            <div class="form-row"><div class="form-group"><label class="form-label">Atanan Kişi</label><input class="form-input" id="task-assignee"></div>
            <div class="form-group"><label class="form-label">Öncelik</label><select class="form-select" id="task-priority"><option value="low">Düşük</option><option value="medium" selected>Orta</option><option value="high">Yüksek</option><option value="urgent">Acil</option></select></div></div>
            <div class="form-row"><div class="form-group"><label class="form-label">Kategori</label><select class="form-select" id="task-cat"><option value="genel">Genel</option><option value="depo">Depo</option><option value="kargo">Kargo</option><option value="siparis">Sipariş</option></select></div>
            <div class="form-group"><label class="form-label">Bitiş Tarihi</label><input class="form-input" id="task-due" type="datetime-local"></div></div>`,
            `<button class="btn btn-secondary" onclick="UI.closeModal()">İptal</button><button class="btn btn-primary" onclick="TasksPage.createTask()">Oluştur</button>`);
    },
    async createTask() {
        try {
            await api.post('/tasks/', {
                title: document.getElementById('task-title').value,
                description: document.getElementById('task-desc').value,
                assigned_to: document.getElementById('task-assignee').value,
                priority: document.getElementById('task-priority').value,
                category: document.getElementById('task-cat').value,
                due_date: document.getElementById('task-due').value || null
            });
            UI.closeModal(); UI.toast('Görev oluşturuldu','success'); this.loadTasks();
        } catch(e) { UI.toast(e.message,'error'); }
    }
};
