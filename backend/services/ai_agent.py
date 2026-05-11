"""
AI Agent Servisi - Mock Implementation.
Doğal dil sorguları işler, intent tanımlama ve bağlama uygun yanıt üretme.
Gerçek Gemini API entegrasyonu için bu dosya genişletilecek.
"""

import json
import re
from datetime import datetime


class AIAgent:
    """
    Mock AI Agent - KOBİ e-ticaret asistanı.
    Müşteri sorularını anlayıp ilgili sistemlerle etkileşime geçer.
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

    def __init__(self):
        self.conversation_history = []

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
        Kullanıcı mesajına bağlama uygun yanıt üret.
        
        Args:
            message: Kullanıcı mesajı
            db_context: Veritabanından çekilen bağlam verileri
            
        Returns:
            dict: {"response": str, "intent": str, "actions": list, "data": dict}
        """
        intent, params = self.detect_intent(message)

        # Yanıt üretme
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
