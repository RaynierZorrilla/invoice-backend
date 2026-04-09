from pydantic import BaseModel, EmailStr
from datetime import datetime
from uuid import UUID

class ClientCreate(BaseModel):
    name: str
    phone: str
    email: EmailStr | None = None
    document_type: str
    document_number: str
    address_rd: str
    notes: str | None = None

class ClientOut(BaseModel):
    id: UUID
    name: str
    phone: str
    email: EmailStr | None
    document_type: str
    document_number: str
    address_rd: str
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
