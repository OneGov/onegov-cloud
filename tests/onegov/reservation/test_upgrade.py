from __future__ import annotations

from datetime import datetime
from libres.db.models import Reservation, ReservedSlot
from onegov.core.utils import Bunch
from onegov.reservation import ResourceCollection
from onegov.reservation.upgrade import backfill_reserved_slot_source_ids
from onegov.reservation.upgrade import (
    store_pricing_settings_on_reservations_fixed)
from sqlalchemy import text
from sqlalchemy.orm.attributes import flag_modified
from uuid import uuid4, UUID


from typing import Any, cast, TYPE_CHECKING
if TYPE_CHECKING:
    from libres.context.core import Context
    from onegov.core.upgrade import UpgradeContext


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


def test_store_pricing_settings_permutations(
    libres_context: Context,
) -> None:
    """ Full matrix (OGC-3406): 3 resources (per_item, per_hour, free) x 4
    allocation settings (per_item, per_hour, free, inherit). The allocation
    wins when it defines pricing; otherwise the resource content does. A
    reservation resolving to `free` is left untouched (``None`` here). A single
    migration run must land every one of the 12 reservations correctly.
    """
    collection = ResourceCollection(libres_context)

    # (resource_method, price_item, price_hour)
    resources = {
        'per_item': (200.0, 0.0),
        'per_hour': (0.0, 80.0),
        'free': (0.0, 0.0),
    }
    # allocation settings keyed by name; {} means inherit from the resource
    allocs: dict[str, dict[str, Any]] = {
        'per_item': {'pricing_method': 'per_item',
                     'price_per_item': 50.0, 'price_per_hour': 0.0},
        'per_hour': {'pricing_method': 'per_hour',
                     'price_per_hour': 30.0, 'price_per_item': 0.0},
        'free': {'pricing_method': 'free'},
        'inherit': {},
    }

    def expected(res_method: str, res_ppi: float, res_pph: float,
                 alloc: str) -> dict[str, object] | None:
        # the allocation wins when it defines pricing
        if alloc == 'per_item':
            return {'method': 'per_item', 'ppi': 50.0, 'pph': 0.0}
        if alloc == 'per_hour':
            return {'method': 'per_hour', 'ppi': 0.0, 'pph': 30.0}
        if alloc == 'free':
            return None  # free -> left untouched
        # inherit: fall back to the resource content
        if res_method == 'per_item':
            return {'method': 'per_item', 'ppi': res_ppi, 'pph': res_pph}
        if res_method == 'per_hour':
            return {'method': 'per_hour', 'ppi': res_ppi, 'pph': res_pph}
        return None  # free resource -> left untouched

    session = None
    tokens: dict[tuple[str, str], UUID] = {}
    hour = 6
    for res_method, (ppi, pph) in resources.items():
        resource = collection.add(f'Room {res_method}', 'Europe/Zurich')
        resource.pricing_method = res_method
        resource.price_per_item = ppi
        resource.price_per_hour = pph
        resource.currency = 'CHF'
        scheduler = resource.get_scheduler(libres_context)
        session = scheduler.session

        for alloc_name, alloc_data in allocs.items():
            start = datetime(2015, 8, 5, hour)
            end = datetime(2015, 8, 5, hour + 1)
            hour += 1
            allocation = scheduler.allocate(
                (start, end), partly_available=False)[0]
            allocation.data = alloc_data
            flag_modified(allocation, 'data')
            token = scheduler.reserve('info@example.org', (start, end))
            scheduler.approve_reservations(token)
            tokens[(res_method, alloc_name)] = token

    assert session is not None
    session.flush()

    # legacy state: no pricing stored on any reservation yet
    for reservation in session.query(Reservation):
        reservation.data = None
        flag_modified(reservation, 'data')
    session.flush()

    context = Bunch(has_table=lambda table: True, session=session)
    store_pricing_settings_on_reservations_fixed(
        cast('UpgradeContext', context))
    session.expire_all()

    for (res_method, alloc_name), token in tokens.items():
        ppi, pph = resources[res_method]
        exp = expected(res_method, ppi, pph, alloc_name)
        data = session.query(Reservation).filter_by(token=token).one().data
        if exp is None:
            # free -> untouched: no pricing written (legacy None reads as {})
            assert not data, (res_method, alloc_name, data)
        else:
            assert data is not None, (res_method, alloc_name)
            assert data['pricing_method'] == exp['method']
            assert data['price_per_item'] == exp['ppi']
            assert data['price_per_hour'] == exp['pph']


def test_store_pricing_settings_leaves_free_untouched(
    libres_context: Context,
) -> None:
    """ Free reservations are never touched: their price is never applied
    (invoice_item returns None for 'free'), so the migration must not churn
    them, even when a stale non-zero price sits in the data (OGC-3406).
    """
    collection = ResourceCollection(libres_context)
    resource = collection.add('Room', 'Europe/Zurich')
    resource.pricing_method = 'free'
    resource.price_per_item = 45.0  # stale price on a free resource
    resource.currency = 'CHF'

    scheduler = resource.get_scheduler(libres_context)
    session = scheduler.session
    scheduler.allocate(
        (datetime(2015, 8, 5, 8), datetime(2015, 8, 5, 10)),
        partly_available=False,
    )
    token = scheduler.reserve(
        'info@example.org', (datetime(2015, 8, 5, 8), datetime(2015, 8, 5, 10))
    )
    scheduler.approve_reservations(token)

    # a free reservation carrying a stale non-zero price
    reservation = session.query(Reservation).filter_by(token=token).one()
    stale = {'pricing_method': 'free', 'price_per_item': 45.0,
             'price_per_hour': 0.0}
    reservation.data = dict(stale)
    flag_modified(reservation, 'data')
    session.flush()

    context = Bunch(has_table=lambda table: True, session=session)
    store_pricing_settings_on_reservations_fixed(
        cast('UpgradeContext', context))
    session.expire_all()

    # left exactly as-is, not zeroed or rewritten
    reservation = session.query(Reservation).filter_by(token=token).one()
    assert reservation.data == stale
