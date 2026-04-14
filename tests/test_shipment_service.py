import uuid
from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import IntegrityError

from common.exceptions import DuplicateTrackingNumberError, InvalidStatusTransitionError
from common.schemas.shipment import ShipmentCreate
from db.models.shipment import Shipment
from services.shipment_service import ShipmentService, allowed_next_statuses

from tests.conftest import configure_query_get, configure_query_list, make_shipment


def test_allowed_next_statuses_pipeline():
    assert allowed_next_statuses("Received") == ["In Transit"]
    assert allowed_next_statuses("In Transit") == ["Arrived RD"]
    assert allowed_next_statuses("Arrived RD") == ["Customs"]
    assert allowed_next_statuses("Customs") == ["Delivered"]
    assert allowed_next_statuses("Delivered") == []
    assert allowed_next_statuses("UnknownLegacy") == []


def test_list_shipments_no_filters_order_and_results(mock_session):
    rows = [make_shipment(tracking_number="B"), make_shipment(tracking_number="A")]
    q, tail = configure_query_list(mock_session, rows)

    svc = ShipmentService(mock_session)
    out = svc.list_shipments()

    assert out == rows
    mock_session.query.assert_called_once_with(Shipment)
    q.order_by.assert_called_once()
    tail.all.assert_called_once()


def test_list_shipments_with_status_filter(mock_session):
    rows = [make_shipment(status="Received")]
    q = MagicMock()
    after_status = MagicMock()
    tail = MagicMock()
    mock_session.query.return_value = q
    q.filter.return_value = after_status
    after_status.order_by.return_value = tail
    tail.all.return_value = rows

    svc = ShipmentService(mock_session)
    out = svc.list_shipments(status="Received")

    assert out == rows
    q.filter.assert_called_once()


def test_list_shipments_tracking_strip_empty_ignored(mock_session):
    q, tail = configure_query_list(mock_session, [])
    svc = ShipmentService(mock_session)
    svc.list_shipments(tracking_number="   ")
    q.filter.assert_not_called()


def test_get_shipment_found(mock_session):
    sid = uuid.uuid4()
    row = make_shipment(id=sid)
    configure_query_get(mock_session, row)

    svc = ShipmentService(mock_session)
    assert svc.get_shipment(sid) is row


def test_get_shipment_not_found(mock_session):
    sid = uuid.uuid4()
    configure_query_get(mock_session, None)

    assert ShipmentService(mock_session).get_shipment(sid) is None


def test_update_status_not_found(mock_session):
    sid = uuid.uuid4()
    configure_query_get(mock_session, None)

    assert (
        ShipmentService(mock_session).update_status(sid, "In Transit") is None
    )


def test_update_status_idempotent_no_commit(mock_session):
    sid = uuid.uuid4()
    row = make_shipment(id=sid, status="Received")
    configure_query_get(mock_session, row)

    svc = ShipmentService(mock_session)
    out = svc.update_status(sid, "Received")

    assert out is row
    mock_session.commit.assert_not_called()


def test_update_status_valid_transition(mock_session):
    sid = uuid.uuid4()
    row = make_shipment(id=sid, status="Received")
    configure_query_get(mock_session, row)

    svc = ShipmentService(mock_session)
    out = svc.update_status(sid, "In Transit")

    assert out is row
    assert row.status == "In Transit"
    mock_session.add.assert_called_once_with(row)
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once_with(row)


def test_update_status_invalid_transition(mock_session):
    sid = uuid.uuid4()
    row = make_shipment(id=sid, status="Received")
    configure_query_get(mock_session, row)

    with pytest.raises(InvalidStatusTransitionError) as exc:
        ShipmentService(mock_session).update_status(sid, "Delivered")

    assert exc.value.from_status == "Received"
    assert exc.value.to_status == "Delivered"
    mock_session.commit.assert_not_called()


def test_create_shipment_duplicate_tracking(mock_session):
    payload = ShipmentCreate(
        tracking_number="DUP-1",
        customer_name="X",
        origin_country="US",
        destination_city_rd="SD",
        shipment_type="Air",
        weight=1.0,
        weight_unit="kg",
    )
    err = IntegrityError("stmt", {}, orig=Exception("duplicate key ... tracking_number"))
    mock_session.commit.side_effect = err

    with pytest.raises(DuplicateTrackingNumberError):
        ShipmentService(mock_session).create_shipment(payload)

    mock_session.rollback.assert_called_once()
