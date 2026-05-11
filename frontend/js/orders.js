/* ─── Siparişler Modülü ─── */
const OrdersPage = {
    async render() {
        return `<div class="filter-bar">
            <select class="form-select" id="order-status-filter">
                <option value="">Tüm Durumlar</option>
                <option value="pending">Beklemede</option><option value="confirmed">Onaylandı</option>
                <option value="preparing">Hazırlanıyor</option><option value="shipped">Kargoda</option>
                <option value="delivered">Teslim Edildi</option><option value="cancelled">İptal</option>
            </select>
            <div class="spacer"></div>
            <button class="btn btn-primary" onclick="OrdersPage.showCreateModal()">+ Yeni Sipariş</button>
        </div>
        <div class="card"><div class="card-body table-wrapper" id="orders-table">Yükleniyor...</div></div>`;
    },
    async afterRender() {
        this.loadOrders();
        document.getElementById('order-status-filter').addEventListener('change', () => this.loadOrders());
    },
    async loadOrders() {
        const el = document.getElementById('orders-table');
        const status = document.getElementById('order-status-filter').value;
        try {
            let url = '/orders/?limit=50';
            if (status) url += `&status=${status}`;
            const data = await api.get(url);
            if (!data.orders?.length) { el.innerHTML = UI.emptyState('📦','Sipariş yok','Henüz sipariş bulunmuyor'); return; }
            el.innerHTML = `<table><thead><tr><th>Sipariş No</th><th>Müşteri</th><th>Ürünler</th><th>Tutar</th><th>Durum</th><th>Tarih</th><th>İşlem</th></tr></thead><tbody>${
                data.orders.map(o => `<tr>
                    <td><strong>#${o.order_number}</strong></td>
                    <td>${o.customer_name||'-'}</td>
                    <td>${o.items?.length||0} kalem</td>
                    <td><strong>${UI.formatMoney(o.total_amount)}</strong></td>
                    <td>${UI.badge(o.status)}</td>
                    <td>${UI.formatDate(o.created_at)}</td>
                    <td><button class="btn-icon" onclick="OrdersPage.showDetail(${o.id})" title="Detay">👁️</button></td>
                </tr>`).join('')
            }</tbody></table>`;
        } catch(e) { el.innerHTML = '<p style="color:var(--danger)">Yüklenemedi</p>'; }
    },
    async showDetail(id) {
        try {
            const o = await api.get(`/orders/${id}`);
            const items = o.items?.map(i => `<tr><td>${i.product_name}</td><td>${i.quantity}</td><td>${UI.formatMoney(i.unit_price)}</td><td>${UI.formatMoney(i.total_price)}</td></tr>`).join('')||'';
            let cargoInfo = '';
            if (o.cargo) {
                cargoInfo = `<div style="margin-top:16px"><h4 style="font-size:14px;margin-bottom:8px">🚚 Kargo Bilgisi</h4>
                    <div class="form-row"><div><strong>Takip:</strong> ${o.cargo.tracking_number}</div><div><strong>Firma:</strong> ${o.cargo.carrier}</div></div>
                    <div style="margin-top:4px"><strong>Durum:</strong> ${UI.badge(o.cargo.status)}</div></div>`;
            }
            const statusOptions = ['pending','confirmed','preparing','shipped','delivered','cancelled'].map(s =>
                `<option value="${s}" ${o.status===s?'selected':''}>${UI.statusLabels[s]||s}</option>`).join('');
            UI.modal(`Sipariş #${o.order_number}`,
                `<div class="form-row"><div class="form-group"><div class="form-label">Müşteri</div><div>${o.customer_name}</div></div><div class="form-group"><div class="form-label">Tarih</div><div>${UI.formatDate(o.created_at)}</div></div></div>
                <div class="form-group"><div class="form-label">Durum</div><select class="form-select" id="order-status-select">${statusOptions}</select></div>
                <h4 style="font-size:14px;margin:16px 0 8px">📋 Sipariş Kalemleri</h4>
                <table><thead><tr><th>Ürün</th><th>Adet</th><th>Birim Fiyat</th><th>Toplam</th></tr></thead><tbody>${items}</tbody></table>
                <div style="text-align:right;margin-top:8px;font-size:16px;font-weight:700">Toplam: ${UI.formatMoney(o.total_amount)}</div>
                ${cargoInfo}
                <div class="form-group" style="margin-top:12px"><div class="form-label">Teslimat Adresi</div><div style="color:var(--text-secondary)">${o.shipping_address||'-'}</div></div>`,
                `<button class="btn btn-secondary" onclick="UI.closeModal()">Kapat</button><button class="btn btn-primary" onclick="OrdersPage.updateStatus(${o.id})">Durumu Güncelle</button>`);
        } catch(e) { UI.toast('Sipariş yüklenemedi','error'); }
    },
    async updateStatus(id) {
        const status = document.getElementById('order-status-select').value;
        try {
            await api.patch(`/orders/${id}/status`, { status });
            UI.closeModal(); UI.toast('Sipariş durumu güncellendi','success'); this.loadOrders();
        } catch(e) { UI.toast(e.message,'error'); }
    },
    async showCreateModal() {
        let customers = [], products = [];
        try { customers = (await api.get('/customers/')).customers; } catch(e) {}
        try { products = (await api.get('/products/')).products; } catch(e) {}
        const custOpts = customers.map(c => `<option value="${c.id}">${c.name}</option>`).join('');
        const prodOpts = products.filter(p=>p.stock_quantity>0).map(p => `<option value="${p.id}">${p.name} (${UI.formatMoney(p.price)})</option>`).join('');
        UI.modal('Yeni Sipariş',
            `<div class="form-group"><label class="form-label">Müşteri</label><select class="form-select" id="new-order-customer">${custOpts}</select></div>
            <div class="form-group"><label class="form-label">Ürün</label><select class="form-select" id="new-order-product">${prodOpts}</select></div>
            <div class="form-group"><label class="form-label">Adet</label><input class="form-input" id="new-order-qty" type="number" value="1" min="1"></div>`,
            `<button class="btn btn-secondary" onclick="UI.closeModal()">İptal</button><button class="btn btn-primary" onclick="OrdersPage.createOrder()">Sipariş Oluştur</button>`);
    },
    async createOrder() {
        try {
            await api.post('/orders/', {
                customer_id: parseInt(document.getElementById('new-order-customer').value),
                items: [{ product_id: parseInt(document.getElementById('new-order-product').value), quantity: parseInt(document.getElementById('new-order-qty').value) }]
            });
            UI.closeModal(); UI.toast('Sipariş oluşturuldu','success'); this.loadOrders();
        } catch(e) { UI.toast(e.message,'error'); }
    }
};
