/* ─── Analitik Modülü ─── */
const AnalyticsPage = {
    async render() {
        let sales = {};
        try { sales = await api.get('/analytics/sales-summary?days=30'); } catch(e) {}
        return `<div class="stats-grid">
            <div class="stat-card purple"><div class="stat-icon">💰</div><div class="stat-value">${UI.formatMoney(sales.total_revenue)}</div><div class="stat-label">Son 30 Gün Ciro</div></div>
            <div class="stat-card teal"><div class="stat-icon">📦</div><div class="stat-value">${sales.total_orders||0}</div><div class="stat-label">Toplam Sipariş</div></div>
            <div class="stat-card yellow"><div class="stat-icon">📊</div><div class="stat-value">${UI.formatMoney(sales.avg_order_value)}</div><div class="stat-label">Ort. Sipariş Değeri</div></div>
        </div>
        <div class="grid-2">
            <div class="card"><div class="card-header"><h3>📈 Günlük Gelir (14 Gün)</h3></div><div class="card-body" id="analytics-revenue-chart">Yükleniyor...</div></div>
            <div class="card"><div class="card-header"><h3>🏆 En Çok Satan Ürünler</h3></div><div class="card-body" id="analytics-top-products">Yükleniyor...</div></div>
        </div>
        <div class="grid-2" style="margin-top:20px">
            <div class="card"><div class="card-header"><h3>📊 Kategori Dağılımı</h3></div><div class="card-body" id="analytics-categories">Yükleniyor...</div></div>
            <div class="card"><div class="card-header"><h3>🔮 AI Talep Tahmini</h3></div><div class="card-body" id="analytics-forecast">Yükleniyor...</div></div>
        </div>`;
    },
    async afterRender() {
        this.loadRevenueChart();
        this.loadTopProducts();
        this.loadCategories();
        this.loadForecast();
    },
    async loadRevenueChart() {
        const el = document.getElementById('analytics-revenue-chart');
        try {
            const data = await api.get('/analytics/daily-revenue?days=14');
            el.innerHTML = UI.barChart(data.map(d => ({ label: d.label, value: d.revenue })));
        } catch(e) { el.innerHTML = '<p style="color:var(--text-muted)">Yüklenemedi</p>'; }
    },
    async loadTopProducts() {
        const el = document.getElementById('analytics-top-products');
        try {
            const products = await api.get('/analytics/top-products?limit=5');
            if (!products?.length) { el.innerHTML = UI.emptyState('📊','Veri yok','Henüz satış verisi yok'); return; }
            el.innerHTML = `<table><thead><tr><th>Ürün</th><th>Satış</th><th>Ciro</th></tr></thead><tbody>${
                products.map((p,i) => `<tr><td>${['🥇','🥈','🥉','4️⃣','5️⃣'][i]} ${p.name}</td><td>${p.total_sold} adet</td><td>${UI.formatMoney(p.total_revenue)}</td></tr>`).join('')
            }</tbody></table>`;
        } catch(e) { el.innerHTML = '<p style="color:var(--text-muted)">Yüklenemedi</p>'; }
    },
    async loadCategories() {
        const el = document.getElementById('analytics-categories');
        try {
            const cats = await api.get('/analytics/category-breakdown');
            if (!cats?.length) { el.innerHTML = UI.emptyState('📊','Veri yok','Henüz kategori verisi yok'); return; }
            el.innerHTML = UI.barChart(cats.map(c => ({ label: c.category, value: c.revenue })));
        } catch(e) { el.innerHTML = '<p style="color:var(--text-muted)">Yüklenemedi</p>'; }
    },
    async loadForecast() {
        const el = document.getElementById('analytics-forecast');
        try {
            const forecasts = await api.get('/analytics/forecast');
            if (!forecasts?.length) { el.innerHTML = UI.emptyState('🔮','Tahmin yok','Yeterli veri yok'); return; }
            el.innerHTML = forecasts.map(f => `<div class="alert-item">
                <span class="alert-icon">📦</span>
                <div class="alert-content">
                    <div class="alert-title">${f.product_name}</div>
                    <div class="alert-desc">Haftalık ort: ${f.avg_weekly_sales} | Tahmin: <strong>${f.predicted_next_week}</strong> adet</div>
                    <div class="alert-action">💡 ${f.recommendation}</div>
                </div></div>`).join('');
        } catch(e) { el.innerHTML = '<p style="color:var(--text-muted)">Yüklenemedi</p>'; }
    }
};
