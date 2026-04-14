import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from common.schemas.shipment import (
    ShipmentCreate,
    ShipmentOut,
    ShipmentStatus,
    ShipmentStatusUpdate,
)
from controllers.shipment_controller import ShipmentController
from db.session import get_db

router = APIRouter(prefix="/shipments", tags=["Shipments"])


@router.get("", response_model=list[ShipmentOut])
def list_shipments(
    status: ShipmentStatus | None = Query(None),
    tracking_number: str | None = Query(None),
    db: Session = Depends(get_db),
):
    return ShipmentController(db).list_shipments(
        status=status,
        tracking_number=tracking_number,
    )


@router.post("", response_model=ShipmentOut)
def create_shipment(payload: ShipmentCreate, db: Session = Depends(get_db)):
    return ShipmentController(db).create_shipment(payload)


@router.get("/{shipment_id}", response_model=ShipmentOut)
def get_shipment(shipment_id: uuid.UUID, db: Session = Depends(get_db)):
    return ShipmentController(db).get_shipment(shipment_id)


@router.patch("/{shipment_id}/status", response_model=ShipmentOut)
def patch_shipment_status(
    shipment_id: uuid.UUID,
    payload: ShipmentStatusUpdate,
    db: Session = Depends(get_db),
):
    return ShipmentController(db).update_status(shipment_id, payload)
