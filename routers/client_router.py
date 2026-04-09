from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.session import get_db
from controllers.client_controller import ClientsController
from common.schemas.client import ClientCreate, ClientOut

router = APIRouter(prefix="/clients", tags=["Clients"])

@router.get("", response_model=list[ClientOut])
def list_clients(db: Session = Depends(get_db)):
    return ClientsController(db).list_clients()

@router.post("", response_model=ClientOut)
def create_client(payload: ClientCreate, db: Session = Depends(get_db)):
    return ClientsController(db).create_client(payload)
