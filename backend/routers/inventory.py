"""Stok/Envanter yönetimi API endpoint'leri."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from services.inventory_service import inventory_service

router = APIRouter(prefix="/api/inventory", tags=["inventory"])


@router.get("/check")
def check_stock_levels(db: Session = Depends(get_db)):
    """Stok seviyelerini kontrol et, kritik ürünler için uyarı oluştur."""
    alerts = inventory_service.check_stock_levels(db)
    return {"checked": True, "new_alerts": len(alerts), "alerts": alerts}


@router.get("/alerts")
def get_alerts(db: Session = Depends(get_db)):
    """Aktif stok uyarılarını getir."""
    return inventory_service.get_active_alerts(db)


@router.patch("/alerts/{alert_id}/resolve")
def resolve_alert(alert_id: int, db: Session = Depends(get_db)):
    """Uyarıyı çözüldü olarak işaretle."""
    result = inventory_service.resolve_alert(db, alert_id)
    if not result:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Uyarı bulunamadı")
    return result


@router.get("/reorder/{product_id}")
def get_reorder_suggestion(product_id: int, db: Session = Depends(get_db)):
    """AI destekli yenileme önerisi al."""
    result = inventory_service.get_reorder_suggestion(db, product_id)
    if not result:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Ürün bulunamadı")
    return result


@router.get("/supplier-draft/{product_id}")
def get_supplier_draft(product_id: int, db: Session = Depends(get_db)):
    """Tedarikçiye sipariş taslak maili oluştur."""
    result = inventory_service.generate_supplier_draft(db, product_id)
    if not result:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Ürün bulunamadı")
    return result
