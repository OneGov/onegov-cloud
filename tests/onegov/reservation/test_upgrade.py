from __future__ import annotations

from datetime import datetime
from libres.db.models import Reservation, ReservedSlot
from onegov.reservation import ResourceCollection
from onegov.reservation.upgrade import backfill_reserved_slot_source_ids
from sqlalchemy import text
from uuid import uuid4


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from libres.context.core import Context


def test_backfill_reserved_slot_source_ids(libres_context: Context) -> None:
    collection = ResourceCollection(libres_context)
    resource = collection.add('Lounge', 'Europe/Zurich')
    scheduler = resource.get_scheduler(libres_context)
    session = scheduler.session

    # partly-available allocation with two sibling reservations (one token)
    scheduler.allocate(
        (datetime(2015, 8, 5, 8), datetime(2015, 8, 5, 18)),
        partly_available=True,
    )
    sid = uuid4()
    token = scheduler.reserve(
        'info@example.org',
        (datetime(2015, 8, 5, 8), datetime(2015, 8, 5, 10)),
        session_id=sid, single_token_per_session=True,
    )
    scheduler.reserve(
        'info@example.org',
        (datetime(2015, 8, 5, 10), datetime(2015, 8, 5, 12)),
        session_id=sid, single_token_per_session=True,
    )
    scheduler.approve_reservations(token)

    # non-partly allocation reserved for a narrower sub-range: the slot spans
    # the whole allocation and is thus wider than the reservation
    scheduler.allocate(
        (datetime(2015, 8, 6, 8), datetime(2015, 8, 6, 18)),
        partly_available=False,
    )
    np_token = scheduler.reserve(
        'info@example.org',
        (datetime(2015, 8, 6, 9), datetime(2015, 8, 6, 17)),
    )
    scheduler.approve_reservations(np_token)

    # a blocker
    scheduler.add_blocker(
        (datetime(2015, 8, 5, 14), datetime(2015, 8, 5, 16)),
    )

    # a slot whose reservation we delete afterwards -> orphan
    orphan_token = scheduler.reserve(
        'info@example.org',
        (datetime(2015, 8, 5, 16), datetime(2015, 8, 5, 18)),
    )
    scheduler.approve_reservations(orphan_token)
    session.flush()

    # ground truth: libres already set source_id correctly on creation
    slots = session.query(ReservedSlot).all()
    expected = {(s.resource, s.start): s.source_id for s in slots}
    orphan_keys = {
        (s.resource, s.start) for s in slots
        if s.reservation_token == orphan_token
    }
    assert orphan_keys
    assert all(v is not None for v in expected.values())

    # simulate the pre-migration state: source_id is still nullable, the
    # orphan's reservation is gone and no slot knows its owner yet
    session.execute(text(
        'ALTER TABLE reserved_slots ALTER COLUMN source_id DROP NOT NULL'
    ))
    session.query(Reservation).filter_by(token=orphan_token).delete()
    session.query(ReservedSlot).update({ReservedSlot.source_id: None})
    session.flush()

    backfill_reserved_slot_source_ids(session)
    session.expire_all()

    remaining = session.query(ReservedSlot).all()
    remaining_keys = {(s.resource, s.start) for s in remaining}

    # the orphan slot is deleted ...
    assert remaining_keys.isdisjoint(orphan_keys)
    # ... and every other slot recovered its exact owner
    assert remaining_keys == set(expected) - orphan_keys
    for s in remaining:
        assert s.source_id is not None
        assert s.source_id == expected[(s.resource, s.start)]
