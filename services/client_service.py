from sqlalchemy.orm import Session
from db.models.client import Client
from common.schemas.client import ClientCreate

class ClientsService:
    def __init__(self, db: Session):
        self.db = db

    def list_clients(self):
        return self.db.query(Client).order_by(Client.created_at.desc()).all()

    def create_client(self, payload: ClientCreate):
        obj = Client(**payload.model_dump())
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj
