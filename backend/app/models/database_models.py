"""
===========================================================
Database Models
-----------------------------------------------------------
SQLAlchemy ORM models for the whole system. Uses SQLite by
default (zero setup) but works with Postgres too if you set
DATABASE_URL in .env.
===========================================================
"""

from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, JSON, Text
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String, nullable=True)
    purchase_order_number = Column(String, nullable=True)
    order_date = Column(String, nullable=True)
    delivery_date = Column(String, nullable=True)
    gst_number = Column(String, nullable=True)
    currency = Column(String, nullable=True, default="INR")

    status = Column(String, default="received")
    # received -> extracted -> validated -> recovered -> inventory_checked
    # -> billed -> completed / rejected

    confidence_score = Column(Float, nullable=True)
    raw_extraction = Column(JSON, nullable=True)
    validation_errors = Column(JSON, nullable=True)
    validation_warnings = Column(JSON, nullable=True)

    source_file_name = Column(String, nullable=True)
    source_document_type = Column(String, nullable=True)
    intake_source = Column(String, default="manual_upload")  # "manual_upload" or "email"

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))

    product_code = Column(String, nullable=True)
    product_name = Column(String, nullable=True)
    quantity = Column(Float, nullable=True)
    unit_price = Column(Float, nullable=True)
    total_price = Column(Float, nullable=True)
    confidence = Column(Float, nullable=True)

    in_stock = Column(String, nullable=True)  # "yes" / "no" / "partial"

    order = relationship("Order", back_populates="items")


class InventoryItem(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    product_code = Column(String, unique=True, index=True)
    product_name = Column(String)
    quantity_available = Column(Float, default=0)
    unit_price = Column(Float, default=0)


class SystemLog(Base):
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, nullable=True)
    agent = Column(String)
    message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, nullable=True)
    level = Column(String, default="info")  # "info" | "warning" | "error"
    title = Column(String)
    message = Column(Text)
    is_read = Column(String, default="no")  # "yes" / "no" (kept as string for simple SQLite compatibility)
    created_at = Column(DateTime, default=datetime.utcnow)
