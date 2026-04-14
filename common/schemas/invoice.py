from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

InvoiceCurrency = Literal["USD", "DOP"]
InvoiceStatus = Literal["Draft", "Sent", "Partially Paid", "Paid", "Overdue"]

_MONEY_QUANT = Decimal("0.01")


class InvoiceCreate(BaseModel):
    invoice_number: str = Field(min_length=1, max_length=50)
    client_id: UUID
    shipment_id: UUID | None = None

    currency: InvoiceCurrency
    fx_rate: Decimal | None = None

    subtotal: Decimal = Field(gt=0)
    taxes: Decimal = Field(default=Decimal("0"), ge=0)
    customs_fee: Decimal = Field(default=Decimal("0"), ge=0)
    insurance_fee: Decimal = Field(default=Decimal("0"), ge=0)
    handling_fee: Decimal = Field(default=Decimal("0"), ge=0)
    total: Decimal = Field(gt=0)

    issue_date: date
    due_date: date
    notes: str | None = Field(default=None, max_length=500)

    @field_validator("invoice_number")
    @classmethod
    def normalize_invoice_number(cls, value: str) -> str:
        return value.strip()

    @model_validator(mode="after")
    def validate_dates_and_total(self):
        if self.due_date < self.issue_date:
            raise ValueError(
                "La fecha de vencimiento no puede ser menor que la fecha de emisión."
            )

        calculated_total = (
            self.subtotal
            + self.taxes
            + self.customs_fee
            + self.insurance_fee
            + self.handling_fee
        ).quantize(_MONEY_QUANT)
        total_q = self.total.quantize(_MONEY_QUANT)

        if total_q != calculated_total:
            raise ValueError(
                "El total no coincide con la suma de subtotal, impuestos y cargos."
            )

        if self.currency == "USD" and self.fx_rate is None:
            raise ValueError("fx_rate es obligatorio cuando la moneda es USD.")

        return self


class InvoiceStatusUpdate(BaseModel):
    status: InvoiceStatus


class InvoiceOut(BaseModel):
    id: UUID
    invoice_number: str
    client_id: UUID
    shipment_id: UUID | None

    currency: InvoiceCurrency
    fx_rate: Decimal | None

    subtotal: Decimal
    taxes: Decimal
    customs_fee: Decimal
    insurance_fee: Decimal
    handling_fee: Decimal
    total: Decimal

    status: InvoiceStatus
    issue_date: date
    due_date: date
    notes: str | None

    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
