"""
Bildirim Servisi.
Sistem genelinde bildirim yönetimi.
"""

from sqlalchemy.orm import Session
from models import Notification, AlertType


class NotificationService:
    """Bildirim yönetimi."""

    def get_unread(self, db: Session, limit: int = 20) -> list:
        """Okunmamış bildirimleri getir."""
        notifs = db.query(Notification).filter(
            Notification.is_read == False
        ).order_by(Notification.created_at.desc()).limit(limit).all()
        return [n.to_dict() for n in notifs]

    def get_all(self, db: Session, limit: int = 50) -> list:
        """Tüm bildirimleri getir."""
        notifs = db.query(Notification).order_by(
            Notification.created_at.desc()
        ).limit(limit).all()
        return [n.to_dict() for n in notifs]

    def mark_as_read(self, db: Session, notification_id: int) -> dict:
        """Bildirimi okundu olarak işaretle."""
        notif = db.query(Notification).filter(Notification.id == notification_id).first()
        if notif:
            notif.is_read = True
            db.commit()
            db.refresh(notif)
            return notif.to_dict()
        return None

    def mark_all_read(self, db: Session) -> int:
        """Tüm bildirimleri okundu yap."""
        count = db.query(Notification).filter(
            Notification.is_read == False
        ).update({"is_read": True})
        db.commit()
        return count

    def create(self, db: Session, title: str, message: str,
               alert_type: AlertType = None, link: str = None) -> dict:
        """Yeni bildirim oluştur."""
        notif = Notification(
            title=title, message=message, type=alert_type, link=link
        )
        db.add(notif)
        db.commit()
        db.refresh(notif)
        return notif.to_dict()

    def get_unread_count(self, db: Session) -> int:
        """Okunmamış bildirim sayısı."""
        return db.query(Notification).filter(Notification.is_read == False).count()


notification_service = NotificationService()
