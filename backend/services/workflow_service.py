"""
İş Akışı ve Görev Yönetimi Servisi.
Otomatik görev oluşturma, ekip atama, günlük iş planı.
"""

from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from models import Task, TaskStatus, TaskPriority, Order, OrderStatus, Notification, AlertType


class WorkflowService:
    """İş akışı motoru."""

    # Ekip üyeleri (demo)
    TEAM_MEMBERS = {
        "depo": "Ahmet Yılmaz",
        "kargo": "Fatma Demir",
        "siparis": "Mehmet Kaya",
        "genel": "Ayşe Çelik"
    }

    def generate_daily_tasks(self, db: Session) -> list:
        """
        Sabah 08:00 otomatik görev oluşturma simülasyonu.
        Bugünkü siparişleri analiz edip görevleri dağıt.
        """
        today = datetime.utcnow().date()
        tasks_created = []

        # Bekleyen siparişler için hazırlama görevi
        pending_orders = db.query(Order).filter(
            Order.status.in_([OrderStatus.CONFIRMED, OrderStatus.PENDING])
        ).all()

        if pending_orders:
            task = Task(
                title=f"📦 {len(pending_orders)} sipariş hazırlanacak",
                description=f"Bugün hazırlanması gereken siparişler: " +
                           ", ".join([f"#{o.order_number}" for o in pending_orders[:10]]),
                assigned_to=self.TEAM_MEMBERS["depo"],
                status=TaskStatus.TODO,
                priority=TaskPriority.HIGH,
                due_date=datetime.combine(today, datetime.min.time().replace(hour=17)),
                category="depo",
                is_auto_generated=True
            )
            db.add(task)
            tasks_created.append(task)

        # Kargoya verilecek siparişler
        preparing_orders = db.query(Order).filter(
            Order.status == OrderStatus.PREPARING
        ).all()

        if preparing_orders:
            task = Task(
                title=f"🚚 {len(preparing_orders)} paket kargoya verilecek",
                description=f"Kargoya verilmeyi bekleyen paketler: " +
                           ", ".join([f"#{o.order_number}" for o in preparing_orders[:10]]),
                assigned_to=self.TEAM_MEMBERS["kargo"],
                status=TaskStatus.TODO,
                priority=TaskPriority.HIGH,
                due_date=datetime.combine(today, datetime.min.time().replace(hour=14)),
                category="kargo",
                is_auto_generated=True
            )
            db.add(task)
            tasks_created.append(task)

        # Günlük stok kontrolü
        task = Task(
            title="📊 Günlük stok kontrolü",
            description="Tüm ürünlerin stok seviyelerini kontrol et, kritik olanları raporla.",
            assigned_to=self.TEAM_MEMBERS["depo"],
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
            due_date=datetime.combine(today, datetime.min.time().replace(hour=10)),
            category="depo",
            is_auto_generated=True
        )
        db.add(task)
        tasks_created.append(task)

        db.commit()
        return [t.to_dict() for t in tasks_created]

    def get_tasks_by_assignee(self, db: Session, assignee: str = None) -> dict:
        """Kişiye göre görevleri grupla."""
        query = db.query(Task)
        if assignee:
            query = query.filter(Task.assigned_to == assignee)

        tasks = query.order_by(Task.priority.desc(), Task.due_date.asc()).all()
        grouped = {}
        for task in tasks:
            key = task.assigned_to or "Atanmamış"
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(task.to_dict())
        return grouped

    def get_today_tasks(self, db: Session) -> list:
        """Bugünkü görevleri getir."""
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        tasks = db.query(Task).filter(
            Task.due_date >= today_start,
            Task.due_date < today_end
        ).order_by(Task.priority.desc()).all()
        return [t.to_dict() for t in tasks]


workflow_service = WorkflowService()
