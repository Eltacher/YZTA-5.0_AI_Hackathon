"""Sipariş yönetimi API endpoint'leri."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from database import get_db
from models import Order, OrderItem, OrderStatus, Product, Customer, Notification, AlertType
import random
import string

router = APIRouter(prefix="/api/orders", tags=["orders"])


class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int


class OrderCreate(BaseModel):
    customer_id: int
    items: List[OrderItemCreate]
    shipping_address: Optional[str] = None
    notes: Optional[str] = None


class OrderStatusUpdate(BaseModel):
    status: str


def generate_order_number() -> str:
    """Benzersiz sipariş numarası üret."""
    prefix = datetime.now().strftime("%y%m")
    suffix = ''.join(random.choices(string.digits, k=4))
    return f"SIP-{prefix}-{suffix}"


@router.get("/")
def list_orders(
    status: Optional[str] = None,
    customer_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Siparişleri listele."""
    query = db.query(Order)
    if status:
        try:
            query = query.filter(Order.status == OrderStatus(status))
        except ValueError:
            pass
    if customer_id:
        query = query.filter(Order.customer_id == customer_id)
    total = query.count()
    orders = query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()
    return {"total": total, "orders": [o.to_dict() for o in orders]}


@router.get("/stats")
def order_stats(db: Session = Depends(get_db)):
    """Sipariş istatistikleri."""
    total = db.query(Order).count()
    pending = db.query(Order).filter(Order.status == OrderStatus.PENDING).count()
    confirmed = db.query(Order).filter(Order.status == OrderStatus.CONFIRMED).count()
    preparing = db.query(Order).filter(Order.status == OrderStatus.PREPARING).count()
    shipped = db.query(Order).filter(Order.status == OrderStatus.SHIPPED).count()
    delivered = db.query(Order).filter(Order.status == OrderStatus.DELIVERED).count()
    cancelled = db.query(Order).filter(Order.status == OrderStatus.CANCELLED).count()

    from sqlalchemy import func
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_count = db.query(Order).filter(Order.created_at >= today).count()
    today_revenue = db.query(func.sum(Order.total_amount)).filter(
        Order.created_at >= today
    ).scalar() or 0

    return {
        "total": total, "pending": pending, "confirmed": confirmed,
        "preparing": preparing, "shipped": shipped, "delivered": delivered,
        "cancelled": cancelled, "today_count": today_count,
        "today_revenue": round(today_revenue, 2)
    }


@router.get("/{order_id}")
def get_order(order_id: int, db: Session = Depends(get_db)):
    """Sipariş detayı."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Sipariş bulunamadı")
    return order.to_dict()


@router.get("/number/{order_number}")
def get_order_by_number(order_number: str, db: Session = Depends(get_db)):
    """Sipariş numarasıyla sorgula."""
    order = db.query(Order).filter(Order.order_number == order_number).first()
    if not order:
        raise HTTPException(status_code=404, detail="Sipariş bulunamadı")
    return order.to_dict()


@router.post("/")
def create_order(data: OrderCreate, db: Session = Depends(get_db)):
    """Yeni sipariş oluştur."""
    customer = db.query(Customer).filter(Customer.id == data.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Müşteri bulunamadı")

    order = Order(
        order_number=generate_order_number(),
        customer_id=data.customer_id,
        shipping_address=data.shipping_address or customer.address,
        notes=data.notes
    )
    db.add(order)
    db.flush()

    total = 0
    for item_data in data.items:
        product = db.query(Product).filter(Product.id == item_data.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Ürün #{item_data.product_id} bulunamadı")
        if product.stock_quantity < item_data.quantity:
            raise HTTPException(status_code=400,
                                detail=f"{product.name} stokta yeterli değil ({product.stock_quantity} mevcut)")

        item_total = product.price * item_data.quantity
        item = OrderItem(
            order_id=order.id, product_id=product.id,
            quantity=item_data.quantity, unit_price=product.price,
            total_price=item_total
        )
        db.add(item)
        product.stock_quantity -= item_data.quantity
        total += item_total

    order.total_amount = total

    notif = Notification(
        title=f"Yeni Sipariş: #{order.order_number}",
        message=f"{customer.name} - {total:.2f} ₺",
        type=AlertType.NEW_ORDER, link=f"/orders?id={order.id}"
    )
    db.add(notif)
    db.commit()
    db.refresh(order)
    return order.to_dict()


@router.patch("/{order_id}/status")
def update_order_status(order_id: int, data: OrderStatusUpdate, db: Session = Depends(get_db)):
    """Sipariş durumunu güncelle."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Sipariş bulunamadı")
    try:
        order.status = OrderStatus(data.status)
    except ValueError:
        raise HTTPException(status_code=400, detail="Geçersiz durum")
    order.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(order)
    return order.to_dict()
