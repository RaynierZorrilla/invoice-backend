from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from common.exceptions import DuplicateTrackingNumberError
from common.schemas.shipment import ShipmentCreate
from db.models.shipment import Shipment


def _is_unique_tracking_number_violation(exc: IntegrityError) -> bool:
    orig = exc.orig
    detail = str(orig).lower() if orig is not None else ""
    return "tracking_number" in detail and (
        "unique" in detail or "duplicate key" in detail
    )


class ShipmentService:
    def __init__(self, db: Session):
        self.db = db

    def list_shipments(self):
        return self.db.query(Shipment).order_by(Shipment.created_at.desc()).all()

    def create_shipment(self, payload: ShipmentCreate):
        obj = Shipment(**payload.model_dump())
        self.db.add(obj)
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            if _is_unique_tracking_number_violation(exc):
                raise DuplicateTrackingNumberError(
                    payload.tracking_number
                ) from exc
            raise
        self.db.refresh(obj)
        return obj
