from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from common.schemas.shipment import ShipmentCreate, ShipmentOut
from controllers.shipment_controller import ShipmentController
from db.session import get_db

router = APIRouter(prefix="/shipments", tags=["Shipments"])


@router.get("", response_model=list[ShipmentOut])
def list_shipments(db: Session = Depends(get_db)):
    return ShipmentController(db).list_shipments()


@router.post("", response_model=ShipmentOut)
def create_shipment(payload: ShipmentCreate, db: Session = Depends(get_db)):
    return ShipmentController(db).create_shipment(payload)
