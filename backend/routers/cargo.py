"""Kargo yönetimi API endpoint'leri."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
from database import get_db
from models import CargoShipment, CargoStatus, Order
from services.cargo_service import cargo_service
import random
import string

router = APIRouter(prefix="/api/cargo", tags=["cargo"])


class CargoCreate(BaseModel):
    order_id: int
    carrier: str = "Yurtiçi Kargo"
    estimated_days: int = 3


class CargoStatusUpdate(BaseModel):
    status: str
    location: Optional[str] = None


def generate_tracking_number() -> str:
    return "TR" + ''.join(random.choices(string.digits, k=12))


@router.get("/")
def list_shipments(
    status: Optional[str] = None,
    delayed_only: bool = False,
    skip: int = 0, limit: int = 50,
    db: Session = Depends(get_db)
):
    query = db.query(CargoShipment)
    if status:
        try:
            query = query.filter(CargoShipment.status == CargoStatus(status))
        except ValueError:
            pass
    if delayed_only:
        query = query.filter(CargoShipment.is_delayed == True)
    total = query.count()
    shipments = query.order_by(CargoShipment.created_at.desc()).offset(skip).limit(limit).all()
    return {"total": total, "shipments": [s.to_dict() for s in shipments]}


@router.get("/summary")
def cargo_summary(db: Session = Depends(get_db)):
    return cargo_service.get_summary(db)


@router.get("/delayed")
def delayed_shipments(db: Session = Depends(get_db)):
    return cargo_service.get_delayed_shipments(db)


@router.get("/check-delays")
def check_delays(db: Session = Depends(get_db)):
    """Gecikmeleri kontrol et ve uyarı oluştur."""
    alerts = cargo_service.check_delays(db)
    return {"checked": True, "new_delays": len(alerts), "alerts": alerts}


@router.get("/{shipment_id}")
def get_shipment(shipment_id: int, db: Session = Depends(get_db)):
    shipment = db.query(CargoShipment).filter(CargoShipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Kargo bulunamadı")
    return shipment.to_dict()


@router.get("/track/{tracking_number}")
def track_shipment(tracking_number: str, db: Session = Depends(get_db)):
    shipment = db.query(CargoShipment).filter(
        CargoShipment.tracking_number == tracking_number
    ).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Kargo bulunamadı")
    return shipment.to_dict()


@router.post("/")
def create_shipment(data: CargoCreate, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == data.order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Sipariş bulunamadı")
    existing = db.query(CargoShipment).filter(CargoShipment.order_id == data.order_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Bu siparişe zaten kargo oluşturulmuş")

    shipment = CargoShipment(
        order_id=data.order_id,
        tracking_number=generate_tracking_number(),
        carrier=data.carrier,
        estimated_delivery=datetime.utcnow() + timedelta(days=data.estimated_days)
    )
    db.add(shipment)
    from models import OrderStatus
    order.status = OrderStatus.SHIPPED
    db.commit()
    db.refresh(shipment)
    return shipment.to_dict()


@router.patch("/{shipment_id}/status")
def update_shipment_status(shipment_id: int, data: CargoStatusUpdate,
                           db: Session = Depends(get_db)):
    result = cargo_service.update_status(db, shipment_id, data.status, data.location)
    if not result:
        raise HTTPException(status_code=404, detail="Kargo bulunamadı veya geçersiz durum")
    return result
