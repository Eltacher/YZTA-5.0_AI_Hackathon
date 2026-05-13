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

    # ── EK: AI ile proaktif gecikme zenginlestirme ──
    def enrich_delay_reasons_with_ai(self, db: Session) -> dict:
        from services.ai_agent import ai_agent
        now = datetime.utcnow()
        cargos = db.query(CargoShipment).filter(
            (CargoShipment.is_delayed == True)
            | (CargoShipment.status == CargoStatus.DELAYED)
            | (
                (CargoShipment.estimated_delivery < now)
                & CargoShipment.status.notin_([CargoStatus.DELIVERED, CargoStatus.RETURNED])
            )
        ).all()

        enriched = 0
        notifs_added = 0
        notifs_updated = 0
        generic = {"Tahmini teslim tarihi aşıldı", "", None}

        for c in cargos:
            if c.delay_reason in generic and ai_agent.is_gemini_active:
                try:
                    prompt = (
                        f"Bir KOBI e-ticaret kargo gecikmesi icin kisa (2 cumle), "
                        f"profesyonel sebep + operator aksiyon onerisi yaz. Turkce.\n"
                        f"Takip: {c.tracking_number} | Firma: {c.carrier} | "
                        f"Son konum: {c.last_location or 'Bilinmiyor'} | "
                        f"Tahmini teslim: {c.estimated_delivery} | Su an: {now}"
                    )
                    resp = ai_agent._gemini_model.generate_content(prompt)
                    c.delay_reason = resp.text.strip()[:500]
                    enriched += 1
                except Exception:
                    pass

            existing = db.query(Notification).filter(
                Notification.link.like(f"%{c.tracking_number}%")
            ).first()
            order_num = c.order.order_number if c.order else "?"
            msg = c.delay_reason or "Gecikme tespit edildi"
            full_msg = f"Sipariş #{order_num} — {msg}"

            if existing:
                if "kargosunda gecikme." in (existing.message or "") or len(existing.message or "") < 200:
                    existing.title = f"🚨 Kargo Gecikmesi: {c.tracking_number}"
                    existing.message = full_msg
                    existing.is_read = False
                    notifs_updated += 1
            else:
                notif = Notification(
                    title=f"🚨 Kargo Gecikmesi: {c.tracking_number}",
                    message=full_msg,
                    type=AlertType.CARGO_DELAY,
                    link=f"/cargo?tracking={c.tracking_number}",
                )
                db.add(notif)
                notifs_added += 1

        if enriched or notifs_added or notifs_updated:
            db.commit()

        return {
            "delayed_cargo_count": len(cargos),
            "enriched_with_ai": enriched,
            "notifications_added": notifs_added,
            "notifications_updated": notifs_updated,
        }

    def generate_customer_apology(self, db: Session, cargo_id: int) -> dict:
        from services.ai_agent import ai_agent
        cargo = db.query(CargoShipment).filter(CargoShipment.id == cargo_id).first()
        if not cargo:
            return {"error": "Kargo bulunamadı"}
        if not ai_agent.is_gemini_active:
            return {"error": "Gemini aktif değil"}

        order = cargo.order
        customer_name = order.customer.name if order and order.customer else "Değerli Müşterimiz"
        order_num = order.order_number if order else "?"

        prompt = (
            f"KOBI e-ticaret isletmesi adina kargosu geciken musteriye profesyonel, "
            f"samimi ozur mesaji yaz. Turkce, en fazla 4 cumle. Siparis no ve takibi "
            f"belirt; kucuk bir jest sun.\n\n"
            f"Musteri: {customer_name}\n"
            f"Siparis: #{order_num}\n"
            f"Takip: {cargo.tracking_number}\n"
            f"Kargo: {cargo.carrier}\n"
            f"Sebep: {cargo.delay_reason or 'Belirtilmemis'}"
        )
        try:
            resp = ai_agent._gemini_model.generate_content(prompt)
            return {
                "cargo_id": cargo_id,
                "tracking_number": cargo.tracking_number,
                "customer_name": customer_name,
                "apology_message": resp.text.strip(),
            }
        except Exception as e:
            return {"error": str(e)}

    def run_full_ai_check(self, db: Session) -> dict:
        std = self.check_delays(db)
        enrich_result = self.enrich_delay_reasons_with_ai(db)
        apologies = []
        delayed = self.get_delayed_shipments(db)
        for c in delayed[:5]:
            res = self.generate_customer_apology(db, c["id"])
            if "apology_message" in res:
                apologies.append(res)
        return {
            "standard_check": {"new_delays": len(std)},
            "ai_enrichment": enrich_result,
            "customer_apologies": apologies,
        }


cargo_service = CargoService()
