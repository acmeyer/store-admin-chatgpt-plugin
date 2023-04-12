from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship, Session
from datetime import datetime

from db.database import Base
from .models import Shop, ApiKey


class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"))
    last_used_at = Column(DateTime)
    last_used_ip = Column(String)
    last_used_user_agent = Column(String)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    shop = relationship("Shop", back_populates="api_keys")


class Shop(Base):
    __tablename__ = "shops"

    id = Column(Integer, primary_key=True, index=True)
    shopify_domain = Column(String, unique=True, index=True)
    shopify_token = Column(String)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    access_scopes = Column(String)

    api_keys = relationship("ApiKey", back_populates="shop")



def update_api_key_last_used(db: Session, key: str):
    api_key = db.query(ApiKey).filter(ApiKey.key == key).first()
    if api_key:
        api_key.last_used_at = datetime.utcnow()
        db.add(api_key)
        db.commit()


def get_shop_by_api_key(db: Session, api_key: str) -> Shop:
    update_api_key_last_used(db, api_key)
    return db.query(Shop).join(ApiKey, Shop.api_keys).filter(ApiKey.key == api_key).first()