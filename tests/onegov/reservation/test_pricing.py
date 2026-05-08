from __future__ import annotations

from datetime import datetime
from onegov.reservation import Reservation, ResourceCollection


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from libres.context.core import Context


def test_per_hour_pricing(libres_context: Context) -> None:
    collection = ResourceCollection(libres_context)

    resource = collection.add('Executive Lounge', 'Europe/Zurich')
    resource.currency = 'CHF'
    resource.pricing_method = 'per_hour'
    resource.price_per_hour = 10

    scheduler = resource.get_scheduler(libres_context)
    dates = (datetime(2017, 6, 7, 12), datetime(2017, 6, 7, 18))
    scheduler.allocate(dates)

    token = scheduler.reserve('info@example.org', dates)
    reservation = scheduler.reservations_by_token(token).one()
    assert isinstance(reservation, Reservation)
    price = reservation.price()
    assert price is not None
    assert price.amount == 60
    assert price.currency == 'CHF'
    price = reservation.price(resource)
    assert price is not None
    assert price.amount == 60
    assert price.currency == 'CHF'


def test_multiple_allocations(libres_context: Context) -> None:
    collection = ResourceCollection(libres_context)

    resource = collection.add('Executive Lounge', 'Europe/Zurich')
    resource.currency = 'CHF'
    resource.pricing_method = 'per_hour'
    resource.price_per_hour = 10

    scheduler = resource.get_scheduler(libres_context)
    dates = (
        (datetime(2017, 6, 7, 12), datetime(2017, 6, 7, 18)),
        (datetime(2017, 6, 8, 12), datetime(2017, 6, 8, 18)),
    )
    scheduler.allocate(dates)

    token = scheduler.reserve('info@example.org', dates)
    reservations = scheduler.reservations_by_token(token).all()

    assert isinstance(reservations[0], Reservation)
    price = reservations[0].price()
    assert price is not None
    assert price.amount == 60
    assert price.currency == 'CHF'
    assert isinstance(reservations[1], Reservation)
    price = reservations[1].price()
    assert price is not None
    assert price.amount == 60
    assert price.currency == 'CHF'
    price = reservations[0].price(resource)
    assert price is not None
    assert price.amount == 60
    assert price.currency == 'CHF'
    price = reservations[1].price(resource)
    assert price is not None
    assert price.amount == 60
    assert price.currency == 'CHF'


def test_per_reservation_pricing(libres_context: Context) -> None:
    collection = ResourceCollection(libres_context)

    resource = collection.add('Executive Lounge', 'Europe/Zurich')
    resource.currency = 'CHF'
    resource.pricing_method = 'per_item'
    resource.price_per_item = 10

    scheduler = resource.get_scheduler(libres_context)
    dates = (datetime(2017, 6, 7, 12), datetime(2017, 6, 7, 18))
    scheduler.allocate(dates, quota=2)

    token = scheduler.reserve('info@example.org', dates, quota=2)
    reservation = scheduler.reservations_by_token(token).one()
    assert isinstance(reservation, Reservation)
    price = reservation.price()
    assert price is not None
    assert price.amount == 20
    assert price.currency == 'CHF'
    price = reservation.price(resource)
    assert price is not None
    assert price.amount == 20
    assert price.currency == 'CHF'
