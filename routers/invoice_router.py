import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from common.schemas.invoice import (
    InvoiceCreate,
    InvoiceOut,
    InvoiceStatus,
    InvoiceStatusUpdate,
)
from controllers.invoice_controller import InvoiceController
from db.session import get_db

router = APIRouter(prefix="/invoices", tags=["Invoices"])


@router.get("", response_model=list[InvoiceOut])
def list_invoices(
    status: InvoiceStatus | None = Query(default=None),
    invoice_number: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return InvoiceController(db).list_invoices(
        status_filter=status,
        invoice_number=invoice_number,
    )


@router.get("/{invoice_id}", response_model=InvoiceOut)
def get_invoice(invoice_id: uuid.UUID, db: Session = Depends(get_db)):
    return InvoiceController(db).get_invoice(invoice_id)


@router.post("", response_model=InvoiceOut)
def create_invoice(payload: InvoiceCreate, db: Session = Depends(get_db)):
    return InvoiceController(db).create_invoice(payload)


@router.patch("/{invoice_id}/status", response_model=InvoiceOut)
def update_invoice_status(
    invoice_id: uuid.UUID,
    payload: InvoiceStatusUpdate,
    db: Session = Depends(get_db),
):
    return InvoiceController(db).update_status(invoice_id, payload)
