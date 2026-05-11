/* ─── Ürünler Modülü ─── */
const ProductsPage = {
    async render() {
        return `<div class="filter-bar">
            <select class="form-select" id="product-category-filter"><option value="">Tüm Kategoriler</option></select>
            <input class="form-input" id="product-search" placeholder="Ürün ara..." style="max-width:220px">
            <label style="display:flex;align-items:center;gap:6px;font-size:13px;color:var(--text-secondary)"><input type="checkbox" id="product-low-stock"> Düşük Stok</label>
            <div class="spacer"></div>
            <button class="btn btn-primary" onclick="ProductsPage.showAddModal()">+ Yeni Ürün</button>
        </div>
        <div id="products-container">Yükleniyor...</div>`;
    },
    async afterRender() {
        this.loadCategories();
        this.loadProducts();
        document.getElementById('product-search').addEventListener('input', () => this.loadProducts());
        document.getElementById('product-category-filter').addEventListener('change', () => this.loadProducts());
        document.getElementById('product-low-stock').addEventListener('change', () => this.loadProducts());
    },
    async loadCategories() {
        try {
            const cats = await api.get('/products/categories');
            const sel = document.getElementById('product-category-filter');
            cats.forEach(c => { const o = document.createElement('option'); o.value = c; o.textContent = c; sel.appendChild(o); });
        } catch(e) {}
    },
    async loadProducts() {
        const container = document.getElementById('products-container');
        const search = document.getElementById('product-search').value;
        const category = document.getElementById('product-category-filter').value;
        const lowStock = document.getElementById('product-low-stock').checked;
        try {
            let url = '/products/?limit=50';
            if (search) url += `&search=${encodeURIComponent(search)}`;
            if (category) url += `&category=${encodeURIComponent(category)}`;
            if (lowStock) url += '&low_stock=true';
            const data = await api.get(url);
            if (!data.products?.length) { container.innerHTML = UI.emptyState('🏷️','Ürün bulunamadı','Henüz ürün eklenmemiş'); return; }
            container.innerHTML = `<div class="product-grid">${data.products.map(p => this.productCard(p)).join('')}</div>`;
        } catch(e) { container.innerHTML = '<p style="color:var(--danger)">Yüklenemedi</p>'; }
    },
    productCard(p) {
        const icons = {'Zeytinyağı':'🫒','Sebze':'🍅','Bal':'🍯','Kuru Meyve':'🥜','Süt Ürünleri':'🧀','El Sanatları':'🧶','Konserve':'🥫'};
        const icon = icons[p.category] || '📦';
        let stockClass = 'stock-ok', stockText = `${p.stock_quantity} ${p.unit}`;
        if (p.stock_quantity <= 0) { stockClass = 'stock-out'; stockText = 'Tükendi'; }
        else if (p.is_low_stock) { stockClass = 'stock-low'; stockText = `⚠️ ${p.stock_quantity} ${p.unit}`; }
        return `<div class="product-card" onclick="ProductsPage.showDetail(${p.id})">
            <div class="product-img">${icon}</div>
            <div class="product-info"><div class="product-name">${p.name}</div><div class="product-category">${p.category||'Genel'}</div>
            <div class="product-footer"><span class="product-price">${UI.formatMoney(p.price)}</span><span class="product-stock ${stockClass}">${stockText}</span></div></div></div>`;
    },
    async showDetail(id) {
        try {
            const p = await api.get(`/products/${id}`);
            UI.modal(p.name, `<div style="text-align:center;font-size:48px;padding:16px">${{'Zeytinyağı':'🫒','Sebze':'🍅','Bal':'🍯','Kuru Meyve':'🥜','Süt Ürünleri':'🧀','El Sanatları':'🧶','Konserve':'🥫'}[p.category]||'📦'}</div>
                <div class="form-row"><div class="form-group"><div class="form-label">SKU</div><div>${p.sku}</div></div><div class="form-group"><div class="form-label">Kategori</div><div>${p.category||'-'}</div></div></div>
                <div class="form-row"><div class="form-group"><div class="form-label">Fiyat</div><div style="font-size:20px;font-weight:700;color:var(--accent-light)">${UI.formatMoney(p.price)}</div></div><div class="form-group"><div class="form-label">Stok</div><div>${p.stock_quantity} ${p.unit}</div></div></div>
                <div class="form-group"><div class="form-label">Açıklama</div><div style="color:var(--text-secondary)">${p.description||'-'}</div></div>
                <div class="form-group"><div class="form-label">Min Stok Eşiği</div><div>${p.min_stock_threshold} ${p.unit}</div></div>`,
                `<button class="btn btn-secondary" onclick="UI.closeModal()">Kapat</button><button class="btn btn-primary" onclick="ProductsPage.showEditModal(${p.id})">Düzenle</button>`);
        } catch(e) { UI.toast('Ürün yüklenemedi','error'); }
    },
    showAddModal() {
        UI.modal('Yeni Ürün', `<div class="form-row"><div class="form-group"><label class="form-label">Ürün Adı</label><input class="form-input" id="p-name"></div><div class="form-group"><label class="form-label">SKU</label><input class="form-input" id="p-sku"></div></div>
            <div class="form-row"><div class="form-group"><label class="form-label">Fiyat (₺)</label><input class="form-input" id="p-price" type="number"></div><div class="form-group"><label class="form-label">Stok</label><input class="form-input" id="p-stock" type="number"></div></div>
            <div class="form-row"><div class="form-group"><label class="form-label">Birim</label><input class="form-input" id="p-unit" value="adet"></div><div class="form-group"><label class="form-label">Kategori</label><input class="form-input" id="p-category"></div></div>
            <div class="form-group"><label class="form-label">Açıklama</label><textarea class="form-textarea" id="p-desc"></textarea></div>`,
            `<button class="btn btn-secondary" onclick="UI.closeModal()">İptal</button><button class="btn btn-primary" onclick="ProductsPage.saveProduct()">Kaydet</button>`);
    },
    async saveProduct() {
        try {
            await api.post('/products/', {
                name: document.getElementById('p-name').value,
                sku: document.getElementById('p-sku').value,
                price: parseFloat(document.getElementById('p-price').value),
                stock_quantity: parseInt(document.getElementById('p-stock').value) || 0,
                unit: document.getElementById('p-unit').value || 'adet',
                category: document.getElementById('p-category').value,
                description: document.getElementById('p-desc').value
            });
            UI.closeModal(); UI.toast('Ürün oluşturuldu','success'); this.loadProducts();
        } catch(e) { UI.toast(e.message,'error'); }
    },
    async showEditModal(id) {
        UI.closeModal();
        const p = await api.get(`/products/${id}`);
        UI.modal('Ürün Düzenle', `<div class="form-row"><div class="form-group"><label class="form-label">Ürün Adı</label><input class="form-input" id="pe-name" value="${p.name}"></div><div class="form-group"><label class="form-label">Fiyat</label><input class="form-input" id="pe-price" type="number" value="${p.price}"></div></div>
            <div class="form-row"><div class="form-group"><label class="form-label">Stok</label><input class="form-input" id="pe-stock" type="number" value="${p.stock_quantity}"></div><div class="form-group"><label class="form-label">Min Eşik</label><input class="form-input" id="pe-threshold" type="number" value="${p.min_stock_threshold}"></div></div>`,
            `<button class="btn btn-secondary" onclick="UI.closeModal()">İptal</button><button class="btn btn-primary" onclick="ProductsPage.updateProduct(${id})">Güncelle</button>`);
    },
    async updateProduct(id) {
        try {
            await api.put(`/products/${id}`, {
                name: document.getElementById('pe-name').value,
                price: parseFloat(document.getElementById('pe-price').value),
                stock_quantity: parseInt(document.getElementById('pe-stock').value),
                min_stock_threshold: parseInt(document.getElementById('pe-threshold').value)
            });
            UI.closeModal(); UI.toast('Ürün güncellendi','success'); this.loadProducts();
        } catch(e) { UI.toast(e.message,'error'); }
    }
};
