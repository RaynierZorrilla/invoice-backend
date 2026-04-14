import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from common.exceptions import DuplicateInvoiceNumberError, InvoiceNotFoundError
from common.schemas.invoice import InvoiceCreate, InvoiceStatusUpdate
from services.invoice_service import InvoiceService


class InvoiceController:
    def __init__(self, db: Session):
        self.service = InvoiceService(db)

    def list_invoices(
        self,
        status_filter: str | None = None,
        invoice_number: str | None = None,
    ):
        return self.service.list_invoices(
            status=status_filter,
            invoice_number=invoice_number,
        )

    def get_invoice(self, invoice_id: uuid.UUID):
        try:
            return self.service.get_invoice(invoice_id)
        except InvoiceNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Factura no encontrada."},
            ) from None

    def create_invoice(self, payload: InvoiceCreate):
        try:
            return self.service.create_invoice(payload)
        except DuplicateInvoiceNumberError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "message": "Ya existe una factura con este número.",
                    "invoice_number": exc.invoice_number,
                },
            ) from exc

    def update_status(
        self, invoice_id: uuid.UUID, payload: InvoiceStatusUpdate
    ):
        try:
            return self.service.update_status(invoice_id, payload)
        except InvoiceNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Factura no encontrada."},
            ) from None
