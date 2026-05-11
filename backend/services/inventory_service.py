"""
Stok ve Envanter Yönetim Servisi.
Otomatik stok izleme, kritik eşik uyarıları ve yenileme önerileri.
"""

from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from models import Product, InventoryAlert, AlertType, Notification, OrderItem
from sqlalchemy import func


class InventoryService:
    """Stok yönetimi iş mantığı."""

    def check_stock_levels(self, db: Session) -> list:
        """
        Tüm ürünlerin stok seviyelerini kontrol et.
        Kritik eşiğin altındaki ürünler için uyarı oluştur.
        """
        products = db.query(Product).filter(Product.is_active == True).all()
        alerts = []

        for product in products:
            if product.stock_quantity <= 0:
                alert = self._create_alert(
                    db, product, AlertType.OUT_OF_STOCK,
                    f"{product.name} stoğu tükendi!",
                    f"Acil olarak {product.name} tedarik edilmeli. "
                    f"Son 30 günde ortalama satış verilerine göre "
                    f"en az {product.min_stock_threshold * 3} {product.unit} sipariş verilmesi önerilir."
                )
                if alert:
                    alerts.append(alert)

            elif product.stock_quantity <= product.min_stock_threshold:
                alert = self._create_alert(
                    db, product, AlertType.LOW_STOCK,
                    f"{product.name} stoğu kritik seviyede: {product.stock_quantity} {product.unit} kaldı.",
                    f"Mevcut stok {product.stock_quantity} {product.unit}. "
                    f"Eşik değeri: {product.min_stock_threshold} {product.unit}. "
                    f"Tedarikçiye sipariş verilmesi önerilir."
                )
                if alert:
                    alerts.append(alert)

        return alerts

    def _create_alert(self, db: Session, product: Product, alert_type: AlertType,
                      message: str, suggestion: str) -> dict:
        """
        Stok uyarısı oluştur (aynı uyarı yoksa).
        """
        # Aynı ürün için aynı tipte çözülmemiş uyarı var mı?
        existing = db.query(InventoryAlert).filter(
            InventoryAlert.product_id == product.id,
            InventoryAlert.alert_type == alert_type,
            InventoryAlert.is_resolved == False
        ).first()

        if existing:
            return None

        alert = InventoryAlert(
            product_id=product.id,
            alert_type=alert_type,
            message=message,
            suggested_action=suggestion
        )
        db.add(alert)

        # Bildirim de oluştur
        notification = Notification(
            title=f"Stok Uyarısı: {product.name}",
            message=message,
            type=alert_type,
            link=f"/inventory?product={product.id}"
        )
        db.add(notification)

        db.commit()
        db.refresh(alert)

        return alert.to_dict()

    def get_active_alerts(self, db: Session) -> list:
        """Aktif (çözülmemiş) stok uyarılarını getir."""
        alerts = db.query(InventoryAlert).filter(
            InventoryAlert.is_resolved == False
        ).order_by(InventoryAlert.created_at.desc()).all()
        return [a.to_dict() for a in alerts]

    def resolve_alert(self, db: Session, alert_id: int) -> dict:
        """Uyarıyı çözüldü olarak işaretle."""
        alert = db.query(InventoryAlert).filter(InventoryAlert.id == alert_id).first()
        if alert:
            alert.is_resolved = True
            db.commit()
            db.refresh(alert)
            return alert.to_dict()
        return None

    def get_reorder_suggestion(self, db: Session, product_id: int) -> dict:
        """
        AI destekli yenileme önerisi oluştur.
        Geçmiş satış verilerine dayanarak tahmini sipariş miktarı hesapla.
        """
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return None

        # Son 30 günlük satışları hesapla
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        total_sold = db.query(func.sum(OrderItem.quantity)).join(
            OrderItem.order
        ).filter(
            OrderItem.product_id == product_id,
            OrderItem.order.has(created_at=thirty_days_ago)
        ).scalar() or 0

        # Günlük ortalama satış
        daily_avg = total_sold / 30 if total_sold > 0 else 2  # minimum 2

        # 2 haftalık stok önerisi
        suggested_quantity = int(daily_avg * 14)
        estimated_cost = suggested_quantity * product.price * 0.6  # maliyet tahmini (%60)

        return {
            "product_id": product.id,
            "product_name": product.name,
            "current_stock": product.stock_quantity,
            "unit": product.unit,
            "daily_avg_sales": round(daily_avg, 1),
            "suggested_quantity": max(suggested_quantity, product.min_stock_threshold),
            "estimated_cost": round(estimated_cost, 2),
            "days_until_stockout": int(product.stock_quantity / daily_avg) if daily_avg > 0 else 999,
            "recommendation": f"{product.name} için {max(suggested_quantity, product.min_stock_threshold)} "
                            f"{product.unit} sipariş verilmesi önerilir. "
                            f"Tahmini maliyet: {estimated_cost:.2f} ₺. "
                            f"Mevcut stokla yaklaşık {int(product.stock_quantity / daily_avg) if daily_avg > 0 else '∞'} gün yeterli."
        }

    def generate_supplier_draft(self, db: Session, product_id: int) -> dict:
        """Tedarikçiye sipariş taslak maili oluştur."""
        suggestion = self.get_reorder_suggestion(db, product_id)
        if not suggestion:
            return None

        draft = {
            "subject": f"Sipariş Talebi - {suggestion['product_name']}",
            "body": f"""Sayın Tedarikçi,

Aşağıdaki ürün için sipariş vermek istiyoruz:

Ürün: {suggestion['product_name']}
Miktar: {suggestion['suggested_quantity']} {suggestion['unit']}
Mevcut Stok: {suggestion['current_stock']} {suggestion['unit']}

Lütfen fiyat ve teslimat süresi bilgilerini iletiniz.

Saygılarımızla,
YZTA E-Ticaret""",
            "suggestion": suggestion
        }
        return draft


inventory_service = InventoryService()
