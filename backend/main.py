"""
YZTA E-Ticaret Platformu — FastAPI Ana Uygulama.
KOBİ'ler için AI destekli e-ticaret yönetim sistemi.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import json

from database import engine, Base, SessionLocal
from routers import products, orders, customers, cargo, inventory, tasks, analytics, ai_chat
from services.notification_service import notification_service

# ─── Veritabanı tablolarını oluştur ──────────────────────────
from models import *  # noqa - modelleri import et ki tablolar oluşsun
Base.metadata.create_all(bind=engine)

# ─── FastAPI Uygulaması ──────────────────────────────────────
app = FastAPI(
    title="YZTA E-Ticaret Platformu",
    description="KOBİ'ler ve kooperatifler için AI destekli e-ticaret yönetim sistemi",
    version="1.0.0"
)

# ─── CORS ayarları ───────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Router'ları kaydet ──────────────────────────────────────
app.include_router(products.router)
app.include_router(orders.router)
app.include_router(customers.router)
app.include_router(cargo.router)
app.include_router(inventory.router)
app.include_router(tasks.router)
app.include_router(analytics.router)
app.include_router(ai_chat.router)


# ─── Bildirim API ────────────────────────────────────────────
@app.get("/api/notifications")
def get_notifications(unread_only: bool = False):
    db = SessionLocal()
    try:
        if unread_only:
            return notification_service.get_unread(db)
        return notification_service.get_all(db)
    finally:
        db.close()


@app.get("/api/notifications/count")
def notification_count():
    db = SessionLocal()
    try:
        return {"count": notification_service.get_unread_count(db)}
    finally:
        db.close()


@app.patch("/api/notifications/{notif_id}/read")
def mark_notification_read(notif_id: int):
    db = SessionLocal()
    try:
        return notification_service.mark_as_read(db, notif_id)
    finally:
        db.close()


@app.post("/api/notifications/read-all")
def mark_all_notifications_read():
    db = SessionLocal()
    try:
        count = notification_service.mark_all_read(db)
        return {"marked": count}
    finally:
        db.close()


# ─── WebSocket — Gerçek zamanlı bildirimler ──────────────────
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for conn in self.active_connections:
            try:
                await conn.send_json(message)
            except Exception:
                pass


manager = ConnectionManager()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Client'tan gelen mesajları işle (ileride genişletilebilir)
            await websocket.send_json({"type": "ack", "message": "Bağlantı aktif"})
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ─── Sağlık kontrolü ─────────────────────────────────────────
@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "YZTA E-Ticaret Platformu",
        "version": "1.0.0"
    }


# ─── Statik dosyalar (Frontend) ─────────────────────────────
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
