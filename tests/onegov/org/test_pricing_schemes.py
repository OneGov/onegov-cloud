from __future__ import annotations

import transaction

from datetime import datetime
from freezegun import freeze_time
from onegov.reservation import Reservation, ResourceCollection
from sqlalchemy.orm.attributes import flag_modified

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from tests.onegov.org.conftest import Client



@freeze_time('2015-08-28', tick=True)
def test_stadtschulen_zug(client: Client) -> None:
    client.app.configure_resource_pricing_schemes(resource_pricing_schemes={
        client.app.application_id: ['stadtschulen_zug']
    })
    assert len(client.app.resource_pricing_schemes) == 1
    assert client.app.resource_pricing_schemes[0].name == 'stadtschulen_zug'
    client.login_admin()

    page = client.get('/resource/tageskarte/edit')
    page.select_radio('payment_method', 'Keine Kreditkarten-Zahlungen')
    page.select_radio('pricing_method', 'Vordefiniertes Preisschema')
    page.select_radio('pricing_scheme', 'Freizeitbetreuungsanlagen')
    page.select_radio('extras_pricing_method', 'Pro Eintrag')
    page.select_radio('discount_method', 'Nur den Preis pro Eintrag/Stunde')
    page.form['currency'] = 'CHF'
    # missing definition and empty table are errors
    page = page.form.submit()
    assert 'Mit Preisschema "Freizeitbetreuungsanlagen" braucht' in page
    assert 'Dieses Feld wird benötigt' in page

    # a partially complete table is still missing, correct field
    # but invalid options is an error as well
    page.form['definition'] = '\n'.join((
        'Kategorie =',
        '    (x) Nonsense',
        '    ( ) Nope',
        '    ( ) C - Even with this one the rest is invalid',
    ))
    page.form['stadtschulen_zug_price_table-0-0'] = 20
    page.form['stadtschulen_zug_price_table-0-1'] = 100
    page.form['stadtschulen_zug_price_table-0-2'] = 150
    page.form['stadtschulen_zug_price_table-1-0'] = 10
    page.form['stadtschulen_zug_price_table-1-1'] = 10
    page.form['stadtschulen_zug_price_table-1-2'] = 20
    page.form['stadtschulen_zug_price_table-2-0'] = 50
    page.form['stadtschulen_zug_price_table-2-1'] = 200
    page = page.form.submit()
    assert 'Mit Preisschema "Freizeitbetreuungsanlagen" braucht' in page
    assert 'Dieses Feld wird benötigt' in page

    # a correct definition that is non-required is also invalid
    page.form['definition'] = '\n'.join((
        'Kategorie =',
        '    (x) A - Stadtzuger Vereine / Gemeinnützige Organisationen',
        '    ( ) B - Andere Organisationen / Personen (Sitz in der Stadt Zug)',
        '    ( ) C - Auswärtige Organisationen / Personen',
    ))
    page.form['stadtschulen_zug_price_table-2-2'] = 300
    page = page.form.submit()
    assert '(Bitte "Kategorie * =" verwenden)' in page
    assert 'Dieses Feld wird benötigt' not in page

    page.form['definition'] = '\n'.join((
        'Kategorie * =',
        '    (x) A - Stadtzuger Vereine / Gemeinnützige Organisationen',
        '    ( ) B - Andere Organisationen / Personen (Sitz in der Stadt Zug)',
        '    ( ) C - Auswärtige Organisationen / Personen',
    ))
    page.form['stadtschulen_zug_price_table-2-2'] = 300
    page.form.submit().follow()

    transaction.begin()

    scheduler = (
        ResourceCollection(client.app.libres_context)
        .by_name('tageskarte')
        .get_scheduler(client.app.libres_context)  # type: ignore[union-attr]
    )

    allocations = scheduler.allocate(
        dates=(datetime(2015, 8, 28, 8), datetime(2015, 8, 28, 20)),
        whole_day=False,
        partly_available=True,
    )
    reserve = client.bound_reserve(allocations[0])

    transaction.commit()

    # create a reservation
    assert reserve('8:00', '12:30').json == {'success': True}

    # initially there should be no price
    page = client.get('/resource/tageskarte/form')
    assert '.00 CHF' not in page

    # after selecting the category we get a price
    page.form['email'] = 'john.doe@example.com'
    page.select_radio(
        'kategorie',
        'A - Stadtzuger Vereine / Gemeinnützige Organisationen'
    )
    assert '25.00 CHF' in page.form.submit().follow()
    page.select_radio(
        'kategorie',
        'B - Andere Organisationen / Personen (Sitz in der Stadt Zug)'
    )
    assert '105.00 CHF' in page.form.submit().follow()
    page.select_radio(
        'kategorie',
        'C - Auswärtige Organisationen / Personen'
    )
    assert '160.00 CHF' in page.form.submit().follow()
    page.form.submit().follow().form.submit()

    # open ticket
    ticket = client.get('/tickets/ALL/open').click('Annehmen').follow()
    assert '160.00' in ticket

    # changing the submission details updates the price as expected
    edit_page = ticket.click('Details bearbeiten')
    edit_page.select_radio(
        'kategorie',
        'B - Andere Organisationen / Personen (Sitz in der Stadt Zug)'
    )
    ticket = edit_page.form.submit().follow()
    assert '105.00' in ticket



@freeze_time('2017-07-09', tick=True)
def test_parktower_panorama_24_surcharge_zeroes_positions(
    client: Client,
) -> None:
    """ OGC-3406: adding a Zuschlag/Abzug zeroes all reservation positions.

    Cause: a per_item resource with the price on the allocations. Imported
    reservations carry ``price_per_item = 0.0`` in their data, so
    ``custom_reservation.invoice_item`` recomputes their line from that 0.0.
    Any ``refresh_invoice_items`` (adding a Zuschlag/Abzug triggers one) then
    wipes the reservation lines to 0 and drops the payment.
    """
    resources = ResourceCollection(client.app.libres_context)

    transaction.begin()
    resource = resources.add(
        'Parktower Panorama 24',
        'Europe/Zurich',
        type='room',
    )
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
    ticket = page.form.submit().follow().form.submit().follow()
    assert 'RSV-' in ticket.text

    client.login_editor()
    page = client.get('/tickets/ALL/open').click('Annehmen').follow()

    invoice = page.click('Rechnung anzeigen')
    assert '200.00' in invoice   # reservation priced correctly

    # simulate the imported/legacy reservation: stored price_per_item = 0.0
    transaction.begin()
    session = client.app.session()
    for reservation in session.query(Reservation):
        reservation.data = {
            'currency': 'CHF',
            'cost_object': None,
            'price_per_hour': 0.0,
            'price_per_item': 0.0,
            'pricing_method': 'per_item',
        }
        flag_modified(reservation, 'data')
    transaction.commit()

    # adding a Zuschlag triggers refresh_invoice_items; the 0.0 stored price
    # falls back to the allocation then resource
    invoice = client.get(invoice.request.url)
    item = invoice.click('Abzug / Zuschlag')
    item.form['booking_text'] = 'Zuschlag'
    item.select_radio('kind', 'Zuschlag')
    item.form['surcharge'] = '50.00'
    invoice = item.form.submit().follow()

    # the fallback keeps the real price; the position must not be wiped to 0
    reservation_row = invoice.pyquery(
        'tr:contains("Parktower Panorama 24")'
    ).text()
    assert '200.00' in reservation_row
