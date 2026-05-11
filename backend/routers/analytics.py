"""Analitik ve İçgörü API endpoint'leri."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from database import get_db
from models import Order, OrderItem, Product, OrderStatus

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/sales-summary")
def sales_summary(days: int = 30, db: Session = Depends(get_db)):
    """Satış özeti."""
    start_date = datetime.utcnow() - timedelta(days=days)

    total_revenue = db.query(func.sum(Order.total_amount)).filter(
        Order.created_at >= start_date,
        Order.status != OrderStatus.CANCELLED
    ).scalar() or 0

    total_orders = db.query(Order).filter(
        Order.created_at >= start_date,
        Order.status != OrderStatus.CANCELLED
    ).count()

    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0

    return {
        "period_days": days,
        "total_revenue": round(total_revenue, 2),
        "total_orders": total_orders,
        "avg_order_value": round(avg_order_value, 2)
    }


@router.get("/daily-revenue")
def daily_revenue(days: int = 14, db: Session = Depends(get_db)):
    """Günlük gelir verisi (grafik için)."""
    data = []
    for i in range(days - 1, -1, -1):
        day = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=i)
        next_day = day + timedelta(days=1)
        revenue = db.query(func.sum(Order.total_amount)).filter(
            Order.created_at >= day,
            Order.created_at < next_day,
            Order.status != OrderStatus.CANCELLED
        ).scalar() or 0
        count = db.query(Order).filter(
            Order.created_at >= day,
            Order.created_at < next_day,
            Order.status != OrderStatus.CANCELLED
        ).count()
        data.append({
            "date": day.strftime("%Y-%m-%d"),
            "label": day.strftime("%d %b"),
            "revenue": round(revenue, 2),
            "orders": count
        })
    return data


@router.get("/top-products")
def top_products(limit: int = 10, days: int = 30, db: Session = Depends(get_db)):
    """En çok satan ürünler."""
    start_date = datetime.utcnow() - timedelta(days=days)
    results = db.query(
        Product.id, Product.name, Product.category,
        func.sum(OrderItem.quantity).label("total_sold"),
        func.sum(OrderItem.total_price).label("total_revenue")
    ).join(OrderItem, Product.id == OrderItem.product_id
    ).join(Order, OrderItem.order_id == Order.id
    ).filter(
        Order.created_at >= start_date,
        Order.status != OrderStatus.CANCELLED
    ).group_by(Product.id).order_by(func.sum(OrderItem.quantity).desc()
    ).limit(limit).all()

    return [{
        "id": r[0], "name": r[1], "category": r[2],
        "total_sold": r[3], "total_revenue": round(r[4], 2)
    } for r in results]


@router.get("/category-breakdown")
def category_breakdown(db: Session = Depends(get_db)):
    """Kategori bazlı satış dağılımı."""
    results = db.query(
        Product.category,
        func.count(OrderItem.id).label("order_count"),
        func.sum(OrderItem.total_price).label("revenue")
    ).join(OrderItem, Product.id == OrderItem.product_id
    ).group_by(Product.category).all()

    return [{
        "category": r[0] or "Diğer",
        "order_count": r[1],
        "revenue": round(r[2], 2)
    } for r in results]


@router.get("/forecast")
def demand_forecast(db: Session = Depends(get_db)):
    """AI destekli basit talep tahmini (mock)."""
    # Son 30 günün en çok satanlarına basit artış trendi uygula
    top = top_products(limit=5, days=30, db=db)
    forecasts = []
    for p in top:
        weekly_avg = p["total_sold"] / 4.3  # ~4.3 hafta
        # Basit trend: %10 artış öngörüsü
        predicted = round(weekly_avg * 1.1, 1)
        forecasts.append({
            "product_id": p["id"],
            "product_name": p["name"],
            "avg_weekly_sales": round(weekly_avg, 1),
            "predicted_next_week": predicted,
            "confidence": "orta",
            "recommendation": f"Önümüzdeki hafta {p['name']} için ~{int(predicted)} "
                            f"adet satış bekleniyor. Stok kontrolü önerilir."
        })
    return forecasts


@router.get("/dashboard-summary")
def dashboard_summary(db: Session = Depends(get_db)):
    """Dashboard için genel özet."""
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    from models import CargoShipment, CargoStatus, InventoryAlert, Task, TaskStatus

    today_orders = db.query(Order).filter(Order.created_at >= today).count()
    today_revenue = db.query(func.sum(Order.total_amount)).filter(
        Order.created_at >= today, Order.status != OrderStatus.CANCELLED
    ).scalar() or 0
    pending_orders = db.query(Order).filter(
        Order.status.in_([OrderStatus.PENDING, OrderStatus.CONFIRMED])
    ).count()
    preparing_orders = db.query(Order).filter(Order.status == OrderStatus.PREPARING).count()

    low_stock = db.query(Product).filter(
        Product.is_active == True,
        Product.stock_quantity <= Product.min_stock_threshold,
        Product.stock_quantity > 0
    ).count()
    out_of_stock = db.query(Product).filter(
        Product.is_active == True, Product.stock_quantity <= 0
    ).count()

    delayed_cargo = db.query(CargoShipment).filter(CargoShipment.is_delayed == True).count()
    pending_cargo = db.query(CargoShipment).filter(
        CargoShipment.status == CargoStatus.PREPARING
    ).count()

    active_alerts = db.query(InventoryAlert).filter(InventoryAlert.is_resolved == False).count()
    tasks_todo = db.query(Task).filter(Task.status == TaskStatus.TODO).count()

    return {
        "today_orders": today_orders,
        "today_revenue": round(today_revenue, 2),
        "pending_orders": pending_orders,
        "preparing_orders": preparing_orders,
        "low_stock_count": low_stock,
        "out_of_stock_count": out_of_stock,
        "delayed_cargo": delayed_cargo,
        "pending_cargo": pending_cargo,
        "active_alerts": active_alerts,
        "tasks_todo": tasks_todo
    }
