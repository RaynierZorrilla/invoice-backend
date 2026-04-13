from sqlalchemy.orm import Session

from common.schemas.shipment import ShipmentCreate
from db.models.shipment import Shipment


class ShipmentService:
    def __init__(self, db: Session):
        self.db = db

    def list_shipments(self):
        return self.db.query(Shipment).order_by(Shipment.created_at.desc()).all()

    def create_shipment(self, payload: ShipmentCreate):
        obj = Shipment(**payload.model_dump())
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj
