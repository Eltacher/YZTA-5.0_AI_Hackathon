# 🚀 YZTA — AI Destekli E-Ticaret Platformu

**YZTA 5.0 AI Hackathon** kapsamında geliştirilen, KOBİ'ler ve kooperatifler için AI destekli e-ticaret yönetim platformu.

## 🎯 Proje Amacı

Küçük ve orta ölçekli işletmelerin günlük operasyonlarını yapay zeka ile otomatikleştirmek:
- Müşteri sorularını AI ile otomatik yanıtlama
- Stok ve sipariş takibini akıllandırma
- Kargo gecikmelerini proaktif tespit
- İş akışlarını otomatik planlama

## 📦 Modüller

| Modül | Açıklama |
|-------|----------|
| 💬 **AI Chatbot** | Doğal dil ile sipariş, stok, kargo sorgulama |
| 📦 **Sipariş Yönetimi** | CRUD, durum takibi, anlık güncellemeler |
| 🚚 **Kargo Takip** | Durum izleme, gecikme tespiti, otomatik bildirim |
| 📊 **Stok Yönetimi** | Kritik eşik uyarıları, AI yenileme önerileri |
| ✅ **Görev Yönetimi** | Otomatik günlük görev oluşturma, ekip atama |
| 📈 **Analitik** | Satış trendleri, AI talep tahmini |

## 🏗️ Mimari

```
┌─────────────────────────────────────────┐
│           Frontend (SPA)                │
│    HTML/CSS/JS - Koyu Tema              │
├─────────────────────────────────────────┤
│           FastAPI Backend               │
│    REST API + WebSocket                 │
├───────────┬─────────────┬───────────────┤
│ AI Agent  │  Servisler  │  Router'lar   │
│ (Gemini)  │  İş Mantığı │  API Katmanı  │
├───────────┴─────────────┴───────────────┤
│     SQLite + SQLAlchemy ORM             │
└─────────────────────────────────────────┘
```

## 🛠️ Teknolojiler

- **Backend:** Python, FastAPI, SQLAlchemy, SQLite
- **Frontend:** HTML5, CSS3, Vanilla JavaScript (SPA)
- **AI:** Google Gemini API (mock mode destekli)
- **Gerçek Zamanlı:** WebSocket

## 🚀 Kurulum ve Çalıştırma

### 1. Bağımlılıkları kur
```bash
cd backend
pip install -r requirements.txt
```

### 2. Demo verileri yükle
```bash
python seed_data.py
```

### 3. Backend'i başlat
```bash
uvicorn main:app --reload --port 8000
```

### 4. Frontend'e eriş
Tarayıcıda `http://localhost:8000` adresini aç.

## 🤖 AI Yaklaşımı

### Agent Mimarisi
- **Intent Detection:** Regex tabanlı doğal dil sorgulama
- **Context Building:** Veritabanından bağlam toplama
- **Response Generation:** Şablon tabanlı akıllı yanıt üretme
- **Action Execution:** Sorgu sonuçlarına göre otomatik aksiyon

### Örnek Senaryolar
```
Kullanıcı: "128 numaralı siparişim nerede?"
→ Sistem sipariş + kargo bilgisini otomatik çeker ve yanıtlar

Kullanıcı: "Stok durumu göster"
→ Tüm ürünlerin stok seviyelerini raporlar

Kullanıcı: "Kritik stok uyarıları"
→ Eşik altındaki ürünleri ve AI önerilerini listeler
```

## 📁 Proje Yapısı

```
YZTA/
├── backend/
│   ├── main.py              # FastAPI uygulama
│   ├── database.py           # Veritabanı bağlantısı
│   ├── models.py             # ORM modelleri
│   ├── seed_data.py          # Demo veriler
│   ├── routers/              # API endpoint'leri
│   │   ├── products.py, orders.py, customers.py
│   │   ├── cargo.py, inventory.py, tasks.py
│   │   ├── analytics.py, ai_chat.py
│   └── services/             # İş mantığı servisleri
│       ├── ai_agent.py       # AI Agent
│       ├── inventory_service.py, cargo_service.py
│       ├── workflow_service.py, notification_service.py
├── frontend/
│   ├── index.html            # SPA shell
│   ├── css/styles.css        # Tasarım sistemi
│   └── js/                   # Modüler JavaScript
└── README.md
```

## 👥 Ekip

YZTA 5.0 AI Hackathon Ekibi

## 📄 Lisans

Bu proje YZTA 5.0 Hackathon kapsamında geliştirilmiştir.
