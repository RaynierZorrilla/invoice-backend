import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from common.exceptions import (
    DuplicateTrackingNumberError,
    InvalidStatusTransitionError,
)
from common.schemas.shipment import ShipmentCreate
from db.models.shipment import Shipment

# Forward-only lifecycle (must match ShipmentStatus in common/schemas/shipment.py)
_ALLOWED_NEXT: dict[str, frozenset[str]] = {
    "Received": frozenset({"In Transit"}),
    "In Transit": frozenset({"Arrived RD"}),
    "Arrived RD": frozenset({"Customs"}),
    "Customs": frozenset({"Delivered"}),
    "Delivered": frozenset(),
}


def allowed_next_statuses(current: str) -> list[str]:
    return sorted(_ALLOWED_NEXT.get(current, frozenset()))


def _is_unique_tracking_number_violation(exc: IntegrityError) -> bool:
    orig = exc.orig
    detail = str(orig).lower() if orig is not None else ""
    return "tracking_number" in detail and (
        "unique" in detail or "duplicate key" in detail
    )


class ShipmentService:
    def __init__(self, db: Session):
        self.db = db

    def list_shipments(
        self,
        status: str | None = None,
        tracking_number: str | None = None,
    ):
        q = self.db.query(Shipment)
        if status is not None:
            q = q.filter(Shipment.status == status)
        if tracking_number is not None:
            tn = tracking_number.strip()
            if tn:
                q = q.filter(Shipment.tracking_number == tn)
        # Newest first; tie-break by id so order is stable for identical created_at
        return q.order_by(Shipment.created_at.desc(), Shipment.id.desc()).all()

    def get_shipment(self, shipment_id: uuid.UUID) -> Shipment | None:
        return self.db.query(Shipment).filter(Shipment.id == shipment_id).first()

    def update_status(
        self, shipment_id: uuid.UUID, status: str
    ) -> Shipment | None:
        obj = self.get_shipment(shipment_id)
        if obj is None:
            return None
        if obj.status == status:
            return obj
        allowed = _ALLOWED_NEXT.get(obj.status, frozenset())
        if status not in allowed:
            raise InvalidStatusTransitionError(obj.status, status)
        obj.status = status
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

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
