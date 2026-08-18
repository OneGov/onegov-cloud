from __future__ import annotations

import transaction

from datetime import datetime
from freezegun import freeze_time
from onegov.reservation import ResourceCollection

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
        ResourceCollection(client.app.libres_context)  # type: ignore[union-attr]
        .by_name('tageskarte')
        .get_scheduler(client.app.libres_context)
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
