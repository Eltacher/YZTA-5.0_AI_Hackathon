/* ─── Müşteriler Modülü ─── */
const CustomersPage = {
    async render() {
        return `<div class="filter-bar">
            <input class="form-input" id="customer-search" placeholder="Müşteri ara..." style="max-width:260px">
            <div class="spacer"></div>
            <button class="btn btn-primary" onclick="CustomersPage.showAddModal()">+ Yeni Müşteri</button>
        </div>
        <div class="card"><div class="card-body table-wrapper" id="customers-table">Yükleniyor...</div></div>`;
    },
    async afterRender() {
        this.load();
        document.getElementById('customer-search').addEventListener('input', () => this.load());
    },
    async load() {
        const el = document.getElementById('customers-table');
        const s = document.getElementById('customer-search').value;
        try {
            const data = await api.get(`/customers/?search=${encodeURIComponent(s)}`);
            if (!data.customers?.length) { el.innerHTML = UI.emptyState('👥','Müşteri yok','Henüz müşteri kaydı yok'); return; }
            el.innerHTML = `<table><thead><tr><th>Ad</th><th>E-posta</th><th>Telefon</th><th>Şehir</th><th>Kayıt</th></tr></thead><tbody>${
                data.customers.map(c => `<tr><td><strong>${c.name}</strong></td><td>${c.email}</td><td>${c.phone||'-'}</td><td>${c.city||'-'}</td><td>${UI.formatDate(c.created_at)}</td></tr>`).join('')
            }</tbody></table>`;
        } catch(e) { el.innerHTML = '<p style="color:var(--danger)">Yüklenemedi</p>'; }
    },
    showAddModal() {
        UI.modal('Yeni Müşteri',
            `<div class="form-row"><div class="form-group"><label class="form-label">Ad Soyad</label><input class="form-input" id="c-name"></div><div class="form-group"><label class="form-label">E-posta</label><input class="form-input" id="c-email" type="email"></div></div>
            <div class="form-row"><div class="form-group"><label class="form-label">Telefon</label><input class="form-input" id="c-phone"></div><div class="form-group"><label class="form-label">Şehir</label><input class="form-input" id="c-city"></div></div>
            <div class="form-group"><label class="form-label">Adres</label><textarea class="form-textarea" id="c-address"></textarea></div>`,
            `<button class="btn btn-secondary" onclick="UI.closeModal()">İptal</button><button class="btn btn-primary" onclick="CustomersPage.create()">Kaydet</button>`);
    },
    async create() {
        try {
            await api.post('/customers/', {
                name: document.getElementById('c-name').value,
                email: document.getElementById('c-email').value,
                phone: document.getElementById('c-phone').value,
                city: document.getElementById('c-city').value,
                address: document.getElementById('c-address').value
            });
            UI.closeModal(); UI.toast('Müşteri oluşturuldu','success'); this.load();
        } catch(e) { UI.toast(e.message,'error'); }
    }
};
