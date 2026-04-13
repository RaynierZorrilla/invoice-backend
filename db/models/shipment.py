import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base


class Shipment(Base):
    __tablename__ = "shipments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tracking_number: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False
    )
    customer_name: Mapped[str] = mapped_column(String(120), nullable=False)
    origin_country: Mapped[str] = mapped_column(String(100), nullable=False)
    destination_city_rd: Mapped[str] = mapped_column(String(100), nullable=False)
    shipment_type: Mapped[str] = mapped_column(String(10), nullable=False)  # Air | Sea
    weight: Mapped[float] = mapped_column(Float, nullable=False)
    weight_unit: Mapped[str] = mapped_column(String(10), nullable=False)  # lb | kg
    status: Mapped[str] = mapped_column(String(50), default="Received", nullable=False)
    estimated_delivery: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
