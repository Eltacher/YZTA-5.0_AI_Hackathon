/* ─── Ortak UI Bileşenleri ─── */
const UI = {
    statusLabels: {
        pending: '⏳ Beklemede', confirmed: '✅ Onaylandı', preparing: '📦 Hazırlanıyor',
        shipped: '🚚 Kargoda', delivered: '✅ Teslim Edildi', cancelled: '❌ İptal',
        delayed: '⚠️ Gecikmiş', picked_up: '🏪 Kurye Aldı', in_transit: '🚛 Yolda',
        out_for_delivery: '🚚 Dağıtımda', returned: '↩️ İade',
        todo: '📋 Yapılacak', in_progress: '🔄 Devam Ediyor', done: '✅ Tamamlandı',
        low: 'Düşük', medium: 'Orta', high: 'Yüksek', urgent: 'Acil'
    },

    badge(status) {
        const label = this.statusLabels[status] || status;
        return `<span class="badge badge-${status}">${label}</span>`;
    },

    toast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        const icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };
        const el = document.createElement('div');
        el.className = `toast ${type}`;
        el.innerHTML = `<span>${icons[type] || ''}</span><span>${message}</span>`;
        container.appendChild(el);
        setTimeout(() => { el.style.opacity = '0'; setTimeout(() => el.remove(), 300); }, 4000);
    },

    modal(title, bodyHTML, footerHTML = '') {
        const existing = document.querySelector('.modal-overlay');
        if (existing) existing.remove();
        const overlay = document.createElement('div');
        overlay.className = 'modal-overlay';
        overlay.innerHTML = `<div class="modal">
            <div class="modal-header"><h3>${title}</h3><button class="modal-close" onclick="this.closest('.modal-overlay').remove()">✕</button></div>
            <div class="modal-body">${bodyHTML}</div>
            ${footerHTML ? `<div class="modal-footer">${footerHTML}</div>` : ''}
        </div>`;
        overlay.addEventListener('click', e => { if (e.target === overlay) overlay.remove(); });
        document.body.appendChild(overlay);
        return overlay;
    },

    closeModal() {
        const m = document.querySelector('.modal-overlay');
        if (m) m.remove();
    },

    emptyState(icon, title, desc) {
        return `<div class="empty-state"><div class="empty-icon">${icon}</div><h4>${title}</h4><p>${desc}</p></div>`;
    },

    formatDate(iso) {
        if (!iso) return '-';
        const d = new Date(iso);
        return d.toLocaleDateString('tr-TR', { day: '2-digit', month: '2-digit', year: 'numeric' });
    },

    formatMoney(val) {
        return Number(val || 0).toLocaleString('tr-TR', { minimumFractionDigits: 2 }) + ' ₺';
    },

    barChart(data, maxHeight = 160) {
        if (!data.length) return '<p class="empty-state">Veri yok</p>';
        const max = Math.max(...data.map(d => d.value), 1);
        let bars = data.map(d => {
            const h = Math.max((d.value / max) * maxHeight, 4);
            return `<div class="bar-col"><span class="bar-value">${d.value}</span><div class="bar" style="height:${h}px"></div><span class="bar-label">${d.label}</span></div>`;
        }).join('');
        return `<div class="bar-chart" style="height:${maxHeight + 40}px">${bars}</div>`;
    }
};
