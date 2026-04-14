import os
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

# main -> db.session exige DATABASE_URL al importar; no se usa en tests mockeados
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://test:test@127.0.0.1:65432/shipinvoice_test",
)


def make_shipment(**overrides):
    now = datetime(2026, 4, 13, 12, 0, 0, tzinfo=timezone.utc)
    fields = {
        "id": uuid.uuid4(),
        "tracking_number": "SHP-TEST-001",
        "customer_name": "Cliente Demo",
        "origin_country": "US",
        "destination_city_rd": "Santo Domingo",
        "shipment_type": "Air",
        "weight": 10.5,
        "weight_unit": "lb",
        "status": "Received",
        "estimated_delivery": None,
        "created_at": now,
        "updated_at": now,
    }
    fields.update(overrides)
    return SimpleNamespace(**fields)


@pytest.fixture
def mock_session():
    return MagicMock()


def configure_query_list(mock_db, rows):
    """db.query(Shipment).[filter...].order_by(...).all() -> rows"""
    q = MagicMock()
    tail = MagicMock()
    mock_db.query.return_value = q
    q.order_by.return_value = tail
    tail.all.return_value = rows
    return q, tail


def configure_query_get(mock_db, shipment_or_none):
    """db.query(Shipment).filter(...).first() -> shipment_or_none"""
    q = MagicMock()
    after_filter = MagicMock()
    mock_db.query.return_value = q
    q.filter.return_value = after_filter
    after_filter.first.return_value = shipment_or_none
    return q, after_filter
