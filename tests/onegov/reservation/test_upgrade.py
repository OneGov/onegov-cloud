from __future__ import annotations

from datetime import datetime
from libres.db.models import Allocation, Reservation, ReservedSlot
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
            return {'method': 'free', 'ppi': 0.0, 'pph': 0.0}
        # inherit: fall back to the resource content
        if res_method == 'per_item':
            return {'method': 'per_item', 'ppi': res_ppi, 'pph': res_pph}
        if res_method == 'per_hour':
            return {'method': 'per_hour', 'ppi': res_ppi, 'pph': res_pph}
        return {'method': 'free', 'ppi': 0.0, 'pph': 0.0}  # free resource

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
        assert exp is not None
        assert data is not None, (res_method, alloc_name)
        assert data['pricing_method'] == exp['method']
        assert data['price_per_item'] == exp['ppi']
        assert data['price_per_hour'] == exp['pph']


def test_store_pricing_settings_quota_mirrors(
    libres_context: Context,
) -> None:
    """ With quota > 1, reserving beyond the master persists mirror
    allocations (resource != mirror_of) that copy the master's pricing data.
    The migration's `resource = mirror_of` guard must read only the master, so
    every reservation in the group still lands the allocation price (OGC-3406).
    """
    collection = ResourceCollection(libres_context)
    resource = collection.add('Room', 'Europe/Zurich')
    resource.pricing_method = 'free'  # allocation overrides to per_item
    resource.currency = 'CHF'

    scheduler = resource.get_scheduler(libres_context)
    session = scheduler.session
    allocation = scheduler.allocate(
        (datetime(2015, 8, 5, 8), datetime(2015, 8, 5, 10)),
        partly_available=False,
        quota=2,
    )[0]
    allocation.data = {'pricing_method': 'per_item', 'price_per_item': 50.0,
                       'price_per_hour': 0.0, 'currency': 'CHF'}
    flag_modified(allocation, 'data')

    # two reservations: the second consumes a mirror slot
    tokens = []
    for _ in range(2):
        token = scheduler.reserve(
            'info@example.org',
            (datetime(2015, 8, 5, 8), datetime(2015, 8, 5, 10)),
        )
        scheduler.approve_reservations(token)
        tokens.append(token)
    session.flush()

    # a mirror allocation (resource != mirror_of) now exists for the group
    mirrors = session.query(Allocation).filter(
        Allocation.resource != Allocation.mirror_of).count()
    assert mirrors >= 1

    # legacy state: no pricing stored yet
    for reservation in session.query(Reservation):
        reservation.data = None
        flag_modified(reservation, 'data')
    session.flush()

    context = Bunch(has_table=lambda table: True, session=session)
    store_pricing_settings_on_reservations_fixed(
        cast('UpgradeContext', context))
    session.expire_all()

    for token in tokens:
        data = session.query(Reservation).filter_by(token=token).one().data
        assert data is not None
        assert data['pricing_method'] == 'per_item'
        assert data['price_per_item'] == 50.0


def test_store_pricing_settings_stores_free(
    libres_context: Context,
) -> None:
    """ Free reservations must record that they are free, so a later change to
    the resource/allocation can't make them carry a cost via the fallback: the
    stored `free` method is the guard, regardless of any price (OGC-3406).
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
    reservation.data = {'pricing_method': 'free', 'price_per_item': 45.0,
                        'price_per_hour': 0.0}
    flag_modified(reservation, 'data')
    session.flush()

    context = Bunch(has_table=lambda table: True, session=session)
    store_pricing_settings_on_reservations_fixed(
        cast('UpgradeContext', context))
    session.expire_all()

    reservation = session.query(Reservation).filter_by(token=token).one()
    assert reservation.data is not None
    assert reservation.data['pricing_method'] == 'free'
