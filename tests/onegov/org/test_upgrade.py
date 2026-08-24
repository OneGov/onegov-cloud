from __future__ import annotations

import transaction

from datetime import datetime
from decimal import Decimal
from freezegun import freeze_time
from onegov.core.utils import Bunch
from onegov.org.upgrade import refresh_zeroed_reservation_invoices
from onegov.reservation import ResourceCollection
from onegov.ticket import TicketCollection

from typing import cast, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.upgrade import UpgradeContext
    from onegov.org.models.ticket import ReservationHandler
    from tests.onegov.org.conftest import Client


@freeze_time('2017-07-09', tick=True)
def test_refresh_zeroed_reservation_invoices(client: Client) -> None:
    """ A reservation invoice whose line was zeroed (before the price data was
    corrected) is recomputed by the upgrade, restoring the price and the
    payment.
    """
    resources = ResourceCollection(client.app.libres_context)

    transaction.begin()
    resource = resources.add(
        'Parktower Panorama 24', 'Europe/Zurich', type='room')
    resource.pricing_method = 'per_item'
    resource.price_per_item = 200.00
    resource.payment_method = 'manual'
    resource.currency = 'CHF'
    scheduler = resource.get_scheduler(client.app.libres_context)
    allocations = scheduler.allocate(
        dates=(datetime(2017, 7, 9), datetime(2017, 7, 9)),
        whole_day=True,
        quota=4,
    )
    reserve = client.bound_reserve(allocations[0])
    transaction.commit()

    reserve(quota=1, whole_day=True)
    page = client.get('/resource/parktower-panorama-24/form')
    page.form['email'] = 'info@example.org'
    ticket_page = page.form.submit().follow().form.submit().follow()
    assert 'RSV-' in ticket_page.text

    client.login_editor()
    invoice = (
        client.get('/tickets/ALL/open')
        .click('Annehmen').follow()
        .click('Rechnung anzeigen')
    )
    assert '200.00' in invoice

    # already-zeroed state: line at 0, payment dropped, price data still 200
    transaction.begin()
    session = client.app.session()
    ticket = TicketCollection(session).query().filter_by(
        handler_code='RSV').one()
    handler = cast('ReservationHandler', ticket.handler)
    payment = handler.payment
    assert ticket.invoice is not None
    for item in ticket.invoice.items:
        if item.group == 'reservation':
            item.unit = Decimal('0')
        item.payments = []
    if payment is not None:
        for reservation in handler.reservations:
            reservation.payment = None
        ticket.payment = None
        ticket.payment_id = None
        session.delete(payment)
    session.flush()
    ticket_id = ticket.id
    transaction.commit()

    # sanity: the invoice is collapsed and has no payment
    session = client.app.session()
    ticket = TicketCollection(session).query().filter_by(id=ticket_id).one()
    assert ticket.invoice is not None
    assert ticket.invoice.total_amount == Decimal('0')
    assert ticket.handler.payment is None

    # run the upgrade task
    context = Bunch(
        has_table=lambda table: True,
        session=session,
        app=Bunch(org=Bunch(price_rounding=None)),
        request=Bunch(session=session, translate=lambda text: text),
    )
    refresh_zeroed_reservation_invoices(cast('UpgradeContext', context))
    transaction.commit()

    # the reservation line and the payment are restored
    session = client.app.session()
    ticket = TicketCollection(session).query().filter_by(id=ticket_id).one()
    assert ticket.invoice is not None
    reservation_items = [
        item for item in ticket.invoice.items if item.group == 'reservation'
    ]
    assert reservation_items
    assert all(item.unit == Decimal('200') for item in reservation_items)
    assert ticket.invoice.total_amount == Decimal('200')
    assert ticket.handler.payment is not None
    assert ticket.handler.payment.amount == Decimal('200')
