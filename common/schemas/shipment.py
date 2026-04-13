from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ShipmentCreate(BaseModel):
    tracking_number: str
    customer_name: str
    origin_country: str
    destination_city_rd: str
    shipment_type: str
    weight: float
    weight_unit: str
    estimated_delivery: datetime | None = None


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
