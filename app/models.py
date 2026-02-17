"""Pydantic models for the Invoice PDF microservice."""

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class BookingItem(BaseModel):
    """A single line-item on the invoice."""

    description: str = Field(..., examples=["City Walking Tour – Full Day"])
    quantity: int = Field(..., ge=1, examples=[2])
    unit_price: float = Field(..., ge=0, examples=[75.00])


class BookingInvoiceRequest(BaseModel):
    """Full payload required to generate an invoice PDF."""

    invoice_number: str = Field(..., examples=["INV-2026-001"])
    customer_name: str = Field(..., examples=["Jane Doe"])
    customer_email: str = Field(..., examples=["jane@example.com"])
    customer_address: str = Field(
        ..., examples=["123 Main St, Jakarta 10110"]
    )
    booking_date: date = Field(..., examples=["2026-02-17"])
    due_date: date = Field(..., examples=["2026-03-17"])
    guide_name: str = Field(..., examples=["Jane Doe"])
    items: list[BookingItem] = Field(..., min_length=1)
    tax_rate: float = Field(default=0.0, ge=0, le=100, examples=[7.0])
    discount: float = Field(default=0.0, ge=0, examples=[10.00])
    notes: Optional[str] = Field(
        default=None, examples=["Thank you for choosing Guide Booker!"]
    )
    currency: str = Field(default="USD", examples=["USD"])
