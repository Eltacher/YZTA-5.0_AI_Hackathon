"""
Kargo Takip Servisi.
Kargo durumu izleme, gecikme tespiti ve otomatik bildirim.
"""

from sqlalchemy.orm import Session
from datetime import datetime
from models import CargoShipment, CargoStatus, Notification, AlertType


class CargoService:
    """Kargo yönetimi iş mantığı."""

    def check_delays(self, db: Session) -> list:
        """Geciken kargoları tespit et ve uyarı oluştur."""
        now = datetime.utcnow()
        delayed = db.query(CargoShipment).filter(
            CargoShipment.estimated_delivery < now,
            CargoShipment.status.notin_([CargoStatus.DELIVERED, CargoStatus.RETURNED]),
            CargoShipment.is_delayed == False
        ).all()

        alerts = []
        for s in delayed:
            s.is_delayed = True
            s.status = CargoStatus.DELAYED
            s.delay_reason = "Tahmini teslim tarihi aşıldı"
            notif = Notification(
                title=f"Kargo Gecikmesi: {s.tracking_number}",
                message=f"Sipariş #{s.order.order_number} kargosunda gecikme.",
                type=AlertType.CARGO_DELAY,
                link=f"/cargo?tracking={s.tracking_number}"
            )
            db.add(notif)
            alerts.append(s.to_dict())

        if delayed:
            db.commit()
        return alerts

    def update_status(self, db: Session, shipment_id: int, new_status: str, location: str = None) -> dict:
        """Kargo durumunu güncelle."""
        shipment = db.query(CargoShipment).filter(CargoShipment.id == shipment_id).first()
        if not shipment:
            return None
        try:
            shipment.status = CargoStatus(new_status)
        except ValueError:
            return None
        if location:
            shipment.last_location = location
        if new_status == "delivered":
            shipment.actual_delivery = datetime.utcnow()
            shipment.is_delayed = False
            if shipment.order:
                from models import OrderStatus
                shipment.order.status = OrderStatus.DELIVERED
        shipment.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(shipment)
        return shipment.to_dict()

    def get_summary(self, db: Session) -> dict:
        """Kargo özet raporu."""
        total = db.query(CargoShipment).count()
        preparing = db.query(CargoShipment).filter(CargoShipment.status == CargoStatus.PREPARING).count()
        in_transit = db.query(CargoShipment).filter(
            CargoShipment.status.in_([CargoStatus.IN_TRANSIT, CargoStatus.OUT_FOR_DELIVERY, CargoStatus.PICKED_UP])
        ).count()
        delivered = db.query(CargoShipment).filter(CargoShipment.status == CargoStatus.DELIVERED).count()
        delayed_count = db.query(CargoShipment).filter(CargoShipment.is_delayed == True).count()
        return {
            "total": total, "preparing": preparing, "in_transit": in_transit,
            "delivered": delivered, "delayed": delayed_count,
            "on_time_rate": round((total - delayed_count) / total * 100, 1) if total > 0 else 100
        }

    def get_delayed_shipments(self, db: Session) -> list:
        """Geciken kargoları listele."""
        shipments = db.query(CargoShipment).filter(
            CargoShipment.is_delayed == True
        ).order_by(CargoShipment.estimated_delivery.asc()).all()
        return [s.to_dict() for s in shipments]


cargo_service = CargoService()
