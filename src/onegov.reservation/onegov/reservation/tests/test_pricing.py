from datetime import datetime
from onegov.reservation import ResourceCollection


def test_per_hour_pricing(libres_context):
    collection = ResourceCollection(libres_context)

    resource = collection.add('Executive Lounge', 'Europe/Zurich')
    scheduler = resource.get_scheduler(libres_context)
    dates = (datetime(2017, 6, 7, 12), datetime(2017, 6, 7, 18))

    scheduler.allocate(dates, data={
        'currency': 'CHF',
        'pricing_method': 'per_hour',
        'price_per_hour': 10
    })

    token = scheduler.reserve('info@example.org', dates)
    reservation = scheduler.reservations_by_token(token).one()

    assert reservation.price.amount == 60
    assert reservation.price.currency == 'CHF'


def test_multiple_allocations(libres_context):
    collection = ResourceCollection(libres_context)

    resource = collection.add('Executive Lounge', 'Europe/Zurich')
    scheduler = resource.get_scheduler(libres_context)
    dates = (
        (datetime(2017, 6, 7, 12), datetime(2017, 6, 7, 18)),
        (datetime(2017, 6, 8, 12), datetime(2017, 6, 8, 18)),
    )

    scheduler.allocate(dates, data={
        'currency': 'CHF',
        'pricing_method': 'per_hour',
        'price_per_hour': 10
    })

    token = scheduler.reserve('info@example.org', dates)
    reservations = scheduler.reservations_by_token(token).all()

    assert reservations[0].price.amount == 60
    assert reservations[0].price.currency == 'CHF'
    assert reservations[1].price.amount == 60
    assert reservations[1].price.currency == 'CHF'


def test_per_reservation_pricing(libres_context):
    collection = ResourceCollection(libres_context)

    resource = collection.add('Executive Lounge', 'Europe/Zurich')
    scheduler = resource.get_scheduler(libres_context)
    dates = (datetime(2017, 6, 7, 12), datetime(2017, 6, 7, 18))

    scheduler.allocate(dates, quota=2, data={
        'currency': 'CHF',
        'pricing_method': 'per_reservation',
        'price_per_reservation': 10
    })

    token = scheduler.reserve('info@example.org', dates, quota=2)
    reservation = scheduler.reservations_by_token(token).one()

    assert reservation.price.amount == 20
    assert reservation.price.currency == 'CHF'
