import uuid

from fastapi import HTTPException
from sqlalchemy.orm import Session

from common.exceptions import (
    DuplicateTrackingNumberError,
    InvalidStatusTransitionError,
)
from common.schemas.shipment import ShipmentCreate, ShipmentStatusUpdate
from services.shipment_service import ShipmentService, allowed_next_statuses


class ShipmentController:
    def __init__(self, db: Session):
        self.service = ShipmentService(db)

    def list_shipments(
        self,
        status: str | None = None,
        tracking_number: str | None = None,
    ):
        return self.service.list_shipments(
            status=status,
            tracking_number=tracking_number,
        )

    def get_shipment(self, shipment_id: uuid.UUID):
        obj = self.service.get_shipment(shipment_id)
        if obj is None:
            raise HTTPException(status_code=404, detail="Envío no encontrado.")
        return obj

    def update_status(self, shipment_id: uuid.UUID, payload: ShipmentStatusUpdate):
        try:
            obj = self.service.update_status(shipment_id, payload.status)
        except InvalidStatusTransitionError as exc:
            raise HTTPException(
                status_code=409,
                detail={
                    "message": "Transición de estado no permitida.",
                    "from_status": exc.from_status,
                    "to_status": exc.to_status,
                    "allowed_next": allowed_next_statuses(exc.from_status),
                },
            ) from exc
        if obj is None:
            raise HTTPException(status_code=404, detail="Envío no encontrado.")
        return obj

    def create_shipment(self, payload: ShipmentCreate):
        try:
            return self.service.create_shipment(payload)
        except DuplicateTrackingNumberError as exc:
            raise HTTPException(
                status_code=409,
                detail={
                    "message": "Ya existe un envío con este número de rastreo.",
                    "tracking_number": exc.tracking_number,
                },
            ) from exc
