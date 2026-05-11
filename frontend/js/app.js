/* ─── SPA Router & Ana Uygulama ─── */
const App = {
    pages: {
        dashboard:  { module: DashboardPage,  title: 'Dashboard',       subtitle: 'Genel bakış ve anlık durum' },
        products:   { module: ProductsPage,   title: 'Ürünler',         subtitle: 'Ürün kataloğu ve stok yönetimi' },
        orders:     { module: OrdersPage,     title: 'Siparişler',      subtitle: 'Sipariş takibi ve yönetimi' },
        cargo:      { module: CargoPage,      title: 'Kargo',           subtitle: 'Kargo takibi ve dağıtım' },
        inventory:  { module: InventoryPage,  title: 'Stok Yönetimi',   subtitle: 'Stok kontrol ve uyarılar' },
        tasks:      { module: TasksPage,      title: 'Görevler',        subtitle: 'İş akışı ve görev yönetimi' },
        analytics:  { module: AnalyticsPage,  title: 'Analitik',        subtitle: 'Satış analizi ve içgörüler' },
        customers:  { module: CustomersPage,  title: 'Müşteriler',      subtitle: 'Müşteri kayıtları' },
    },

    currentPage: null,

    init() {
        // Navigasyon
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                this.navigate(item.dataset.page);
            });
        });

        // Bildirimler
        document.getElementById('notification-btn').addEventListener('click', () => this.toggleNotifications());
        document.getElementById('mark-all-read-btn').addEventListener('click', () => this.markAllRead());

        // Sidebar toggle (mobil)
        document.getElementById('sidebar-toggle').addEventListener('click', () => {
            document.getElementById('sidebar').classList.toggle('open');
        });

        // Chat modülü
        ChatModule.init();

        // URL hash'ten sayfa belirle
        const hash = location.hash.replace('#', '') || 'dashboard';
        this.navigate(hash);

        // Bildirimleri yükle
        this.loadNotificationCount();
        setInterval(() => this.loadNotificationCount(), 30000);
    },

    async navigate(page) {
        if (!this.pages[page]) page = 'dashboard';
        this.currentPage = page;

        // Nav aktif durumu
        document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
        const activeNav = document.querySelector(`[data-page="${page}"]`);
        if (activeNav) activeNav.classList.add('active');

        // Başlık güncelle
        const pageConfig = this.pages[page];
        document.getElementById('page-title').textContent = pageConfig.title;
        document.getElementById('page-subtitle').textContent = pageConfig.subtitle;
        document.title = `${pageConfig.title} — YZTA AI E-Ticaret`;

        // URL hash güncelle
        location.hash = page;

        // İçerik yükle
        const content = document.getElementById('page-content');
        content.innerHTML = '<div class="loading-screen"><div class="loader"></div><p>Yükleniyor...</p></div>';

        try {
            const html = await pageConfig.module.render();
            content.innerHTML = html;
            if (pageConfig.module.afterRender) {
                await pageConfig.module.afterRender();
            }
        } catch (e) {
            console.error('Page render error:', e);
            content.innerHTML = `<div class="empty-state"><div class="empty-icon">❌</div><h4>Sayfa yüklenemedi</h4><p>${e.message}</p></div>`;
        }

        // Mobilde sidebar kapat
        document.getElementById('sidebar').classList.remove('open');
    },

    async loadNotificationCount() {
        try {
            const data = await api.get('/notifications/count');
            const badge = document.getElementById('notification-count');
            if (data.count > 0) {
                badge.textContent = data.count;
                badge.style.display = 'flex';
            } else {
                badge.style.display = 'none';
            }
        } catch(e) {}
    },

    async toggleNotifications() {
        const panel = document.getElementById('notification-panel');
        const isVisible = panel.style.display !== 'none';
        if (isVisible) {
            panel.style.display = 'none';
            return;
        }
        panel.style.display = 'block';
        try {
            const notifs = await api.get('/notifications');
            const list = document.getElementById('notification-list');
            if (!notifs?.length) {
                list.innerHTML = '<div style="padding:20px;text-align:center;color:var(--text-muted)">Bildirim yok</div>';
                return;
            }
            list.innerHTML = notifs.map(n => `<div class="notif-item ${n.is_read?'':'unread'}" onclick="App.readNotification(${n.id},'${n.link||''}')">
                <div class="notif-title">${n.title}</div>
                <div class="notif-message">${n.message}</div>
                <div class="notif-time">${UI.formatDate(n.created_at)}</div>
            </div>`).join('');
        } catch(e) {}
    },

    async readNotification(id, link) {
        try { await api.patch(`/notifications/${id}/read`); } catch(e) {}
        document.getElementById('notification-panel').style.display = 'none';
        this.loadNotificationCount();
        if (link) {
            const page = link.replace('/','').split('?')[0];
            if (this.pages[page]) this.navigate(page);
        }
    },

    async markAllRead() {
        try { await api.post('/notifications/read-all'); } catch(e) {}
        this.loadNotificationCount();
        this.toggleNotifications();
    }
};

// Uygulama başlat
document.addEventListener('DOMContentLoaded', () => App.init());
