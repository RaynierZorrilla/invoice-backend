import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from common.exceptions import DuplicateInvoiceNumberError, InvoiceNotFoundError
from common.schemas.invoice import InvoiceCreate, InvoiceStatusUpdate
from db.models.invoice import Invoice


def _is_unique_invoice_number_violation(exc: IntegrityError) -> bool:
    orig = exc.orig
    detail = str(orig).lower() if orig is not None else ""
    return "invoice_number" in detail and (
        "unique" in detail or "duplicate key" in detail
    )


class InvoiceService:
    def __init__(self, db: Session):
        self.db = db

    def list_invoices(
        self,
        status: str | None = None,
        invoice_number: str | None = None,
    ):
        query = self.db.query(Invoice)

        if status is not None:
            query = query.filter(Invoice.status == status)

        if invoice_number is not None:
            cleaned = invoice_number.strip()
            if cleaned:
                query = query.filter(Invoice.invoice_number == cleaned)

        return query.order_by(
            Invoice.created_at.desc(), Invoice.id.desc()
        ).all()

    def get_invoice(self, invoice_id: uuid.UUID) -> Invoice:
        invoice = (
            self.db.query(Invoice).filter(Invoice.id == invoice_id).first()
        )
        if invoice is None:
            raise InvoiceNotFoundError
        return invoice

    def create_invoice(self, payload: InvoiceCreate) -> Invoice:
        data = payload.model_dump(mode="python")
        obj = Invoice(**data)
        self.db.add(obj)
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            if _is_unique_invoice_number_violation(exc):
                raise DuplicateInvoiceNumberError(
                    payload.invoice_number
                ) from exc
            raise
        self.db.refresh(obj)
        return obj

    def update_status(
        self, invoice_id: uuid.UUID, payload: InvoiceStatusUpdate
    ) -> Invoice:
        invoice = (
            self.db.query(Invoice).filter(Invoice.id == invoice_id).first()
        )
        if invoice is None:
            raise InvoiceNotFoundError

        invoice.status = payload.status
        self.db.add(invoice)
        self.db.commit()
        self.db.refresh(invoice)
        return invoice
