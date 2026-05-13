"""AI Chatbot API endpoint'leri."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db
from models import Order, Product, CargoShipment, ChatMessage
from services.ai_agent import ai_agent
from services.inventory_service import inventory_service
import re
import uuid

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    session_id: str = None


@router.post("/")
def chat(data: ChatRequest, db: Session = Depends(get_db)):
    """AI chatbot ile konuşma."""
    session_id = data.session_id or str(uuid.uuid4())[:8]

    # Kullanıcı mesajını kaydet
    user_msg = ChatMessage(
        session_id=session_id, role="user", content=data.message
    )
    db.add(user_msg)

    # Intent tespit et
    intent, params = ai_agent.detect_intent(data.message)

    # Bağlam verisini topla
    db_context = {}

    if intent == "order_query":
        order_num = params.get("order_number") or params.get("number")
        if order_num:
            # Tam eşleşme veya kısmi arama
            order = db.query(Order).filter(
                Order.order_number.ilike(f"%{order_num}%")
            ).first()
            if order:
                db_context["order"] = order.to_dict()

    elif intent == "stock_check":
        products = db.query(Product).filter(Product.is_active == True).all()
        db_context["products"] = [p.to_dict() for p in products]

    elif intent == "cargo_track":
        order_num = params.get("order_number") or params.get("number")
        if order_num:
            order = db.query(Order).filter(
                Order.order_number.ilike(f"%{order_num}%")
            ).first()
            if order and order.cargo:
                db_context["cargo"] = order.cargo.to_dict()
        else:
            # Son kargo bilgisi
            cargo = db.query(CargoShipment).order_by(
                CargoShipment.created_at.desc()
            ).first()
            if cargo:
                db_context["cargo"] = cargo.to_dict()

    elif intent == "product_info":
        # Ürün adı ile arama
        msg_lower = data.message.lower()
        products = db.query(Product).filter(Product.is_active == True).all()
        for p in products:
            if p.name.lower() in msg_lower:
                db_context["product"] = p.to_dict()
                break

    elif intent == "daily_summary":
        from routers.analytics import dashboard_summary
        db_context["summary"] = dashboard_summary(db=db)

    elif intent == "inventory_alert":
        alerts = inventory_service.get_active_alerts(db)
        db_context["alerts"] = alerts

    # AI yanıtı üret
    response = ai_agent.generate_response(data.message, db_context)

    # Asistan yanıtını kaydet
    assistant_msg = ChatMessage(
        session_id=session_id, role="assistant",
        content=response["response"], intent=intent
    )
    db.add(assistant_msg)
    db.commit()

    return {
        "session_id": session_id,
        "response": response["response"],
        "intent": response["intent"],
        "actions": response["actions"]
    }


@router.get("/history/{session_id}")
def chat_history(session_id: str, db: Session = Depends(get_db)):
    """Sohbet geçmişi."""
    messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.created_at.asc()).all()
    return [m.to_dict() for m in messages]


# ── EK: smart endpoint ──
@router.post("/smart")
def chat_smart(data: ChatRequest, db: Session = Depends(get_db)):
    session_id = data.session_id or str(uuid.uuid4())[:8]

    db.add(ChatMessage(
        session_id=session_id, role="user", content=data.message
    ))

    result = ai_agent.smart_response(data.message, db)

    db.add(ChatMessage(
        session_id=session_id, role="assistant",
        content=result["response"], intent=result["intent"]
    ))
    db.commit()

    return {
        "session_id": session_id,
        "response": result["response"],
        "intent": result["intent"],
        "actions": result["actions"],
    }
