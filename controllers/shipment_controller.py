from fastapi import HTTPException
from sqlalchemy.orm import Session

from common.exceptions import DuplicateTrackingNumberError
from common.schemas.shipment import ShipmentCreate
from services.shipment_service import ShipmentService


class ShipmentController:
    def __init__(self, db: Session):
        self.service = ShipmentService(db)

    def list_shipments(self):
        return self.service.list_shipments()

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
