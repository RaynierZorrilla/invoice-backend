import uuid
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from common.exceptions import DuplicateInvoiceNumberError, InvoiceNotFoundError
from common.schemas.invoice import InvoiceCreate, InvoiceStatusUpdate
from db.models.invoice import Invoice
from services.invoice_service import InvoiceService

from tests.conftest import configure_query_get, configure_query_list, make_invoice


def _valid_dop_create(**overrides) -> InvoiceCreate:
    data = {
        "invoice_number": "INV-SVC-001",
        "client_id": uuid.uuid4(),
        "shipment_id": None,
        "currency": "DOP",
        "fx_rate": None,
        "subtotal": Decimal("1000.00"),
        "taxes": Decimal("180.00"),
        "customs_fee": Decimal("100.00"),
        "insurance_fee": Decimal("50.00"),
        "handling_fee": Decimal("25.00"),
        "total": Decimal("1355.00"),
        "issue_date": date(2026, 1, 30),
        "due_date": date(2026, 2, 5),
        "notes": "Nota",
    }
    data.update(overrides)
    return InvoiceCreate(**data)


def test_invoice_create_schema_usd_requires_fx():
    with pytest.raises(ValidationError) as exc:
        InvoiceCreate(
            invoice_number="INV-U1",
            client_id=uuid.uuid4(),
            currency="USD",
            fx_rate=None,
            subtotal=Decimal("10.00"),
            taxes=Decimal("0"),
            customs_fee=Decimal("0"),
            insurance_fee=Decimal("0"),
            handling_fee=Decimal("0"),
            total=Decimal("10.00"),
            issue_date=date(2026, 1, 1),
            due_date=date(2026, 1, 2),
        )
    assert "fx_rate" in str(exc.value).lower()


def test_invoice_create_schema_total_mismatch():
    with pytest.raises(ValidationError) as exc:
        InvoiceCreate(
            invoice_number="INV-BAD",
            client_id=uuid.uuid4(),
            currency="DOP",
            fx_rate=None,
            subtotal=Decimal("100.00"),
            taxes=Decimal("0"),
            customs_fee=Decimal("0"),
            insurance_fee=Decimal("0"),
            handling_fee=Decimal("0"),
            total=Decimal("99.00"),
            issue_date=date(2026, 1, 1),
            due_date=date(2026, 1, 2),
        )
    assert "total" in str(exc.value).lower() or "coincide" in str(exc.value).lower()


def test_invoice_create_schema_due_before_issue():
    with pytest.raises(ValidationError) as exc:
        InvoiceCreate(
            invoice_number="INV-DATES",
            client_id=uuid.uuid4(),
            currency="DOP",
            fx_rate=None,
            subtotal=Decimal("10.00"),
            taxes=Decimal("0"),
            customs_fee=Decimal("0"),
            insurance_fee=Decimal("0"),
            handling_fee=Decimal("0"),
            total=Decimal("10.00"),
            issue_date=date(2026, 2, 5),
            due_date=date(2026, 1, 1),
        )
    assert "vencimiento" in str(exc.value).lower()


def test_list_invoices_no_filters(mock_session):
    rows = [make_invoice(invoice_number="B"), make_invoice(invoice_number="A")]
    q, tail = configure_query_list(mock_session, rows)

    svc = InvoiceService(mock_session)
    out = svc.list_invoices()

    assert out == rows
    mock_session.query.assert_called_once_with(Invoice)
    q.order_by.assert_called_once()
    tail.all.assert_called_once()


def test_list_invoices_status_filter(mock_session):
    rows = [make_invoice(status="Draft")]
    q = MagicMock()
    after_status = MagicMock()
    tail = MagicMock()
    mock_session.query.return_value = q
    q.filter.return_value = after_status
    after_status.order_by.return_value = tail
    tail.all.return_value = rows

    out = InvoiceService(mock_session).list_invoices(status="Draft")
    assert out == rows


def test_list_invoices_status_and_number_filters(mock_session):
    rows = [make_invoice(invoice_number="INV-0001", status="Paid")]
    q = MagicMock()
    after_status = MagicMock()
    after_number = MagicMock()
    tail = MagicMock()
    mock_session.query.return_value = q
    q.filter.return_value = after_status
    after_status.filter.return_value = after_number
    after_number.order_by.return_value = tail
    tail.all.return_value = rows

    out = InvoiceService(mock_session).list_invoices(
        status="Paid",
        invoice_number="INV-0001",
    )
    assert out == rows


def test_list_invoices_invoice_number_blank_skips_filter(mock_session):
    q, tail = configure_query_list(mock_session, [])
    InvoiceService(mock_session).list_invoices(invoice_number="   ")
    q.filter.assert_not_called()


def test_get_invoice_found(mock_session):
    iid = uuid.uuid4()
    row = make_invoice(id=iid)
    configure_query_get(mock_session, row)
    assert InvoiceService(mock_session).get_invoice(iid) is row


def test_get_invoice_not_found(mock_session):
    iid = uuid.uuid4()
    configure_query_get(mock_session, None)
    with pytest.raises(InvoiceNotFoundError):
        InvoiceService(mock_session).get_invoice(iid)


def test_create_invoice_success(mock_session):
    payload = _valid_dop_create()
    svc = InvoiceService(mock_session)
    out = svc.create_invoice(payload)

    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once()
    assert isinstance(out, Invoice)
    assert out.invoice_number == payload.invoice_number
    assert out.client_id == payload.client_id


def test_create_invoice_duplicate_number(mock_session):
    payload = _valid_dop_create(invoice_number="DUP-INV")
    err = IntegrityError(
        "stmt",
        {},
        orig=Exception("duplicate key ... invoice_number ..."),
    )
    mock_session.commit.side_effect = err

    with pytest.raises(DuplicateInvoiceNumberError):
        InvoiceService(mock_session).create_invoice(payload)

    mock_session.rollback.assert_called_once()


def test_update_status_success(mock_session):
    iid = uuid.uuid4()
    row = make_invoice(id=iid, status="Draft")
    configure_query_get(mock_session, row)

    out = InvoiceService(mock_session).update_status(
        iid,
        InvoiceStatusUpdate(status="Sent"),
    )

    assert out.status == "Sent"
    mock_session.commit.assert_called_once()


def test_update_status_not_found(mock_session):
    iid = uuid.uuid4()
    configure_query_get(mock_session, None)

    with pytest.raises(InvoiceNotFoundError):
        InvoiceService(mock_session).update_status(
            iid, InvoiceStatusUpdate(status="Sent")
        )
