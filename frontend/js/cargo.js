/* ─── Kargo Modülü ─── */
const CargoPage = {
    async render() {
        let summary = {};
        try { summary = await api.get('/cargo/summary'); } catch(e) {}
        return `<div class="stats-grid">
            <div class="stat-card purple"><div class="stat-icon">📦</div><div class="stat-value">${summary.preparing||0}</div><div class="stat-label">Hazırlanıyor</div></div>
            <div class="stat-card teal"><div class="stat-icon">🚛</div><div class="stat-value">${summary.in_transit||0}</div><div class="stat-label">Yolda</div></div>
            <div class="stat-card yellow"><div class="stat-icon">✅</div><div class="stat-value">${summary.delivered||0}</div><div class="stat-label">Teslim Edildi</div></div>
            <div class="stat-card pink"><div class="stat-icon">⚠️</div><div class="stat-value">${summary.delayed||0}</div><div class="stat-label">Geciken</div></div>
        </div>
        <div class="filter-bar">
            <select class="form-select" id="cargo-status-filter">
                <option value="">Tüm Durumlar</option>
                <option value="preparing">Hazırlanıyor</option><option value="in_transit">Yolda</option>
                <option value="delivered">Teslim Edildi</option><option value="delayed">Gecikmiş</option>
            </select>
            <label style="display:flex;align-items:center;gap:6px;font-size:13px;color:var(--text-secondary)"><input type="checkbox" id="cargo-delayed-only"> Sadece Geciken</label>
            <div class="spacer"></div>
            <button class="btn btn-secondary" onclick="CargoPage.checkDelays()">🔍 Gecikme Kontrolü</button>
        </div>
        <div class="card"><div class="card-body table-wrapper" id="cargo-table">Yükleniyor...</div></div>`;
    },
    async afterRender() {
        this.loadShipments();
        document.getElementById('cargo-status-filter').addEventListener('change', () => this.loadShipments());
        document.getElementById('cargo-delayed-only').addEventListener('change', () => this.loadShipments());
    },
    async loadShipments() {
        const el = document.getElementById('cargo-table');
        const status = document.getElementById('cargo-status-filter').value;
        const delayed = document.getElementById('cargo-delayed-only').checked;
        try {
            let url = '/cargo/?limit=50';
            if (status) url += `&status=${status}`;
            if (delayed) url += '&delayed_only=true';
            const data = await api.get(url);
            if (!data.shipments?.length) { el.innerHTML = UI.emptyState('🚚','Kargo yok','Henüz kargo kaydı yok'); return; }
            el.innerHTML = `<table><thead><tr><th>Takip No</th><th>Sipariş</th><th>Firma</th><th>Durum</th><th>Konum</th><th>Tah. Teslimat</th><th>İşlem</th></tr></thead><tbody>${
                data.shipments.map(s => `<tr>
                    <td><strong>${s.tracking_number}</strong></td>
                    <td>#${s.order_number||'-'}</td><td>${s.carrier||'-'}</td>
                    <td>${UI.badge(s.status)}${s.is_delayed?' <span style="color:var(--danger)">⚠️</span>':''}</td>
                    <td>${s.last_location||'-'}</td>
                    <td>${UI.formatDate(s.estimated_delivery)}</td>
                    <td><button class="btn-icon" onclick="CargoPage.showDetail(${s.id})" title="Detay">👁️</button></td>
                </tr>`).join('')
            }</tbody></table>`;
        } catch(e) { el.innerHTML = '<p style="color:var(--danger)">Yüklenemedi</p>'; }
    },
    async showDetail(id) {
        try {
            const s = await api.get(`/cargo/${id}`);
            const statusOpts = ['preparing','picked_up','in_transit','out_for_delivery','delivered','delayed'].map(st =>
                `<option value="${st}" ${s.status===st?'selected':''}>${UI.statusLabels[st]||st}</option>`).join('');
            UI.modal(`Kargo: ${s.tracking_number}`,
                `<div class="form-row"><div class="form-group"><div class="form-label">Sipariş</div><div>#${s.order_number||'-'}</div></div><div class="form-group"><div class="form-label">Firma</div><div>${s.carrier}</div></div></div>
                <div class="form-group"><div class="form-label">Durum</div><select class="form-select" id="cargo-status-select">${statusOpts}</select></div>
                <div class="form-group"><label class="form-label">Konum</label><input class="form-input" id="cargo-location" value="${s.last_location||''}"></div>
                ${s.is_delayed?`<div class="alert-item" style="margin-top:12px"><span class="alert-icon">⚠️</span><div class="alert-content"><div class="alert-title">Gecikme Tespit Edildi</div><div class="alert-desc">${s.delay_reason||'Sebep belirtilmemiş'}</div></div></div>`:''}`,
                `<button class="btn btn-secondary" onclick="UI.closeModal()">Kapat</button><button class="btn btn-primary" onclick="CargoPage.updateStatus(${s.id})">Güncelle</button>`);
        } catch(e) { UI.toast('Kargo yüklenemedi','error'); }
    },
    async updateStatus(id) {
        try {
            await api.patch(`/cargo/${id}/status`, {
                status: document.getElementById('cargo-status-select').value,
                location: document.getElementById('cargo-location').value
            });
            UI.closeModal(); UI.toast('Kargo güncellendi','success'); this.loadShipments();
        } catch(e) { UI.toast(e.message,'error'); }
    },
    async checkDelays() {
        try {
            const res = await api.get('/cargo/check-delays');
            UI.toast(`Gecikme kontrolü tamamlandı: ${res.new_delays} yeni gecikme`, res.new_delays ? 'warning' : 'success');
            this.loadShipments();
        } catch(e) { UI.toast('Kontrol başarısız','error'); }
    }
};
