"""
Veritabanı bağlantı ve oturum yönetimi.
SQLite + SQLAlchemy ile basit ve taşınabilir veritabanı yapısı.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# SQLite veritabanı dosyası backend klasöründe oluşturulacak
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'yzta_ecommerce.db')}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite için gerekli
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Her istek için bir veritabanı oturumu oluştur ve işlem bitince kapat."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Veritabanı tablolarını oluştur."""
    from models import Base as ModelsBase  # noqa: F811
    ModelsBase.metadata.create_all(bind=engine)
