from sqlalchemy.orm import Session
from common.schemas.client import ClientCreate
from services.client_service import ClientsService

class ClientsController:
    def __init__(self, db: Session):
        self.service = ClientsService(db)

    def list_clients(self):
        return self.service.list_clients()

    def create_client(self, payload: ClientCreate):
        return self.service.create_client(payload)
