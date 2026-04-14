import uuid
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from common.exceptions import DuplicateInvoiceNumberError
from db.session import get_db
from main import app
from tests.conftest import make_invoice

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    app.dependency_overrides.clear()


def test_get_invoice_404():
    mock_db = MagicMock()
    configure_get(mock_db, None)
    app.dependency_overrides[get_db] = lambda: mock_db

    iid = uuid.uuid4()
    r = client.get(f"/api/invoices/{iid}")

    assert r.status_code == 404
    assert r.json()["detail"] == {"message": "Factura no encontrada."}


def test_get_invoice_200():
    row = make_invoice()
    mock_db = MagicMock()
    configure_get(mock_db, row)
    app.dependency_overrides[get_db] = lambda: mock_db

    r = client.get(f"/api/invoices/{row.id}")

    assert r.status_code == 200
    body = r.json()
    assert body["id"] == str(row.id)
    assert body["invoice_number"] == row.invoice_number
    assert body["status"] == "Draft"
    assert body["currency"] == "DOP"


def test_list_invoices_with_both_query_params():
    rows = [make_invoice(invoice_number="INV-0001", status="Paid")]
    mock_db = MagicMock()
    q = MagicMock()
    after_status = MagicMock()
    after_number = MagicMock()
    tail = MagicMock()
    mock_db.query.return_value = q
    q.filter.return_value = after_status
    after_status.filter.return_value = after_number
    after_number.order_by.return_value = tail
    tail.all.return_value = rows

    app.dependency_overrides[get_db] = lambda: mock_db

    r = client.get(
        "/api/invoices",
        params={"status": "Paid", "invoice_number": "INV-0001"},
    )

    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["invoice_number"] == "INV-0001"


def test_patch_invoice_status_200():
    row = make_invoice(status="Draft")
    mock_db = MagicMock()
    configure_get(mock_db, row)
    app.dependency_overrides[get_db] = lambda: mock_db

    r = client.patch(
        f"/api/invoices/{row.id}/status",
        json={"status": "Sent"},
    )

    assert r.status_code == 200
    assert r.json()["status"] == "Sent"
    mock_db.commit.assert_called_once()


def test_patch_invoice_status_404():
    mock_db = MagicMock()
    configure_get(mock_db, None)
    app.dependency_overrides[get_db] = lambda: mock_db

    iid = uuid.uuid4()
    r = client.patch(
        f"/api/invoices/{iid}/status",
        json={"status": "Sent"},
    )

    assert r.status_code == 404


def test_post_invoice_422_total_mismatch():
    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db

    r = client.post(
        "/api/invoices",
        json={
            "invoice_number": "INV-X",
            "client_id": str(uuid.uuid4()),
            "shipment_id": None,
            "currency": "DOP",
            "fx_rate": None,
            "subtotal": "100.00",
            "taxes": "0",
            "customs_fee": "0",
            "insurance_fee": "0",
            "handling_fee": "0",
            "total": "99.00",
            "issue_date": "2026-01-30",
            "due_date": "2026-02-05",
        },
    )

    assert r.status_code == 422


def test_post_invoice_422_usd_without_fx():
    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db

    r = client.post(
        "/api/invoices",
        json={
            "invoice_number": "INV-USD",
            "client_id": str(uuid.uuid4()),
            "currency": "USD",
            "fx_rate": None,
            "subtotal": "10.00",
            "taxes": "0",
            "customs_fee": "0",
            "insurance_fee": "0",
            "handling_fee": "0",
            "total": "10.00",
            "issue_date": "2026-01-30",
            "due_date": "2026-02-05",
        },
    )

    assert r.status_code == 422


def test_post_invoice_409_duplicate(monkeypatch):
    mock_db = MagicMock()

    def fake_create(_self, _payload):
        raise DuplicateInvoiceNumberError("DUP-INV-1")

    monkeypatch.setattr(
        "services.invoice_service.InvoiceService.create_invoice",
        fake_create,
    )
    app.dependency_overrides[get_db] = lambda: mock_db

    r = client.post(
        "/api/invoices",
        json={
            "invoice_number": "DUP-INV-1",
            "client_id": str(uuid.uuid4()),
            "currency": "DOP",
            "fx_rate": None,
            "subtotal": "100.00",
            "taxes": "0",
            "customs_fee": "0",
            "insurance_fee": "0",
            "handling_fee": "0",
            "total": "100.00",
            "issue_date": "2026-01-30",
            "due_date": "2026-02-05",
        },
    )

    assert r.status_code == 409
    assert r.json()["detail"]["invoice_number"] == "DUP-INV-1"


def test_post_invoice_200_monkeypatch(monkeypatch):
    created = make_invoice(
        invoice_number="INV-OK-1",
        total=Decimal("1355.00"),
        subtotal=Decimal("1000.00"),
        taxes=Decimal("180.00"),
        customs_fee=Decimal("100.00"),
        insurance_fee=Decimal("50.00"),
        handling_fee=Decimal("25.00"),
        issue_date=date(2026, 1, 30),
        due_date=date(2026, 2, 5),
    )

    def fake_create(_self, _payload):
        return created

    monkeypatch.setattr(
        "services.invoice_service.InvoiceService.create_invoice",
        fake_create,
    )
    app.dependency_overrides[get_db] = lambda: MagicMock()

    r = client.post(
        "/api/invoices",
        json={
            "invoice_number": "INV-OK-1",
            "client_id": str(created.client_id),
            "shipment_id": None,
            "currency": "DOP",
            "fx_rate": None,
            "subtotal": "1000.00",
            "taxes": "180.00",
            "customs_fee": "100.00",
            "insurance_fee": "50.00",
            "handling_fee": "25.00",
            "total": "1355.00",
            "issue_date": "2026-01-30",
            "due_date": "2026-02-05",
        },
    )

    assert r.status_code == 200
    assert r.json()["invoice_number"] == "INV-OK-1"


def configure_get(mock_db, invoice_or_none):
    q = MagicMock()
    after = MagicMock()
    mock_db.query.return_value = q
    q.filter.return_value = after
    after.first.return_value = invoice_or_none
