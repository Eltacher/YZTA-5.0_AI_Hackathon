"""
AI Agent Servisi - Mock + Gemini Dual Mode.
GEMINI_API_KEY ayarlıysa gerçek Gemini model kullanır,
yoksa mevcut mock yanıtlarla çalışır.
"""

import json
import os
import re
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


class AIAgent:
    """
    Dual-mode AI Agent - KOBİ e-ticaret asistanı.
    Mock fallback + Gemini API desteği.
    """

    # Intent tanımlama desenleri
    INTENT_PATTERNS = {
        "order_query": [
            r"sipariş.*nerede", r"sipariş.*durum", r"sipariş.*takip",
            r"(\d+)\s*numaralı\s*sipariş", r"siparişim.*ne\s*zaman",
            r"order.*status", r"kargom.*nerede"
        ],
        "stock_check": [
            r"stok.*var\s*mı", r"ürün.*mevcut", r"stok.*durum",
            r"(.+)\s*kaldı\s*mı", r"kaç\s*tane.*var"
        ],
        "cargo_track": [
            r"kargo.*takip", r"kargo.*nerede", r"teslimat.*ne\s*zaman",
            r"kargo.*durum", r"gönderi.*takip"
        ],
        "product_info": [
            r"ürün.*bilgi", r"fiyat.*ne\s*kadar", r"ürün.*özellik",
            r"(.+)\s*fiyatı", r"ne\s*kadar"
        ],
        "general_help": [
            r"yardım", r"merhaba", r"selam", r"nasıl.*yardımcı",
            r"neler\s*yapabilir", r"help"
        ],
        "daily_summary": [
            r"günlük\s*özet", r"bugün.*sipariş", r"durum\s*rapor",
            r"özet.*ver", r"bugün\s*ne\s*var"
        ],
        "inventory_alert": [
            r"stok.*uyarı", r"kritik\s*stok", r"azalan\s*ürün",
            r"stok.*bitmek", r"tedarik"
        ]
    }

    SYSTEM_PROMPT = """Sen YZTA AI Asistan'sın — KOBİ'ler ve kooperatifler için e-ticaret yönetim platformunun akıllı asistanısın.

Görevlerin:
- Sipariş takibi ve durumu hakkında bilgi vermek
- Stok seviyeleri ve uyarıları raporlamak
- Kargo takibi ve gecikmeleri bildirmek
- Ürün bilgileri sunmak
- Günlük iş özetleri oluşturmak
- Tedarikçi sipariş önerileri yapmak

Kurallar:
- Türkçe yanıt ver, samimi ama profesyonel ol
- Emoji kullan ama abartma
- Verileri listeleyerek ve madde işaretleriyle sun
- Fiyatları ₺ (Türk Lirası) cinsinden göster
- Kısa ve öz yanıtlar ver, gereksiz açıklama yapma
- **Kalın** metin kullanarak önemli verileri vurgula
- Kullanıcının verdiği bağlam verilerini (context) kullanarak yanıt oluştur
- Bağlam verisi yoksa, kullanıcıyı yönlendir"""

    def __init__(self):
        self.conversation_history = []
        self._gemini_model = None
        self._api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self._init_gemini()

    def _init_gemini(self):
        """Gemini API'yi başlat. Key yoksa veya hata olursa mock'a düş."""
        if not self._api_key:
            print("ℹ️  GEMINI_API_KEY ayarlanmamış → Mock mod aktif")
            return

        try:
            import google.generativeai as genai
            genai.configure(api_key=self._api_key)
            self._gemini_model = genai.GenerativeModel("gemini-2.0-flash")
            # Test çağrısı
            self._gemini_model.generate_content("test", generation_config={"max_output_tokens": 5})
            print("✅ Gemini API bağlantısı başarılı → Gerçek AI mod aktif")
        except Exception as e:
            print(f"⚠️  Gemini API başlatılamadı: {e} → Mock mod aktif")
            self._gemini_model = None

    @property
    def is_gemini_active(self) -> bool:
        return self._gemini_model is not None

    def set_api_key(self, key: str) -> dict:
        """API key'i runtime'da ayarla ve test et."""
        self._api_key = key.strip()
        if not self._api_key:
            self._gemini_model = None
            # .env dosyasını güncelle
            self._update_env_file("")
            return {"success": True, "mode": "mock", "message": "API key kaldırıldı, mock mod aktif"}

        try:
            import google.generativeai as genai
            genai.configure(api_key=self._api_key)
            model = genai.GenerativeModel("gemini-2.0-flash")
            # Doğrulama çağrısı
            model.generate_content("Merhaba", generation_config={"max_output_tokens": 10})
            self._gemini_model = model
            # .env dosyasını güncelle
            self._update_env_file(self._api_key)
            return {"success": True, "mode": "gemini", "message": "Gemini API aktif!"}
        except Exception as e:
            self._gemini_model = None
            return {"success": False, "mode": "mock", "message": f"API key geçersiz: {str(e)}"}

    def _update_env_file(self, key: str):
        """Env dosyasını güncelle."""
        env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
        try:
            lines = []
            found = False
            if os.path.exists(env_path):
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip().startswith("GEMINI_API_KEY"):
                            lines.append(f"GEMINI_API_KEY={key}\n")
                            found = True
                        else:
                            lines.append(line)
            if not found:
                lines.append(f"GEMINI_API_KEY={key}\n")
            with open(env_path, "w", encoding="utf-8") as f:
                f.writelines(lines)
        except Exception:
            pass  # Env yazılamazsa sessizce devam et

    def detect_intent(self, message: str) -> tuple:
        """
        Kullanıcı mesajından intent ve parametreleri çıkar.
        Returns: (intent, params_dict)
        """
        message_lower = message.lower().strip()

        for intent, patterns in self.INTENT_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, message_lower)
                if match:
                    params = {}
                    # Sipariş numarası çıkar
                    order_match = re.search(r'(\d+)\s*(?:numaralı|nolu|no)', message_lower)
                    if order_match:
                        params["order_number"] = order_match.group(1)

                    # Genel sayı çıkar
                    if not params.get("order_number"):
                        num_match = re.search(r'\b(\d+)\b', message_lower)
                        if num_match:
                            params["number"] = num_match.group(1)

                    return intent, params

        return "general_help", {}

    def generate_response(self, message: str, db_context: dict = None) -> dict:
        """
        Kullanıcı mesajına yanıt üret.
        Gemini aktifse gerçek AI, değilse mock yanıt.
        """
        intent, params = self.detect_intent(message)

        # Gemini aktifse: AI ile yanıtla
        if self.is_gemini_active:
            return self._gemini_response(message, intent, db_context)

        # Mock mod: mevcut şablon yanıtlar
        return self._mock_response(message, intent, params, db_context)

    def _gemini_response(self, message: str, intent: str, db_context: dict = None) -> dict:
        """Gemini API ile yanıt üret."""
        try:
            # Bağlam metnini oluştur
            context_text = self._format_context(intent, db_context)

            prompt = f"""{self.SYSTEM_PROMPT}

--- BAĞLAM VERİLERİ ---
{context_text}

--- KULLANICI MESAJI ---
{message}

Yukarıdaki bağlam verilerini kullanarak kullanıcıya yardımcı ol. Markdown formatında yanıt ver."""

            response = self._gemini_model.generate_content(
                prompt,
                generation_config={
                    "max_output_tokens": 1024,
                    "temperature": 0.7,
                }
            )

            return {
                "response": response.text,
                "intent": intent,
                "actions": [f"{intent}_gemini"],
                "data": db_context
            }
        except Exception as e:
            # Gemini hatası → mock'a düş
            print(f"⚠️  Gemini yanıt hatası: {e}, mock'a düşülüyor")
            _, params = self.detect_intent(message)
            return self._mock_response(message, intent, params, db_context)

    def _format_context(self, intent: str, db_context: dict = None) -> str:
        """Bağlam verilerini Gemini'ye okunabilir metne dönüştür."""
        if not db_context:
            return "Bağlam verisi yok."

        parts = []

        if intent == "order_query" and db_context.get("order"):
            o = db_context["order"]
            parts.append(f"Sipariş: #{o.get('order_number')}, Durum: {o.get('status')}, "
                        f"Müşteri: {o.get('customer_name')}, Tutar: {o.get('total_amount', 0):.2f} ₺, "
                        f"Tarih: {str(o.get('created_at', ''))[:10]}")
            if o.get("cargo"):
                c = o["cargo"]
                parts.append(f"Kargo: {c.get('tracking_number')}, Durum: {c.get('status')}, "
                           f"Konum: {c.get('last_location')}")

        elif intent == "stock_check" and db_context.get("products"):
            parts.append("Ürün Stok Durumları:")
            for p in db_context["products"]:
                status = "KRİTİK" if p["stock_quantity"] <= p.get("min_stock_threshold", 10) else "Normal"
                parts.append(f"  - {p['name']}: {p['stock_quantity']} {p.get('unit', 'adet')} ({status})")

        elif intent == "cargo_track" and db_context.get("cargo"):
            c = db_context["cargo"]
            parts.append(f"Kargo: {c.get('tracking_number')}, Firma: {c.get('carrier')}, "
                        f"Durum: {c.get('status')}, Konum: {c.get('last_location')}, "
                        f"Tahmini Teslimat: {str(c.get('estimated_delivery', ''))[:10]}")
            if c.get("is_delayed"):
                parts.append(f"⚠️ GECİKME: {c.get('delay_reason', 'Sebep bilinmiyor')}")

        elif intent == "product_info" and db_context.get("product"):
            p = db_context["product"]
            parts.append(f"Ürün: {p['name']}, Fiyat: {p['price']:.2f} ₺, "
                        f"Stok: {p['stock_quantity']} {p.get('unit', 'adet')}, "
                        f"Kategori: {p.get('category')}, Açıklama: {p.get('description')}")

        elif intent == "daily_summary" and db_context.get("summary"):
            s = db_context["summary"]
            parts.append(f"Bugünkü Siparişler: {s.get('today_orders', 0)}, "
                        f"Bugünkü Ciro: {s.get('today_revenue', 0):.2f} ₺, "
                        f"Bekleyen: {s.get('pending_orders', 0)}, "
                        f"Düşük Stok: {s.get('low_stock_count', 0)}, "
                        f"Geciken Kargo: {s.get('delayed_cargo', 0)}")

        elif intent == "inventory_alert" and db_context.get("alerts"):
            parts.append("Aktif Stok Uyarıları:")
            for a in db_context["alerts"]:
                parts.append(f"  - {a.get('product_name')}: {a.get('message')} | Öneri: {a.get('suggested_action', '-')}")

        return "\n".join(parts) if parts else "Bağlam verisi yok."

    # ─── Mock Yanıt Sistemi ──────────────────────────────────────

    def _mock_response(self, message: str, intent: str, params: dict, db_context: dict = None) -> dict:
        """Mevcut mock şablon yanıtları."""
        if intent == "order_query":
            return self._handle_order_query(params, db_context)
        elif intent == "stock_check":
            return self._handle_stock_check(params, db_context)
        elif intent == "cargo_track":
            return self._handle_cargo_track(params, db_context)
        elif intent == "product_info":
            return self._handle_product_info(params, db_context)
        elif intent == "daily_summary":
            return self._handle_daily_summary(db_context)
        elif intent == "inventory_alert":
            return self._handle_inventory_alert(db_context)
        else:
            return self._handle_general(message)

    def _handle_order_query(self, params: dict, context: dict = None) -> dict:
        """Sipariş sorgularını işle."""
        if context and context.get("order"):
            order = context["order"]
            status_labels = {
                "pending": "⏳ Beklemede",
                "confirmed": "✅ Onaylandı",
                "preparing": "📦 Hazırlanıyor",
                "shipped": "🚚 Kargoya verildi",
                "delivered": "✅ Teslim edildi",
                "cancelled": "❌ İptal edildi"
            }
            status_text = status_labels.get(order.get("status"), order.get("status"))

            response = f"""📋 **Sipariş #{order.get('order_number')}** bilgileri:

• **Durum:** {status_text}
• **Müşteri:** {order.get('customer_name', 'Bilinmiyor')}
• **Toplam Tutar:** {order.get('total_amount', 0):.2f} ₺
• **Tarih:** {order.get('created_at', 'Bilinmiyor')[:10]}"""

            if order.get("cargo"):
                cargo = order["cargo"]
                response += f"""
• **Kargo Takip:** {cargo.get('tracking_number', 'Henüz yok')}
• **Kargo Durumu:** {cargo.get('status', 'Bilinmiyor')}
• **Son Konum:** {cargo.get('last_location', 'Bilinmiyor')}"""

            return {
                "response": response,
                "intent": "order_query",
                "actions": ["order_fetched"],
                "data": order
            }
        else:
            order_num = params.get("order_number", "?")
            return {
                "response": f"🔍 {order_num} numaralı sipariş sistemde bulunamadı. Lütfen sipariş numaranızı kontrol edin.",
                "intent": "order_query",
                "actions": [],
                "data": None
            }

    def _handle_stock_check(self, params: dict, context: dict = None) -> dict:
        """Stok sorgularını işle."""
        if context and context.get("products"):
            products = context["products"]
            lines = ["📊 **Stok Durumu:**\n"]
            for p in products:
                icon = "🔴" if p["stock_quantity"] <= p.get("min_stock_threshold", 10) else "🟢"
                lines.append(f"• {icon} **{p['name']}**: {p['stock_quantity']} {p.get('unit', 'adet')}")

            return {
                "response": "\n".join(lines),
                "intent": "stock_check",
                "actions": ["stock_checked"],
                "data": {"products": products}
            }
        return {
            "response": "📊 Stok bilgileri yükleniyor... Lütfen ürün adını belirtin veya genel stok durumunu görmek için 'stok durumu' yazın.",
            "intent": "stock_check",
            "actions": [],
            "data": None
        }

    def _handle_cargo_track(self, params: dict, context: dict = None) -> dict:
        """Kargo takip sorgularını işle."""
        if context and context.get("cargo"):
            cargo = context["cargo"]
            status_labels = {
                "preparing": "📦 Hazırlanıyor",
                "picked_up": "🏪 Kurye aldı",
                "in_transit": "🚛 Yolda",
                "out_for_delivery": "🚚 Dağıtımda",
                "delivered": "✅ Teslim edildi",
                "delayed": "⚠️ Gecikmiş",
                "returned": "↩️ İade edildi"
            }
            status_text = status_labels.get(cargo.get("status"), cargo.get("status"))

            response = f"""🚚 **Kargo Takip Bilgisi:**

• **Takip No:** {cargo.get('tracking_number')}
• **Kargo Firması:** {cargo.get('carrier', 'Bilinmiyor')}
• **Durum:** {status_text}
• **Son Konum:** {cargo.get('last_location', 'Güncelleniyor...')}
• **Tahmini Teslimat:** {cargo.get('estimated_delivery', 'Belirsiz')[:10] if cargo.get('estimated_delivery') else 'Belirsiz'}"""

            if cargo.get("is_delayed"):
                response += f"\n\n⚠️ **Gecikme Sebebi:** {cargo.get('delay_reason', 'Kargo firmasından bilgi bekleniyor')}"

            return {
                "response": response,
                "intent": "cargo_track",
                "actions": ["cargo_tracked"],
                "data": cargo
            }
        return {
            "response": "🔍 Kargo bilgisi bulunamadı. Sipariş veya takip numaranızı paylaşır mısınız?",
            "intent": "cargo_track",
            "actions": [],
            "data": None
        }

    def _handle_product_info(self, params: dict, context: dict = None) -> dict:
        """Ürün bilgi sorgularını işle."""
        if context and context.get("product"):
            p = context["product"]
            stock_icon = "🟢 Stokta" if p["stock_quantity"] > 0 else "🔴 Tükendi"
            return {
                "response": f"""🏷️ **{p['name']}**

• **Fiyat:** {p['price']:.2f} ₺
• **Stok:** {stock_icon} ({p['stock_quantity']} {p.get('unit', 'adet')})
• **Kategori:** {p.get('category', 'Genel')}
• **Açıklama:** {p.get('description', 'Açıklama yok')}""",
                "intent": "product_info",
                "actions": ["product_fetched"],
                "data": p
            }
        return {
            "response": "🏷️ Hangi ürün hakkında bilgi almak istiyorsunuz? Ürün adını veya kodunu yazabilirsiniz.",
            "intent": "product_info",
            "actions": [],
            "data": None
        }

    def _handle_daily_summary(self, context: dict = None) -> dict:
        """Günlük özet oluştur."""
        if context and context.get("summary"):
            s = context["summary"]
            return {
                "response": f"""📊 **Günlük Özet — {datetime.now().strftime('%d.%m.%Y')}**

📦 **Siparişler:**
• Bugün gelen: **{s.get('new_orders', 0)}** sipariş
• Bekleyen: **{s.get('pending_orders', 0)}** sipariş
• Hazırlanacak: **{s.get('preparing_orders', 0)}** sipariş
• Bugün teslim: **{s.get('delivering_today', 0)}** sipariş

💰 **Satışlar:**
• Bugünkü ciro: **{s.get('today_revenue', 0):.2f} ₺**

📊 **Stok Uyarıları:**
• Kritik seviye: **{s.get('low_stock_count', 0)}** ürün
• Tükenen: **{s.get('out_of_stock_count', 0)}** ürün

🚚 **Kargo:**
• Bekleyen kargo: **{s.get('pending_cargo', 0)}**
• Geciken kargo: **{s.get('delayed_cargo', 0)}**

✅ **Görevler:**
• Bugün tamamlanacak: **{s.get('tasks_due_today', 0)}** görev""",
                "intent": "daily_summary",
                "actions": ["summary_generated"],
                "data": s
            }
        return {
            "response": "📊 Günlük özet hazırlanıyor...",
            "intent": "daily_summary",
            "actions": [],
            "data": None
        }

    def _handle_inventory_alert(self, context: dict = None) -> dict:
        """Stok uyarılarını işle."""
        if context and context.get("alerts"):
            alerts = context["alerts"]
            lines = ["⚠️ **Aktif Stok Uyarıları:**\n"]
            for a in alerts:
                icon = "🔴" if a.get("alert_type") == "out_of_stock" else "🟡"
                lines.append(f"• {icon} **{a.get('product_name')}**: {a.get('message')}")
                if a.get("suggested_action"):
                    lines.append(f"  💡 Öneri: {a['suggested_action']}")
            return {
                "response": "\n".join(lines),
                "intent": "inventory_alert",
                "actions": ["alerts_fetched"],
                "data": {"alerts": alerts}
            }
        return {
            "response": "✅ Şu anda aktif stok uyarısı bulunmuyor.",
            "intent": "inventory_alert",
            "actions": [],
            "data": None
        }

    def _handle_general(self, message: str) -> dict:
        """Genel mesajlara yanıt ver."""
        return {
            "response": f"""👋 Merhaba! Ben **YZTA AI Asistan**, size aşağıdaki konularda yardımcı olabilirim:

• 📦 **Sipariş Takibi** — "128 numaralı siparişim nerede?"
• 📊 **Stok Durumu** — "Domates stoğu var mı?"
• 🚚 **Kargo Takip** — "Kargom nerede?"
• 🏷️ **Ürün Bilgisi** — "Zeytinyağı fiyatı ne kadar?"
• 📋 **Günlük Özet** — "Bugünkü özeti göster"
• ⚠️ **Stok Uyarıları** — "Kritik stok uyarıları"

Sormak istediğinizi yazmanız yeterli! 🚀""",
            "intent": "general_help",
            "actions": [],
            "data": None
        }


# Singleton instance
ai_agent = AIAgent()
