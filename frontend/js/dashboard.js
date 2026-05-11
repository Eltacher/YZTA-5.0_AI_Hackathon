/* ─── Dashboard Modülü ─── */
const DashboardPage = {
    async render() {
        let summary = {};
        try { summary = await api.get('/analytics/dashboard-summary'); } catch(e) { console.error(e); }

        return `
        <div class="stats-grid">
            <div class="stat-card purple">
                <div class="stat-icon">📦</div>
                <div class="stat-value">${summary.today_orders || 0}</div>
                <div class="stat-label">Bugünkü Siparişler</div>
            </div>
            <div class="stat-card teal">
                <div class="stat-icon">💰</div>
                <div class="stat-value">${UI.formatMoney(summary.today_revenue)}</div>
                <div class="stat-label">Bugünkü Ciro</div>
            </div>
            <div class="stat-card yellow">
                <div class="stat-icon">⏳</div>
                <div class="stat-value">${summary.pending_orders || 0}</div>
                <div class="stat-label">Bekleyen Siparişler</div>
            </div>
            <div class="stat-card pink">
                <div class="stat-icon">⚠️</div>
                <div class="stat-value">${summary.low_stock_count || 0}</div>
                <div class="stat-label">Stok Uyarısı</div>
            </div>
        </div>

        <div class="grid-2">
            <div class="card">
                <div class="card-header"><h3>📦 Son Siparişler</h3></div>
                <div class="card-body" id="dash-recent-orders">Yükleniyor...</div>
            </div>
            <div class="card">
                <div class="card-header"><h3>⚠️ Aktif Uyarılar</h3></div>
                <div class="card-body" id="dash-alerts">Yükleniyor...</div>
            </div>
        </div>

        <div class="grid-2" style="margin-top:20px">
            <div class="card">
                <div class="card-header"><h3>✅ Bugünkü Görevler</h3></div>
                <div class="card-body" id="dash-tasks">Yükleniyor...</div>
            </div>
            <div class="card">
                <div class="card-header"><h3>🚚 Kargo Durumu</h3></div>
                <div class="card-body" id="dash-cargo">Yükleniyor...</div>
            </div>
        </div>`;
    },

    async afterRender() {
        this.loadRecentOrders();
        this.loadAlerts();
        this.loadTasks();
        this.loadCargo();
    },

    async loadRecentOrders() {
        const el = document.getElementById('dash-recent-orders');
        try {
            const data = await api.get('/orders/?limit=5');
            if (!data.orders?.length) { el.innerHTML = UI.emptyState('📦','Sipariş yok','Henüz sipariş bulunmuyor'); return; }
            el.innerHTML = `<table><thead><tr><th>Sipariş</th><th>Müşteri</th><th>Tutar</th><th>Durum</th></tr></thead><tbody>${
                data.orders.map(o => `<tr><td><strong>#${o.order_number}</strong></td><td>${o.customer_name||'-'}</td><td>${UI.formatMoney(o.total_amount)}</td><td>${UI.badge(o.status)}</td></tr>`).join('')
            }</tbody></table>`;
        } catch(e) { el.innerHTML = '<p style="color:var(--text-muted)">Yüklenemedi</p>'; }
    },

    async loadAlerts() {
        const el = document.getElementById('dash-alerts');
        try {
            const alerts = await api.get('/inventory/alerts');
            if (!alerts?.length) { el.innerHTML = UI.emptyState('✅','Uyarı yok','Tüm stoklar normal seviyede'); return; }
            el.innerHTML = alerts.slice(0,5).map(a => `<div class="alert-item">
                <span class="alert-icon">${a.alert_type==='out_of_stock'?'🔴':'🟡'}</span>
                <div class="alert-content"><div class="alert-title">${a.product_name||'Ürün'}</div><div class="alert-desc">${a.message}</div>
                ${a.suggested_action ? `<div class="alert-action">💡 ${a.suggested_action}</div>`:''}</div>
            </div>`).join('');
        } catch(e) { el.innerHTML = '<p style="color:var(--text-muted)">Yüklenemedi</p>'; }
    },

    async loadTasks() {
        const el = document.getElementById('dash-tasks');
        try {
            const data = await api.get('/tasks/?limit=5');
            const tasks = data.tasks || [];
            if (!tasks.length) { el.innerHTML = UI.emptyState('✅','Görev yok','Bugün için görev bulunmuyor'); return; }
            el.innerHTML = tasks.slice(0,5).map(t => {
                const checkClass = t.status==='done'?'done':t.status==='in_progress'?'in-progress':'';
                return `<div class="task-item"><div class="task-check ${checkClass}">${t.status==='done'?'✓':''}</div>
                    <div class="task-info"><div class="task-title">${t.title}</div>
                    <div class="task-meta"><span>${t.assigned_to||'Atanmamış'}</span><span>${UI.badge(t.priority)}</span></div></div></div>`;
            }).join('');
        } catch(e) { el.innerHTML = '<p style="color:var(--text-muted)">Yüklenemedi</p>'; }
    },

    async loadCargo() {
        const el = document.getElementById('dash-cargo');
        try {
            const s = await api.get('/cargo/summary');
            el.innerHTML = `<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
                <div><span style="font-size:24px;font-weight:700">${s.preparing||0}</span><br><small style="color:var(--text-muted)">Hazırlanıyor</small></div>
                <div><span style="font-size:24px;font-weight:700">${s.in_transit||0}</span><br><small style="color:var(--text-muted)">Yolda</small></div>
                <div><span style="font-size:24px;font-weight:700">${s.delivered||0}</span><br><small style="color:var(--text-muted)">Teslim</small></div>
                <div><span style="font-size:24px;font-weight:700;color:${s.delayed?'var(--danger)':'var(--success)'}">${s.delayed||0}</span><br><small style="color:var(--text-muted)">Geciken</small></div>
            </div>
            <div style="margin-top:14px"><div class="progress-bar"><div class="progress-fill" style="width:${s.on_time_rate||100}%;background:${s.on_time_rate>80?'var(--gradient-2)':'var(--gradient-3)'}"></div></div>
            <small style="color:var(--text-muted);margin-top:4px;display:block">Zamanında Teslim: %${s.on_time_rate||100}</small></div>`;
        } catch(e) { el.innerHTML = '<p style="color:var(--text-muted)">Yüklenemedi</p>'; }
    }
};
