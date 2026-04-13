from sqlalchemy.orm import Session

from common.schemas.shipment import ShipmentCreate
from services.shipment_service import ShipmentService


class ShipmentController:
    def __init__(self, db: Session):
        self.service = ShipmentService(db)

    def list_shipments(self):
        return self.service.list_shipments()

    def create_shipment(self, payload: ShipmentCreate):
        return self.service.create_shipment(payload)
