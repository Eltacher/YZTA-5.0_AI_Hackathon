/* ─── Stok/Envanter Modülü ─── */
const InventoryPage = {
    async render() {
        return `<div class="filter-bar">
            <button class="btn btn-secondary" onclick="InventoryPage.checkStock()">🔍 Stok Kontrolü Çalıştır</button>
            <div class="spacer"></div>
        </div>
        <div class="grid-2">
            <div class="card"><div class="card-header"><h3>⚠️ Aktif Stok Uyarıları</h3></div><div class="card-body" id="inv-alerts">Yükleniyor...</div></div>
            <div class="card"><div class="card-header"><h3>📊 Düşük Stoklu Ürünler</h3></div><div class="card-body" id="inv-low-stock">Yükleniyor...</div></div>
        </div>`;
    },
    async afterRender() { this.loadAlerts(); this.loadLowStock(); },
    async loadAlerts() {
        const el = document.getElementById('inv-alerts');
        try {
            const alerts = await api.get('/inventory/alerts');
            if (!alerts?.length) { el.innerHTML = UI.emptyState('✅','Uyarı yok','Tüm stoklar normal'); return; }
            el.innerHTML = alerts.map(a => `<div class="alert-item">
                <span class="alert-icon">${a.alert_type==='out_of_stock'?'🔴':'🟡'}</span>
                <div class="alert-content"><div class="alert-title">${a.product_name}</div><div class="alert-desc">${a.message}</div>
                ${a.suggested_action?`<div class="alert-action">💡 ${a.suggested_action}</div>`:''}
                <div style="margin-top:8px;display:flex;gap:8px">
                    <button class="btn btn-sm btn-secondary" onclick="InventoryPage.showReorder(${a.product_id})">📋 Sipariş Önerisi</button>
                    <button class="btn btn-sm btn-secondary" onclick="InventoryPage.resolveAlert(${a.id})">✅ Çözüldü</button>
                </div></div></div>`).join('');
        } catch(e) { el.innerHTML = '<p style="color:var(--danger)">Yüklenemedi</p>'; }
    },
    async loadLowStock() {
        const el = document.getElementById('inv-low-stock');
        try {
            const data = await api.get('/products/?low_stock=true');
            if (!data.products?.length) { el.innerHTML = UI.emptyState('✅','Hepsi normal','Kritik stok yok'); return; }
            el.innerHTML = `<table><thead><tr><th>Ürün</th><th>Stok</th><th>Eşik</th><th>Durum</th></tr></thead><tbody>${
                data.products.map(p => `<tr><td>${p.name}</td><td>${p.stock_quantity} ${p.unit}</td><td>${p.min_stock_threshold} ${p.unit}</td>
                <td>${p.stock_quantity<=0?UI.badge('out'):UI.badge('low')}</td></tr>`).join('')
            }</tbody></table>`;
        } catch(e) { el.innerHTML = '<p style="color:var(--danger)">Yüklenemedi</p>'; }
    },
    async checkStock() {
        try {
            const res = await api.get('/inventory/check');
            UI.toast(`Stok kontrolü: ${res.new_alerts} yeni uyarı`, res.new_alerts ? 'warning' : 'success');
            this.loadAlerts(); this.loadLowStock();
        } catch(e) { UI.toast('Kontrol başarısız','error'); }
    },
    async resolveAlert(id) {
        try {
            await api.patch(`/inventory/alerts/${id}/resolve`);
            UI.toast('Uyarı çözüldü','success'); this.loadAlerts();
        } catch(e) { UI.toast(e.message,'error'); }
    },
    async showReorder(productId) {
        try {
            const draft = await api.get(`/inventory/supplier-draft/${productId}`);
            UI.modal('📋 Tedarikçi Sipariş Taslağı',
                `<div class="form-group"><div class="form-label">Konu</div><div style="font-weight:600">${draft.subject}</div></div>
                <div class="form-group"><div class="form-label">Öneri</div><div style="padding:12px;background:var(--bg-secondary);border-radius:var(--radius-sm);color:var(--text-secondary);font-size:13px">${draft.suggestion?.recommendation||''}</div></div>
                <div class="form-group"><div class="form-label">Mail Taslağı</div><pre style="padding:12px;background:var(--bg-secondary);border-radius:var(--radius-sm);font-size:12px;white-space:pre-wrap;color:var(--text-primary)">${draft.body}</pre></div>`,
                `<button class="btn btn-secondary" onclick="UI.closeModal()">Kapat</button>`);
        } catch(e) { UI.toast('Öneri yüklenemedi','error'); }
    }
};
