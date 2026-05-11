"""
Veritabanı modelleri.
Tüm e-ticaret varlıkları: Ürün, Sipariş, Müşteri, Kargo, Stok, Görev, Chat.
"""

from sqlalchemy import (
    Column, Integer, String, Float, Text, DateTime, Boolean,
    ForeignKey, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from database import Base


# ─── Enum Tanımları ───────────────────────────────────────────

class OrderStatus(str, enum.Enum):
    PENDING = "pending"           # Beklemede
    CONFIRMED = "confirmed"       # Onaylandı
    PREPARING = "preparing"       # Hazırlanıyor
    SHIPPED = "shipped"           # Kargoya verildi
    DELIVERED = "delivered"       # Teslim edildi
    CANCELLED = "cancelled"       # İptal edildi


class CargoStatus(str, enum.Enum):
    PREPARING = "preparing"       # Hazırlanıyor
    PICKED_UP = "picked_up"       # Kurye aldı
    IN_TRANSIT = "in_transit"     # Yolda
    OUT_FOR_DELIVERY = "out_for_delivery"  # Dağıtımda
    DELIVERED = "delivered"       # Teslim edildi
    DELAYED = "delayed"           # Gecikmiş
    RETURNED = "returned"         # İade edildi


class TaskStatus(str, enum.Enum):
    TODO = "todo"                 # Yapılacak
    IN_PROGRESS = "in_progress"   # Devam ediyor
    DONE = "done"                 # Tamamlandı


class TaskPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class AlertType(str, enum.Enum):
    LOW_STOCK = "low_stock"           # Düşük stok
    OUT_OF_STOCK = "out_of_stock"     # Stok tükendi
    CARGO_DELAY = "cargo_delay"       # Kargo gecikmesi
    NEW_ORDER = "new_order"           # Yeni sipariş
    TASK_DUE = "task_due"             # Görev süresi doldu
    REORDER_SUGGESTION = "reorder"    # Yeniden sipariş önerisi


# ─── Modeller ─────────────────────────────────────────────────

class Customer(Base):
    """Müşteri modeli."""
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True)
    phone = Column(String(20))
    address = Column(Text)
    city = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)

    # İlişkiler
    orders = relationship("Order", back_populates="customer")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "address": self.address,
            "city": self.city,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class Product(Base):
    """Ürün modeli."""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    price = Column(Float, nullable=False)
    stock_quantity = Column(Integer, default=0)
    unit = Column(String(20), default="adet")       # adet, kg, litre vb.
    category = Column(String(100))
    sku = Column(String(50), unique=True, index=True)  # Stok kodu
    min_stock_threshold = Column(Integer, default=10)   # Kritik stok eşiği
    image_url = Column(String(500))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # İlişkiler
    order_items = relationship("OrderItem", back_populates="product")
    inventory_alerts = relationship("InventoryAlert", back_populates="product")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price": self.price,
            "stock_quantity": self.stock_quantity,
            "unit": self.unit,
            "category": self.category,
            "sku": self.sku,
            "min_stock_threshold": self.min_stock_threshold,
            "image_url": self.image_url,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_low_stock": self.stock_quantity <= self.min_stock_threshold
        }


class Order(Base):
    """Sipariş modeli."""
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(20), unique=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.PENDING)
    total_amount = Column(Float, default=0.0)
    shipping_address = Column(Text)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # İlişkiler
    customer = relationship("Customer", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    cargo = relationship("CargoShipment", back_populates="order", uselist=False)

    def to_dict(self):
        return {
            "id": self.id,
            "order_number": self.order_number,
            "customer_id": self.customer_id,
            "customer_name": self.customer.name if self.customer else None,
            "status": self.status.value if self.status else None,
            "total_amount": self.total_amount,
            "shipping_address": self.shipping_address,
            "notes": self.notes,
            "items": [item.to_dict() for item in self.items] if self.items else [],
            "cargo": self.cargo.to_dict() if self.cargo else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class OrderItem(Base):
    """Sipariş kalemi modeli."""
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)

    # İlişkiler
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")

    def to_dict(self):
        return {
            "id": self.id,
            "order_id": self.order_id,
            "product_id": self.product_id,
            "product_name": self.product.name if self.product else None,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "total_price": self.total_price
        }


class CargoShipment(Base):
    """Kargo gönderi modeli."""
    __tablename__ = "cargo_shipments"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    tracking_number = Column(String(50), unique=True, index=True)
    carrier = Column(String(100))                    # Kargo firması
    status = Column(SQLEnum(CargoStatus), default=CargoStatus.PREPARING)
    estimated_delivery = Column(DateTime)
    actual_delivery = Column(DateTime)
    last_location = Column(String(200))
    is_delayed = Column(Boolean, default=False)
    delay_reason = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # İlişkiler
    order = relationship("Order", back_populates="cargo")

    def to_dict(self):
        return {
            "id": self.id,
            "order_id": self.order_id,
            "order_number": self.order.order_number if self.order else None,
            "tracking_number": self.tracking_number,
            "carrier": self.carrier,
            "status": self.status.value if self.status else None,
            "estimated_delivery": self.estimated_delivery.isoformat() if self.estimated_delivery else None,
            "actual_delivery": self.actual_delivery.isoformat() if self.actual_delivery else None,
            "last_location": self.last_location,
            "is_delayed": self.is_delayed,
            "delay_reason": self.delay_reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class InventoryAlert(Base):
    """Stok uyarı modeli."""
    __tablename__ = "inventory_alerts"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    alert_type = Column(SQLEnum(AlertType), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    is_resolved = Column(Boolean, default=False)
    suggested_action = Column(Text)      # AI önerisi
    created_at = Column(DateTime, default=datetime.utcnow)

    # İlişkiler
    product = relationship("Product", back_populates="inventory_alerts")

    def to_dict(self):
        return {
            "id": self.id,
            "product_id": self.product_id,
            "product_name": self.product.name if self.product else None,
            "alert_type": self.alert_type.value if self.alert_type else None,
            "message": self.message,
            "is_read": self.is_read,
            "is_resolved": self.is_resolved,
            "suggested_action": self.suggested_action,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class Task(Base):
    """Görev modeli."""
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    assigned_to = Column(String(100))        # Atanan kişi
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.TODO)
    priority = Column(SQLEnum(TaskPriority), default=TaskPriority.MEDIUM)
    due_date = Column(DateTime)
    category = Column(String(50))            # sipariş, depo, kargo, genel
    related_order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    is_auto_generated = Column(Boolean, default=False)  # AI tarafından mı oluşturuldu
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "assigned_to": self.assigned_to,
            "status": self.status.value if self.status else None,
            "priority": self.priority.value if self.priority else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "category": self.category,
            "related_order_id": self.related_order_id,
            "is_auto_generated": self.is_auto_generated,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }


class ChatMessage(Base):
    """AI sohbet mesajı modeli."""
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(50), index=True)
    role = Column(String(20), nullable=False)   # user, assistant
    content = Column(Text, nullable=False)
    intent = Column(String(50))                  # order_query, stock_check, cargo_track vb.
    metadata_json = Column(Text)                 # Ek veri (JSON string)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "role": self.role,
            "content": self.content,
            "intent": self.intent,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class Notification(Base):
    """Bildirim modeli."""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(SQLEnum(AlertType))
    is_read = Column(Boolean, default=False)
    link = Column(String(200))               # İlgili sayfaya yönlendirme
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "message": self.message,
            "type": self.type.value if self.type else None,
            "is_read": self.is_read,
            "link": self.link,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
