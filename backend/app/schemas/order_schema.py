"""
===========================================================
Order Schemas
-----------------------------------------------------------
Pydantic models used by the FastAPI routes for response
validation and auto-generated Swagger docs.
===========================================================
"""

from typing import List, Optional
from pydantic import BaseModel


class OrderItemSchema(BaseModel):
    product_code: Optional[str] = None
    product_name: Optional[str] = None
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    total_price: Optional[float] = None
    confidence: Optional[float] = None
    in_stock: Optional[str] = None


class OrderResponseSchema(BaseModel):
    status: str
    order_id: Optional[int] = None
    customer_name: Optional[str] = None
    purchase_order_number: Optional[str] = None
    order_date: Optional[str] = None
    delivery_date: Optional[str] = None
    currency: Optional[str] = None
    confidence_score: Optional[float] = None
    validation_errors: List[str] = []
    validation_warnings: List[str] = []
    items: List[OrderItemSchema] = []


class UploadResponseSchema(BaseModel):
    status: str
    message: Optional[str] = None
    order: Optional[OrderResponseSchema] = None
