"""Ürün yönetimi API endpoint'leri."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from database import get_db
from models import Product

router = APIRouter(prefix="/api/products", tags=["products"])


class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    stock_quantity: int = 0
    unit: str = "adet"
    category: Optional[str] = None
    sku: str
    min_stock_threshold: int = 10
    image_url: Optional[str] = None


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    stock_quantity: Optional[int] = None
    unit: Optional[str] = None
    category: Optional[str] = None
    min_stock_threshold: Optional[int] = None
    image_url: Optional[str] = None
    is_active: Optional[bool] = None


@router.get("/")
def list_products(
    category: Optional[str] = None,
    search: Optional[str] = None,
    low_stock: bool = False,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Ürünleri listele, filtreleme destekli."""
    query = db.query(Product).filter(Product.is_active == True)
    if category:
        query = query.filter(Product.category == category)
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))
    if low_stock:
        query = query.filter(Product.stock_quantity <= Product.min_stock_threshold)
    total = query.count()
    products = query.offset(skip).limit(limit).all()
    return {"total": total, "products": [p.to_dict() for p in products]}


@router.get("/categories")
def list_categories(db: Session = Depends(get_db)):
    """Ürün kategorilerini listele."""
    cats = db.query(Product.category).distinct().filter(Product.category != None).all()
    return [c[0] for c in cats]


@router.get("/{product_id}")
def get_product(product_id: int, db: Session = Depends(get_db)):
    """Ürün detayını getir."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Ürün bulunamadı")
    return product.to_dict()


@router.post("/")
def create_product(data: ProductCreate, db: Session = Depends(get_db)):
    """Yeni ürün oluştur."""
    existing = db.query(Product).filter(Product.sku == data.sku).first()
    if existing:
        raise HTTPException(status_code=400, detail="Bu SKU zaten mevcut")
    product = Product(**data.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product.to_dict()


@router.put("/{product_id}")
def update_product(product_id: int, data: ProductUpdate, db: Session = Depends(get_db)):
    """Ürün güncelle."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Ürün bulunamadı")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(product, key, value)
    db.commit()
    db.refresh(product)
    return product.to_dict()


@router.delete("/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    """Ürünü pasife al."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Ürün bulunamadı")
    product.is_active = False
    db.commit()
    return {"message": "Ürün silindi", "id": product_id}
