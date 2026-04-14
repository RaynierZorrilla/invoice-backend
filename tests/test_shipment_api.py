import uuid
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from common.exceptions import DuplicateTrackingNumberError
from db.session import get_db
from main import app
from tests.conftest import make_shipment

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    app.dependency_overrides.clear()


def test_get_shipment_404():
    mock_db = MagicMock()
    q = MagicMock()
    after = MagicMock()
    mock_db.query.return_value = q
    q.filter.return_value = after
    after.first.return_value = None

    app.dependency_overrides[get_db] = lambda: mock_db

    sid = uuid.uuid4()
    r = client.get(f"/api/shipments/{sid}")

    assert r.status_code == 404
    assert r.json()["detail"] == "Envío no encontrado."


def test_get_shipment_200():
    row = make_shipment()
    mock_db = MagicMock()
    q = MagicMock()
    after = MagicMock()
    mock_db.query.return_value = q
    q.filter.return_value = after
    after.first.return_value = row

    app.dependency_overrides[get_db] = lambda: mock_db

    r = client.get(f"/api/shipments/{row.id}")

    assert r.status_code == 200
    body = r.json()
    assert body["id"] == str(row.id)
    assert body["tracking_number"] == row.tracking_number
    assert body["status"] == "Received"


def test_patch_status_409_invalid_transition():
    row = make_shipment(status="Received")
    mock_db = MagicMock()
    q = MagicMock()
    after = MagicMock()
    mock_db.query.return_value = q
    q.filter.return_value = after
    after.first.return_value = row

    app.dependency_overrides[get_db] = lambda: mock_db

    r = client.patch(
        f"/api/shipments/{row.id}/status",
        json={"status": "Delivered"},
    )

    assert r.status_code == 409
    detail = r.json()["detail"]
    assert detail["message"] == "Transición de estado no permitida."
    assert detail["from_status"] == "Received"
    assert detail["to_status"] == "Delivered"
    assert detail["allowed_next"] == ["In Transit"]


def test_patch_status_200():
    row = make_shipment(status="Received")
    mock_db = MagicMock()
    q = MagicMock()
    after = MagicMock()
    mock_db.query.return_value = q
    q.filter.return_value = after
    after.first.return_value = row

    app.dependency_overrides[get_db] = lambda: mock_db

    r = client.patch(
        f"/api/shipments/{row.id}/status",
        json={"status": "In Transit"},
    )

    assert r.status_code == 200
    assert r.json()["status"] == "In Transit"
    mock_db.commit.assert_called_once()


def test_list_shipments_with_query_params():
    rows = [make_shipment(tracking_number="SHP-2026-0001", status="Received")]
    mock_db = MagicMock()
    q = MagicMock()
    after_status = MagicMock()
    after_tracking = MagicMock()
    tail = MagicMock()
    mock_db.query.return_value = q
    q.filter.return_value = after_status
    after_status.filter.return_value = after_tracking
    after_tracking.order_by.return_value = tail
    tail.all.return_value = rows

    app.dependency_overrides[get_db] = lambda: mock_db

    r = client.get(
        "/api/shipments",
        params={"status": "Received", "tracking_number": "SHP-2026-0001"},
    )

    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["tracking_number"] == "SHP-2026-0001"


def test_post_shipment_409_duplicate(monkeypatch):
    mock_db = MagicMock()

    def fake_create(_self, _payload):
        raise DuplicateTrackingNumberError("DUP-1")

    monkeypatch.setattr(
        "services.shipment_service.ShipmentService.create_shipment",
        fake_create,
    )

    app.dependency_overrides[get_db] = lambda: mock_db

    r = client.post(
        "/api/shipments",
        json={
            "tracking_number": "DUP-1",
            "customer_name": "A",
            "origin_country": "US",
            "destination_city_rd": "SD",
            "shipment_type": "Air",
            "weight": 1,
            "weight_unit": "kg",
        },
    )

    assert r.status_code == 409
    assert "tracking_number" in r.json()["detail"]
