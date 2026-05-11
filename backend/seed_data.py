"""
Demo veri yükleyici.
Sistemi gerçekçi verilerle doldurur: ürünler, müşteriler, siparişler, kargo, görevler.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime, timedelta
import random

from database import engine, SessionLocal, Base
from models import (
    Customer, Product, Order, OrderItem, OrderStatus,
    CargoShipment, CargoStatus, Task, TaskStatus, TaskPriority,
    InventoryAlert, AlertType, Notification
)


def seed():
    """Veritabanını demo verilerle doldur."""
    # Tabloları oluştur
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Mevcut veri varsa atla
    if db.query(Product).count() > 0:
        print("⚠️  Veritabanında zaten veri var. Seed atlanıyor.")
        db.close()
        return

    print("🌱 Demo verileri yükleniyor...")

    # ─── Müşteriler ──────────────────────────────────────────
    customers = [
        Customer(name="Ayşe Yıldız", email="ayse@example.com", phone="0532 111 2233",
                 address="Atatürk Cad. No:15", city="İstanbul"),
        Customer(name="Mehmet Kara", email="mehmet@example.com", phone="0535 222 3344",
                 address="Cumhuriyet Mah. 23. Sok.", city="Ankara"),
        Customer(name="Fatma Demir", email="fatma@example.com", phone="0542 333 4455",
                 address="Kordon Boyu No:8", city="İzmir"),
        Customer(name="Ali Çelik", email="ali@example.com", phone="0505 444 5566",
                 address="Sahil Yolu Cad. No:42", city="Antalya"),
        Customer(name="Zeynep Arslan", email="zeynep@example.com", phone="0533 555 6677",
                 address="Uzun Çarşı No:5", city="Bursa"),
        Customer(name="Hasan Öztürk", email="hasan@example.com", phone="0544 666 7788",
                 address="Liman Mah. 12. Sok.", city="Trabzon"),
        Customer(name="Elif Şahin", email="elif@example.com", phone="0555 777 8899",
                 address="Mevlana Cad. No:33", city="Konya"),
        Customer(name="Emre Aydın", email="emre@example.com", phone="0532 888 9900",
                 address="Kale Mah. No:7", city="Gaziantep"),
    ]
    db.add_all(customers)
    db.flush()
    print(f"  ✅ {len(customers)} müşteri oluşturuldu")

    # ─── Ürünler (Tarım kooperatifi teması) ──────────────────
    products = [
        Product(name="Organik Zeytinyağı", description="Soğuk sıkım, ilk hasat, 1L cam şişe",
                price=450.00, stock_quantity=85, unit="şişe", category="Zeytinyağı",
                sku="ZYT-001", min_stock_threshold=20),
        Product(name="Domates (Sera)", description="Taze sera domatesi, 1 kg",
                price=45.00, stock_quantity=8, unit="kg", category="Sebze",
                sku="SBZ-001", min_stock_threshold=50),
        Product(name="Bal (Süzme)", description="Yayladan toplanan doğal çiçek balı, 500g",
                price=280.00, stock_quantity=42, unit="kavanoz", category="Bal",
                sku="BAL-001", min_stock_threshold=15),
        Product(name="Kuru İncir", description="Aydın kuru inciri, 500g paket",
                price=120.00, stock_quantity=150, unit="paket", category="Kuru Meyve",
                sku="KMY-001", min_stock_threshold=30),
        Product(name="Antep Fıstığı", description="Gaziantep fıstığı, kavrulmuş, 250g",
                price=220.00, stock_quantity=65, unit="paket", category="Kuru Meyve",
                sku="KMY-002", min_stock_threshold=25),
        Product(name="Tulum Peyniri", description="Erzincan tulum peyniri, 500g",
                price=350.00, stock_quantity=3, unit="adet", category="Süt Ürünleri",
                sku="SUT-001", min_stock_threshold=10),
        Product(name="Lavanta Sabunu", description="El yapımı doğal lavanta sabunu",
                price=55.00, stock_quantity=200, unit="adet", category="El Sanatları",
                sku="ELS-001", min_stock_threshold=40),
        Product(name="Çam Balı", description="Muğla çam balı, 1 kg",
                price=380.00, stock_quantity=28, unit="kavanoz", category="Bal",
                sku="BAL-002", min_stock_threshold=10),
        Product(name="Biber Salçası", description="Ev yapımı biber salçası, 650g kavanoz",
                price=95.00, stock_quantity=0, unit="kavanoz", category="Konserve",
                sku="KNS-001", min_stock_threshold=20),
        Product(name="Ceviz İçi", description="Yerli ceviz içi, 500g",
                price=190.00, stock_quantity=55, unit="paket", category="Kuru Meyve",
                sku="KMY-003", min_stock_threshold=20),
        Product(name="Keçi Sütü", description="Taze keçi sütü, 1L",
                price=75.00, stock_quantity=12, unit="şişe", category="Süt Ürünleri",
                sku="SUT-002", min_stock_threshold=15),
        Product(name="El Dokuma Kilim", description="Geleneksel Anadolu el dokuma kilim, 120x180cm",
                price=1250.00, stock_quantity=7, unit="adet", category="El Sanatları",
                sku="ELS-002", min_stock_threshold=3),
    ]
    db.add_all(products)
    db.flush()
    print(f"  ✅ {len(products)} ürün oluşturuldu")

    # ─── Siparişler ──────────────────────────────────────────
    statuses = [OrderStatus.PENDING, OrderStatus.CONFIRMED, OrderStatus.PREPARING,
                OrderStatus.SHIPPED, OrderStatus.DELIVERED, OrderStatus.DELIVERED]
    orders_data = []

    for i in range(20):
        customer = random.choice(customers)
        days_ago = random.randint(0, 30)
        status = random.choice(statuses)

        order = Order(
            order_number=f"SIP-2605-{1000 + i}",
            customer_id=customer.id,
            status=status,
            shipping_address=customer.address,
            created_at=datetime.utcnow() - timedelta(days=days_ago, hours=random.randint(0, 23)),
        )
        db.add(order)
        db.flush()

        # 1-4 ürün ekle
        num_items = random.randint(1, 4)
        selected_products = random.sample(products, min(num_items, len(products)))
        total = 0

        for prod in selected_products:
            qty = random.randint(1, 5)
            item_total = prod.price * qty
            item = OrderItem(
                order_id=order.id, product_id=prod.id,
                quantity=qty, unit_price=prod.price, total_price=item_total
            )
            db.add(item)
            total += item_total

        order.total_amount = round(total, 2)
        orders_data.append(order)

    db.flush()
    print(f"  ✅ {len(orders_data)} sipariş oluşturuldu")

    # ─── Kargo kayıtları ─────────────────────────────────────
    shipped_orders = [o for o in orders_data if o.status in
                      [OrderStatus.SHIPPED, OrderStatus.DELIVERED]]
    carriers = ["Yurtiçi Kargo", "Aras Kargo", "MNG Kargo", "PTT Kargo", "Sürat Kargo"]
    locations = ["İstanbul Dağıtım Merkezi", "Ankara Aktarma", "İzmir Şube",
                 "Antalya Dağıtım", "Bursa Merkez", "Teslimat Noktası"]

    for i, order in enumerate(shipped_orders):
        is_delayed = random.random() < 0.2  # %20 gecikme
        est_delivery = order.created_at + timedelta(days=random.randint(2, 5))

        cargo = CargoShipment(
            order_id=order.id,
            tracking_number=f"TR{900000000000 + i}",
            carrier=random.choice(carriers),
            status=CargoStatus.DELIVERED if order.status == OrderStatus.DELIVERED else
                   (CargoStatus.DELAYED if is_delayed else CargoStatus.IN_TRANSIT),
            estimated_delivery=est_delivery,
            actual_delivery=est_delivery + timedelta(days=1) if order.status == OrderStatus.DELIVERED else None,
            last_location=random.choice(locations),
            is_delayed=is_delayed,
            delay_reason="Hava koşulları nedeniyle gecikme" if is_delayed else None,
            created_at=order.created_at + timedelta(hours=4)
        )
        db.add(cargo)

    db.flush()
    print(f"  ✅ {len(shipped_orders)} kargo kaydı oluşturuldu")

    # ─── Stok uyarıları ──────────────────────────────────────
    low_stock_products = [p for p in products if p.stock_quantity <= p.min_stock_threshold]
    for p in low_stock_products:
        alert_type = AlertType.OUT_OF_STOCK if p.stock_quantity <= 0 else AlertType.LOW_STOCK
        alert = InventoryAlert(
            product_id=p.id,
            alert_type=alert_type,
            message=f"{p.name}: {'Stok tükendi!' if p.stock_quantity <= 0 else f'{p.stock_quantity} {p.unit} kaldı'}",
            suggested_action=f"Tedarikçiden en az {p.min_stock_threshold * 2} {p.unit} sipariş önerilir."
        )
        db.add(alert)

    print(f"  ✅ {len(low_stock_products)} stok uyarısı oluşturuldu")

    # ─── Görevler ────────────────────────────────────────────
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    demo_tasks = [
        Task(title="📦 Bekleyen siparişleri hazırla", description="Bugün gelen siparişlerin paketlenmesi",
             assigned_to="Ahmet Yılmaz", status=TaskStatus.IN_PROGRESS, priority=TaskPriority.HIGH,
             due_date=today.replace(hour=14), category="depo", is_auto_generated=True),
        Task(title="🚚 Kargo teslimatlarını kontrol et", description="Bugün teslim edilmesi gereken kargoları takip et",
             assigned_to="Fatma Demir", status=TaskStatus.TODO, priority=TaskPriority.HIGH,
             due_date=today.replace(hour=16), category="kargo", is_auto_generated=True),
        Task(title="📊 Günlük stok sayımı", description="Depo stok sayımı ve sistem güncelleme",
             assigned_to="Ahmet Yılmaz", status=TaskStatus.TODO, priority=TaskPriority.MEDIUM,
             due_date=today.replace(hour=10), category="depo", is_auto_generated=True),
        Task(title="📧 Tedarikçi siparişleri", description="Kritik stok seviyesindeki ürünler için tedarikçi ile iletişim",
             assigned_to="Mehmet Kaya", status=TaskStatus.TODO, priority=TaskPriority.URGENT,
             due_date=today.replace(hour=11), category="siparis", is_auto_generated=True),
        Task(title="🔍 Geciken kargo takibi", description="Geciken kargoları araştır ve müşterileri bilgilendir",
             assigned_to="Fatma Demir", status=TaskStatus.DONE, priority=TaskPriority.HIGH,
             due_date=today.replace(hour=12), category="kargo", is_auto_generated=True,
             completed_at=today.replace(hour=11, minute=45)),
    ]
    db.add_all(demo_tasks)
    print(f"  ✅ {len(demo_tasks)} görev oluşturuldu")

    # ─── Bildirimler ─────────────────────────────────────────
    notifications = [
        Notification(title="Yeni Sipariş", message="Ayşe Yıldız yeni sipariş oluşturdu (#SIP-2605-1000)",
                     type=AlertType.NEW_ORDER, link="/orders"),
        Notification(title="Stok Uyarısı", message="Domates (Sera) stoğu kritik seviyede: 8 kg kaldı",
                     type=AlertType.LOW_STOCK, link="/inventory"),
        Notification(title="Stok Tükendi", message="Biber Salçası stoğu tamamen tükendi!",
                     type=AlertType.OUT_OF_STOCK, link="/inventory"),
        Notification(title="Kargo Gecikmesi", message="TR900000000003 takip numaralı kargoda gecikme",
                     type=AlertType.CARGO_DELAY, link="/cargo"),
    ]
    db.add_all(notifications)
    print(f"  ✅ {len(notifications)} bildirim oluşturuldu")

    db.commit()
    db.close()
    print("\n🎉 Demo verileri başarıyla yüklendi!")


if __name__ == "__main__":
    seed()
