from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ShipmentCreate(BaseModel):
    tracking_number: str = Field(..., min_length=1, max_length=50)
    customer_name: str
    origin_country: str
    destination_city_rd: str
    shipment_type: Literal["Air", "Sea"]
    weight: float = Field(..., gt=0)
    weight_unit: Literal["lb", "kg"]
    estimated_delivery: datetime | None = None

    @field_validator("tracking_number", mode="before")
    @classmethod
    def strip_tracking_number(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip()
        return v


class ShipmentOut(BaseModel):
    id: UUID
    tracking_number: str
    customer_name: str
    origin_country: str
    destination_city_rd: str
    shipment_type: str
    weight: float
    weight_unit: str
    status: str
    estimated_delivery: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
