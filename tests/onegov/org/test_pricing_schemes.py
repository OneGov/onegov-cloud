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



@freeze_time('2026-09-04', tick=True)
def test_horw_horwerhalle(client: Client) -> None:
    client.app.configure_resource_pricing_schemes(resource_pricing_schemes={
        client.app.application_id: ['horw_horwerhalle']
    })
    assert len(client.app.resource_pricing_schemes) == 1
    assert client.app.resource_pricing_schemes[0].name == 'horw_horwerhalle'
    client.login_admin()

    page = client.get('/resource/tageskarte/edit')
    page.select_radio('payment_method', 'Keine Kreditkarten-Zahlungen')
    page.select_radio('pricing_method', 'Vordefiniertes Preisschema')
    page.select_radio('pricing_scheme', 'Horwerhalle')
    page.select_radio('extras_pricing_method', 'Pro Eintrag')
    page.select_radio('discount_method', 'Nur den Preis pro Eintrag/Stunde')
    page.form['currency'] = 'CHF'
    # missing definition and empty table are errors
    page = page.form.submit()
    assert 'Mit Preisschema "Horwerhalle" braucht' in page
    assert 'Dieses Feld wird benötigt' in page

    # a partially complete table is still missing, correct field
    # but missing required option is an error as well
    page.form['definition'] = '\n'.join((
        'Horwer Non-Profit Organisation =',
        '    ( ) Ya',
        '    (x) Nein',
        'Mit Wirtschaft =',
        '    ( ) Ya',
        '    (x) Nein',
    ))
    page.form['horw_horwerhalle_price_table-0-0'] = 50
    page.form['horw_horwerhalle_price_table-0-1'] = 120
    page.form['horw_horwerhalle_price_table-0-2'] = 200
    page.form['horw_horwerhalle_price_table-1-0'] = 600
    page.form['horw_horwerhalle_price_table-1-1'] = 600
    page.form['horw_horwerhalle_price_table-1-2'] = 1200
    page.form['horw_horwerhalle_price_table-2-0'] = 200
    page.form['horw_horwerhalle_price_table-2-1'] = 400
    page.form['horw_horwerhalle_price_table-2-2'] = 800
    page.form['horw_horwerhalle_price_table-3-0'] = 800
    page.form['horw_horwerhalle_price_table-3-1'] = 800
    page = page.form.submit()
    assert 'Mit Preisschema "Horwerhalle" braucht' in page
    assert 'Dieses Feld wird benötigt' in page

    # a correct definition that is non-required is also invalid
    page.form['definition'] = '\n'.join((
        'Horwer Non-Profit Organisation =',
        '    ( ) Ja',
        '    (x) Nein',
        'Mit Wirtschaft =',
        '    ( ) Ja',
        '    (x) Nein',
    ))
    page.form['horw_horwerhalle_price_table-3-2'] = 1600
    page = page.form.submit()
    assert 'nicht optional sein' in page
    assert 'Dieses Feld wird benötigt' not in page

    page.form['definition'] = '\n'.join((
        'Horwer Non-Profit Organisation * =',
        '    ( ) Ja',
        '    (x) Nein',
        'Mit Wirtschaft =',
        '    ( ) Ja',
        '    (x) Nein',
    ))
    page.form.submit().follow()

    transaction.begin()

    scheduler = (
        ResourceCollection(client.app.libres_context)
        .by_name('tageskarte')
        .get_scheduler(client.app.libres_context)  # type: ignore[union-attr]
    )

    allocations = scheduler.allocate(
        dates=[
            # friday
            (datetime(2026, 9, 4, 8), datetime(2026, 9, 4, 20)),
            # satuday
            (datetime(2026, 9, 5, 8), datetime(2026, 9, 5, 20)),
        ],
        whole_day=False,
        partly_available=True,
    )
    reserve1 = client.bound_reserve(allocations[0])
    reserve2 = client.bound_reserve(allocations[1])

    transaction.commit()

    # create a reservation
    assert reserve1('8:00', '12:30').json == {'success': True}

    # initially there should be no price
    page = client.get('/resource/tageskarte/form')
    assert '.00 CHF' not in page

    # with this selection we still get no price on a friday
    page.form['email'] = 'john.doe@example.com'
    page.select_radio(
        'horwer_non_profit_organisation',
        'Ja'
    )
    page.select_radio(
        'mit_wirtschaft',
        'Nein'
    )
    assert '.00 CHF' not in page.form.submit().follow()
    page.select_radio(
        'horwer_non_profit_organisation',
        'Ja'
    )
    page.select_radio(
        'mit_wirtschaft',
        'Ja'
    )
    assert '600.00 CHF' in page.form.submit().follow()
    page.select_radio(
        'horwer_non_profit_organisation',
        'Nein'
    )
    page.select_radio(
        'mit_wirtschaft',
        'Nein'
    )
    assert '400.00 CHF' in page.form.submit().follow()
    page.select_radio(
        'horwer_non_profit_organisation',
        'Nein'
    )
    page.select_radio(
        'mit_wirtschaft',
        'Ja'
    )
    assert '800.00 CHF' in page.form.submit().follow()
    page.form.submit().follow().form.submit()

    # open ticket
    ticket = client.get('/tickets/ALL/open').click('Annehmen').follow()
    assert '800.00' in ticket

    # changing the submission details updates the price as expected
    edit_page = ticket.click('Details bearbeiten')
    edit_page.select_radio(
        'mit_wirtschaft',
        'Nein'
    )
    ticket = edit_page.form.submit().follow()
    assert '400.00' in ticket

    # create a reservation
    assert reserve2('8:00', '9:30').json == {'success': True}

    # initially there should be no price
    page = client.get('/resource/tageskarte/form')
    assert '.00 CHF' not in page

    # on a saturday we do get a price with this selection
    page.form['email'] = 'john.doe@example.com'
    page.select_radio(
        'horwer_non_profit_organisation',
        'Ja'
    )
    page.select_radio(
        'mit_wirtschaft',
        'Nein'
    )
    assert '50.00 CHF' in page.form.submit().follow()
    page.select_radio(
        'horwer_non_profit_organisation',
        'Ja'
    )
    page.select_radio(
        'mit_wirtschaft',
        'Ja'
    )
    assert '600.00 CHF' in page.form.submit().follow()
    page.select_radio(
        'horwer_non_profit_organisation',
        'Nein'
    )
    page.select_radio(
        'mit_wirtschaft',
        'Nein'
    )
    assert '200.00 CHF' in page.form.submit().follow()
    page.select_radio(
        'horwer_non_profit_organisation',
        'Nein'
    )
    page.select_radio(
        'mit_wirtschaft',
        'Ja'
    )
    assert '800.00 CHF' in page.form.submit().follow()
    page.form.submit().follow().form.submit()


@freeze_time('2026-09-04', tick=True)
def test_horw_villa_kraemerstein(client: Client) -> None:
    client.app.configure_resource_pricing_schemes(resource_pricing_schemes={
        client.app.application_id: ['horw_villa_kraemerstein']
    })
    assert len(client.app.resource_pricing_schemes) == 1
    assert (
        client.app.resource_pricing_schemes[0].name
        == 'horw_villa_kraemerstein'
    )
    client.login_admin()

    # labels from Anhang 5 of the Gebührenverordnung
    saal = 'Gartensaal, Foyer und Terrasse'
    kueche = (
        'Gartensaal, Foyer, Terrasse, Lounge/Bar, '
        'Küche inkl. Geräte und Geschirr'
    )

    page = client.get('/resource/tageskarte/edit')
    page.select_radio('payment_method', 'Keine Kreditkarten-Zahlungen')
    page.select_radio('pricing_method', 'Vordefiniertes Preisschema')
    page.select_radio('pricing_scheme', 'Villa Krämerstein')
    page.select_radio('extras_pricing_method', 'Pro Eintrag')
    page.select_radio('discount_method', 'Nur den Preis pro Eintrag/Stunde')
    page.form['currency'] = 'CHF'
    # missing definition and empty table are errors
    page = page.form.submit()
    assert 'Mit Preisschema "Villa Krämerstein" braucht' in page
    assert 'Dieses Feld wird benötigt' in page

    # a partially complete table is still missing, correct field
    # but missing required option is an error as well
    page.form['definition'] = '\n'.join((
        'Horwer Organisation oder in Horw wohnhafte Privatperson =',
        '    ( ) Ya',
        '    (x) Nein',
        'Räumlichkeiten und Anlagen =',
        f'    (x) {saal}',
        f'    ( ) {kueche}',
    ))
    page.form['horw_villa_kraemerstein_price_table-0-0'] = 25
    page.form['horw_villa_kraemerstein_price_table-0-1'] = 45
    page.form['horw_villa_kraemerstein_price_table-0-2'] = 85
    page.form['horw_villa_kraemerstein_price_table-0-3'] = 35
    page.form['horw_villa_kraemerstein_price_table-0-4'] = 55
    page.form['horw_villa_kraemerstein_price_table-0-5'] = 95
    page.form['horw_villa_kraemerstein_price_table-1-0'] = 120
    page.form['horw_villa_kraemerstein_price_table-1-1'] = 140
    page.form['horw_villa_kraemerstein_price_table-1-2'] = 180
    page.form['horw_villa_kraemerstein_price_table-1-3'] = 130
    page.form['horw_villa_kraemerstein_price_table-1-4'] = 150
    page.form['horw_villa_kraemerstein_price_table-1-5'] = 190
    page.form['horw_villa_kraemerstein_price_table-2-0'] = 220
    page.form['horw_villa_kraemerstein_price_table-2-1'] = 240
    page.form['horw_villa_kraemerstein_price_table-2-2'] = 280
    page.form['horw_villa_kraemerstein_price_table-2-3'] = 230
    page.form['horw_villa_kraemerstein_price_table-2-4'] = 250
    page.form['horw_villa_kraemerstein_price_table-2-5'] = 290
    page.form['horw_villa_kraemerstein_price_table-3-0'] = 320
    page.form['horw_villa_kraemerstein_price_table-3-1'] = 340
    page.form['horw_villa_kraemerstein_price_table-3-2'] = 380
    page.form['horw_villa_kraemerstein_price_table-3-3'] = 330
    page.form['horw_villa_kraemerstein_price_table-3-4'] = 350
    page = page.form.submit()
    assert 'mit "Horwer Organisation" im Namen' in page
    assert 'Dieses Feld wird benötigt' in page

    # a correct definition that is non-required is also invalid
    page.form['definition'] = '\n'.join((
        'Horwer Organisation oder in Horw wohnhafte Privatperson =',
        '    ( ) Ja',
        '    (x) Nein',
        'Räumlichkeiten und Anlagen =',
        f'    (x) {saal}',
        f'    ( ) {kueche}',
    ))
    page.form['horw_villa_kraemerstein_price_table-3-5'] = 390
    page = page.form.submit()
    assert 'nicht optional sein' in page
    assert 'Dieses Feld wird benötigt' not in page

    # a missing "Anlagen" field is invalid
    page.form['definition'] = '\n'.join((
        'Horwer Organisation oder in Horw wohnhafte Privatperson * =',
        '    ( ) Ja',
        '    (x) Nein',
    ))
    page = page.form.submit()
    assert 'mit "Anlagen" im Namen' in page

    # an "Anlagen" field with more than two options is invalid
    page.form['definition'] = '\n'.join((
        'Horwer Organisation oder in Horw wohnhafte Privatperson * =',
        '    ( ) Ja',
        '    (x) Nein',
        'Räumlichkeiten und Anlagen =',
        f'    (x) {saal}',
        f'    ( ) {kueche}',
        '    ( ) Lounge/Bar',
    ))
    page = page.form.submit()
    assert 'mit "Anlagen" im Namen' in page

    # an "Anlagen" field without a "Küche" option is invalid
    page.form['definition'] = '\n'.join((
        'Horwer Organisation oder in Horw wohnhafte Privatperson * =',
        '    ( ) Ja',
        '    (x) Nein',
        'Räumlichkeiten und Anlagen =',
        f'    (x) {saal}',
        '    ( ) Lounge/Bar',
    ))
    page = page.form.submit()
    assert 'mit "Anlagen" im Namen' in page

    # an "Anlagen" field where both options contain "Küche" is invalid
    page.form['definition'] = '\n'.join((
        'Horwer Organisation oder in Horw wohnhafte Privatperson * =',
        '    ( ) Ja',
        '    (x) Nein',
        'Räumlichkeiten und Anlagen =',
        '    (x) Gartensaal, Foyer, Terrasse und Küche',
        f'    ( ) {kueche}',
    ))
    page = page.form.submit()
    assert 'mit "Anlagen" im Namen' in page

    page.form['definition'] = '\n'.join((
        'Horwer Organisation oder in Horw wohnhafte Privatperson * =',
        '    ( ) Ja',
        '    (x) Nein',
        'Räumlichkeiten und Anlagen =',
        f'    (x) {saal}',
        f'    ( ) {kueche}',
    ))
    page.form.submit().follow()

    transaction.begin()

    scheduler = (
        ResourceCollection(client.app.libres_context)
        .by_name('tageskarte')
        .get_scheduler(client.app.libres_context)  # type: ignore[union-attr]
    )

    allocations = scheduler.allocate(
        dates=[
            # friday
            (datetime(2026, 9, 4, 8), datetime(2026, 9, 4, 20)),
            # satuday
            (datetime(2026, 9, 5, 8), datetime(2026, 9, 5, 20)),
        ],
        whole_day=False,
        partly_available=True,
    )
    reserve1 = client.bound_reserve(allocations[0])
    reserve2 = client.bound_reserve(allocations[1])

    transaction.commit()

    # create a half day reservation on a friday
    assert reserve1('8:00', '12:30').json == {'success': True}

    # initially there should be no price
    page = client.get('/resource/tageskarte/form')
    assert '.00 CHF' not in page

    page.form['email'] = 'john.doe@example.com'
    page.select_radio(
        'horwer_organisation_oder_in_horw_wohnhafte_privatperson',
        'Ja'
    )
    page.select_radio(
        'raumlichkeiten_und_anlagen',
        saal
    )
    assert '45.00 CHF' in page.form.submit().follow()
    page.select_radio(
        'horwer_organisation_oder_in_horw_wohnhafte_privatperson',
        'Ja'
    )
    page.select_radio(
        'raumlichkeiten_und_anlagen',
        kueche
    )
    assert '140.00 CHF' in page.form.submit().follow()
    page.select_radio(
        'horwer_organisation_oder_in_horw_wohnhafte_privatperson',
        'Nein'
    )
    page.select_radio(
        'raumlichkeiten_und_anlagen',
        saal
    )
    assert '240.00 CHF' in page.form.submit().follow()
    page.select_radio(
        'horwer_organisation_oder_in_horw_wohnhafte_privatperson',
        'Nein'
    )
    page.select_radio(
        'raumlichkeiten_und_anlagen',
        kueche
    )
    assert '340.00 CHF' in page.form.submit().follow()
    page.form.submit().follow().form.submit()

    # open ticket
    ticket = client.get('/tickets/ALL/open').click('Annehmen').follow()
    assert '340.00' in ticket

    # changing the submission details updates the price as expected
    edit_page = ticket.click('Details bearbeiten')
    edit_page.select_radio('raumlichkeiten_und_anlagen', saal)
    ticket = edit_page.form.submit().follow()
    assert '240.00' in ticket

    # create a two hour reservation on a saturday
    assert reserve2('8:00', '9:30').json == {'success': True}

    # initially there should be no price
    page = client.get('/resource/tageskarte/form')
    assert '.00 CHF' not in page

    page.form['email'] = 'john.doe@example.com'
    page.select_radio(
        'horwer_organisation_oder_in_horw_wohnhafte_privatperson',
        'Ja'
    )
    page.select_radio(
        'raumlichkeiten_und_anlagen',
        saal
    )
    assert '35.00 CHF' in page.form.submit().follow()
    page.select_radio(
        'horwer_organisation_oder_in_horw_wohnhafte_privatperson',
        'Ja'
    )
    page.select_radio(
        'raumlichkeiten_und_anlagen',
        kueche
    )
    assert '130.00 CHF' in page.form.submit().follow()
    page.select_radio(
        'horwer_organisation_oder_in_horw_wohnhafte_privatperson',
        'Nein'
    )
    page.select_radio(
        'raumlichkeiten_und_anlagen',
        saal
    )
    assert '230.00 CHF' in page.form.submit().follow()
    page.select_radio(
        'horwer_organisation_oder_in_horw_wohnhafte_privatperson',
        'Nein'
    )
    page.select_radio(
        'raumlichkeiten_und_anlagen',
        kueche
    )
    assert '330.00 CHF' in page.form.submit().follow()
    page.form.submit().follow().form.submit()

    ticket = client.get('/tickets/ALL/open').click('Annehmen').follow()
    assert '330.00' in ticket

    # create a full day reservation on a saturday
    assert reserve2('10:00', '20:00').json == {'success': True}

    page = client.get('/resource/tageskarte/form')
    page.form['email'] = 'john.doe@example.com'
    page.select_radio(
        'horwer_organisation_oder_in_horw_wohnhafte_privatperson',
        'Ja'
    )
    page.select_radio(
        'raumlichkeiten_und_anlagen',
        saal
    )
    assert '95.00 CHF' in page.form.submit().follow()
    page.select_radio(
        'horwer_organisation_oder_in_horw_wohnhafte_privatperson',
        'Nein'
    )
    page.select_radio(
        'raumlichkeiten_und_anlagen',
        kueche
    )
    assert '390.00 CHF' in page.form.submit().follow()


@freeze_time('2026-09-04', tick=True)
def test_horw_aussensportanlagen(client: Client) -> None:
    client.app.configure_resource_pricing_schemes(resource_pricing_schemes={
        client.app.application_id: ['horw_aussensportanlagen']
    })
    assert len(client.app.resource_pricing_schemes) == 1
    assert (
        client.app.resource_pricing_schemes[0].name
        == 'horw_aussensportanlagen'
    )
    client.login_admin()

    page = client.get('/resource/tageskarte/edit')
    page.select_radio('payment_method', 'Keine Kreditkarten-Zahlungen')
    page.select_radio('pricing_method', 'Vordefiniertes Preisschema')
    page.select_radio(
        'pricing_scheme',
        'Rasenspielfeld / Allwetterplatz / Leichtathletikanlage'
    )
    page.select_radio('extras_pricing_method', 'Pro Eintrag')
    page.select_radio('discount_method', 'Nur den Preis pro Eintrag/Stunde')
    page.form['currency'] = 'CHF'
    # missing definition and empty table are errors
    page = page.form.submit()
    assert 'Mit Preisschema "Aussensportanlagen" braucht' in page
    assert 'Dieses Feld wird benötigt' in page

    # a partially complete table is still missing, correct field
    # but missing required option is an error as well
    page.form['definition'] = '\n'.join((
        'Horwer Non-Profit Organisation =',
        '    ( ) Ya',
        '    (x) Nein',
        'Mit Wirtschaft =',
        '    ( ) Ja',
        '    (x) Nein',
    ))
    page.form['horw_aussensportanlagen_price_table-0-0'] = 20
    page.form['horw_aussensportanlagen_price_table-0-1'] = 30
    page.form['horw_aussensportanlagen_price_table-0-2'] = 50
    page.form['horw_aussensportanlagen_price_table-1-0'] = 50
    page.form['horw_aussensportanlagen_price_table-1-1'] = 100
    page.form['horw_aussensportanlagen_price_table-1-2'] = 200
    page.form['horw_aussensportanlagen_price_table-2-0'] = 100
    page.form['horw_aussensportanlagen_price_table-2-1'] = 200
    page.form['horw_aussensportanlagen_price_table-2-2'] = 400
    page.form['horw_aussensportanlagen_price_table-3-0'] = 100
    page.form['horw_aussensportanlagen_price_table-3-1'] = 300
    page = page.form.submit()
    assert 'mit "Non-Profit" im Namen' in page
    assert 'Dieses Feld wird benötigt' in page

    # a correct definition that is non-required is also invalid
    page.form['definition'] = '\n'.join((
        'Horwer Non-Profit Organisation =',
        '    ( ) Ja',
        '    (x) Nein',
        'Mit Wirtschaft =',
        '    ( ) Ja',
        '    (x) Nein',
    ))
    page.form['horw_aussensportanlagen_price_table-3-2'] = 500
    page = page.form.submit()
    assert 'nicht optional sein' in page
    assert 'Dieses Feld wird benötigt' not in page

    # a wirtschaft field without a "Ja" option is invalid
    page.form['definition'] = '\n'.join((
        'Horwer Non-Profit Organisation * =',
        '    ( ) Ja',
        '    (x) Nein',
        'Mit Wirtschaft =',
        '    ( ) Ya',
        '    (x) Nein',
    ))
    page = page.form.submit()
    assert 'mit "Wirtschaft" im Namen' in page

    page.form['definition'] = '\n'.join((
        'Horwer Non-Profit Organisation * =',
        '    ( ) Ja',
        '    (x) Nein',
        'Mit Wirtschaft =',
        '    ( ) Ja',
        '    (x) Nein',
    ))
    page = page.form.submit()
    assert 'nicht optional sein' in page

    page.form['definition'] = '\n'.join((
        'Horwer Non-Profit Organisation * =',
        '    ( ) Ja',
        '    (x) Nein',
        'Mit Wirtschaft * =',
        '    ( ) Ja',
        '    (x) Nein',
    ))
    page.form.submit().follow()

    transaction.begin()

    scheduler = (
        ResourceCollection(client.app.libres_context)
        .by_name('tageskarte')
        .get_scheduler(client.app.libres_context)  # type: ignore[union-attr]
    )

    allocations = scheduler.allocate(
        dates=[
            # friday
            (datetime(2026, 9, 4, 8), datetime(2026, 9, 4, 20)),
            # satuday
            (datetime(2026, 9, 5, 8), datetime(2026, 9, 5, 20)),
            # sunday
            (datetime(2026, 9, 6, 8), datetime(2026, 9, 6, 20)),
        ],
        whole_day=False,
        partly_available=True,
    )
    reserve1 = client.bound_reserve(allocations[0])
    reserve2 = client.bound_reserve(allocations[1])
    reserve3 = client.bound_reserve(allocations[2])

    transaction.commit()

    # create a half day reservation on a friday
    assert reserve1('8:00', '12:30').json == {'success': True}

    # initially there should be no price
    page = client.get('/resource/tageskarte/form')
    assert '.00 CHF' not in page

    # with this selection we still get no price on a friday
    page.form['email'] = 'john.doe@example.com'
    page.select_radio(
        'horwer_non_profit_organisation',
        'Ja'
    )
    page.select_radio(
        'mit_wirtschaft',
        'Nein'
    )
    assert '.00 CHF' not in page.form.submit().follow()
    page.select_radio(
        'horwer_non_profit_organisation',
        'Ja'
    )
    page.select_radio(
        'mit_wirtschaft',
        'Ja'
    )
    assert '100.00 CHF' in page.form.submit().follow()
    page.select_radio(
        'horwer_non_profit_organisation',
        'Nein'
    )
    page.select_radio(
        'mit_wirtschaft',
        'Nein'
    )
    # on weekdays there's a discount
    assert '120.00 CHF' in page.form.submit().follow()
    page.select_radio(
        'horwer_non_profit_organisation',
        'Nein'
    )
    page.select_radio(
        'mit_wirtschaft',
        'Ja'
    )
    assert '300.00 CHF' in page.form.submit().follow()
    page.form.submit().follow().form.submit()

    # open ticket
    ticket = client.get('/tickets/ALL/open').click('Annehmen').follow()
    assert '300.00' in ticket

    # changing the submission details updates the price as expected
    edit_page = ticket.click('Details bearbeiten')
    edit_page.select_radio(
        'mit_wirtschaft',
        'Nein'
    )
    ticket = edit_page.form.submit().follow()
    assert '120.00' in ticket

    # create a two hour reservation on a saturday
    assert reserve2('8:00', '9:30').json == {'success': True}

    # initially there should be no price
    page = client.get('/resource/tageskarte/form')
    assert '.00 CHF' not in page

    # on a saturday we do get a price with this selection
    page.form['email'] = 'john.doe@example.com'
    page.select_radio(
        'horwer_non_profit_organisation',
        'Ja'
    )
    page.select_radio(
        'mit_wirtschaft',
        'Nein'
    )
    assert '20.00 CHF' in page.form.submit().follow()
    page.select_radio(
        'horwer_non_profit_organisation',
        'Ja'
    )
    page.select_radio(
        'mit_wirtschaft',
        'Ja'
    )
    assert '50.00 CHF' in page.form.submit().follow()
    page.select_radio(
        'horwer_non_profit_organisation',
        'Nein'
    )
    page.select_radio(
        'mit_wirtschaft',
        'Nein'
    )
    assert '100.00 CHF' in page.form.submit().follow()
    page.select_radio(
        'horwer_non_profit_organisation',
        'Nein'
    )
    page.select_radio(
        'mit_wirtschaft',
        'Ja'
    )
    assert '100.00 CHF' in page.form.submit().follow()
    page.form.submit().follow().form.submit()

    # open ticket
    ticket = client.get('/tickets/ALL/open').click('Annehmen').follow()
    assert '100.00' in ticket

    # changing the submission details updates the price as expected
    edit_page = ticket.click('Details bearbeiten')
    edit_page.select_radio(
        'horwer_non_profit_organisation',
        'Ja'
    )
    ticket = edit_page.form.submit().follow()
    assert '50.00' in ticket

    # create a full day reservation on a sunday
    assert reserve3('8:00', '20:00').json == {'success': True}

    page = client.get('/resource/tageskarte/form')
    page.form['email'] = 'john.doe@example.com'
    page.select_radio(
        'horwer_non_profit_organisation',
        'Ja'
    )
    page.select_radio(
        'mit_wirtschaft',
        'Nein'
    )
    assert '50.00 CHF' in page.form.submit().follow()
    page.select_radio(
        'horwer_non_profit_organisation',
        'Nein'
    )
    page.select_radio(
        'mit_wirtschaft',
        'Nein'
    )
    assert '400.00 CHF' in page.form.submit().follow()
    page.select_radio(
        'horwer_non_profit_organisation',
        'Nein'
    )
    page.select_radio(
        'mit_wirtschaft',
        'Ja'
    )
    assert '500.00 CHF' in page.form.submit().follow()


@freeze_time('2026-09-04', tick=True)
def test_horw_aula_zentrum(client: Client) -> None:
    client.app.configure_resource_pricing_schemes(resource_pricing_schemes={
        client.app.application_id: ['horw_aula_zentrum']
    })
    assert len(client.app.resource_pricing_schemes) == 1
    assert client.app.resource_pricing_schemes[0].name == 'horw_aula_zentrum'
    client.login_admin()

    page = client.get('/resource/tageskarte/edit')
    page.select_radio('payment_method', 'Keine Kreditkarten-Zahlungen')
    page.select_radio('pricing_method', 'Vordefiniertes Preisschema')
    page.select_radio('pricing_scheme', 'Aula Schulhaus Zentrum')
    page.select_radio('extras_pricing_method', 'Pro Eintrag')
    page.select_radio('discount_method', 'Nur den Preis pro Eintrag/Stunde')
    page.form['currency'] = 'CHF'
    # missing definition and empty table are errors
    page = page.form.submit()
    assert 'Mit Preisschema "Aula Schulhaus Zentrum" braucht' in page
    assert 'Dieses Feld wird benötigt' in page

    # a partially complete table is still missing, correct field
    # but missing required option is an error as well
    page.form['definition'] = '\n'.join((
        'Horwer Non-Profit Organisation =',
        '    ( ) Ya',
        '    (x) Nein',
        'Dauerbelegung * =',
        '    ( ) Ja',
        '    (x) Nein',
    ))
    page.form['horw_aula_zentrum_price_table-0-0'] = 260
    page.form['horw_aula_zentrum_price_table-0-1'] = 300
    page.form['horw_aula_zentrum_price_table-0-2'] = 360
    page.form['horw_aula_zentrum_price_table-1-0'] = 220
    page.form['horw_aula_zentrum_price_table-1-1'] = 250
    page.form['horw_aula_zentrum_price_table-1-2'] = 320
    page.form['horw_aula_zentrum_price_table-2-0'] = 270
    page.form['horw_aula_zentrum_price_table-2-1'] = 370
    page.form['horw_aula_zentrum_price_table-2-2'] = 570
    page.form['horw_aula_zentrum_price_table-3-0'] = 280
    page.form['horw_aula_zentrum_price_table-3-1'] = 380
    page = page.form.submit()
    assert 'mit "Non-Profit" im Namen' in page
    assert 'Dieses Feld wird benötigt' in page

    # a correct definition that is non-required is also invalid
    page.form['definition'] = '\n'.join((
        'Horwer Non-Profit Organisation =',
        '    ( ) Ja',
        '    (x) Nein',
        'Dauerbelegung * =',
        '    ( ) Ja',
        '    (x) Nein',
    ))
    page.form['horw_aula_zentrum_price_table-3-2'] = 580
    page = page.form.submit()
    assert '"Horwer Non-Profit Organisation" nicht optional sein' in page
    assert 'Dieses Feld wird benötigt' not in page

    # a missing dauerbelegung field is invalid
    page.form['definition'] = '\n'.join((
        'Horwer Non-Profit Organisation * =',
        '    ( ) Ja',
        '    (x) Nein',
    ))
    page = page.form.submit()
    assert 'mit "Dauerbelegung" im Namen' in page

    # a dauerbelegung field without a "Ja" option is invalid
    page.form['definition'] = '\n'.join((
        'Horwer Non-Profit Organisation * =',
        '    ( ) Ja',
        '    (x) Nein',
        'Dauerbelegung * =',
        '    ( ) Ya',
        '    (x) Nein',
    ))
    page = page.form.submit()
    assert 'mit "Dauerbelegung" im Namen' in page

    # a non-required dauerbelegung field is invalid
    page.form['definition'] = '\n'.join((
        'Horwer Non-Profit Organisation * =',
        '    ( ) Ja',
        '    (x) Nein',
        'Dauerbelegung =',
        '    ( ) Ja',
        '    (x) Nein',
    ))
    page = page.form.submit()
    assert '"Dauerbelegung" nicht optional sein' in page

    page.form['definition'] = '\n'.join((
        'Horwer Non-Profit Organisation * =',
        '    ( ) Ja',
        '    (x) Nein',
        'Dauerbelegung * =',
        '    ( ) Ja',
        '    (x) Nein',
    ))
    page.form.submit().follow()

    transaction.begin()

    scheduler = (
        ResourceCollection(client.app.libres_context)
        .by_name('tageskarte')
        .get_scheduler(client.app.libres_context)  # type: ignore[union-attr]
    )

    allocations = scheduler.allocate(
        dates=[
            # friday
            (datetime(2026, 9, 4, 8), datetime(2026, 9, 4, 20)),
            # satuday
            (datetime(2026, 9, 5, 8), datetime(2026, 9, 5, 20)),
            # sunday
            (datetime(2026, 9, 6, 8), datetime(2026, 9, 6, 20)),
        ],
        whole_day=False,
        partly_available=True,
    )
    reserve1 = client.bound_reserve(allocations[0])
    reserve2 = client.bound_reserve(allocations[1])
    reserve3 = client.bound_reserve(allocations[2])

    transaction.commit()

    # create a half day reservation on a friday
    assert reserve1('8:00', '12:30').json == {'success': True}

    # initially there should be no price
    page = client.get('/resource/tageskarte/form')
    assert '.00 CHF' not in page

    page.form['email'] = 'john.doe@example.com'
    page.select_radio(
        'horwer_non_profit_organisation',
        'Ja'
    )
    page.select_radio(
        'dauerbelegung',
        'Nein'
    )
    # on weekdays there's a discount
    assert '260.00 CHF' in page.form.submit().follow()
    page.select_radio(
        'horwer_non_profit_organisation',
        'Ja'
    )
    page.select_radio(
        'dauerbelegung',
        'Ja'
    )
    assert '250.00 CHF' in page.form.submit().follow()
    page.select_radio(
        'horwer_non_profit_organisation',
        'Nein'
    )
    page.select_radio(
        'dauerbelegung',
        'Nein'
    )
    assert '370.00 CHF' in page.form.submit().follow()
    page.select_radio(
        'horwer_non_profit_organisation',
        'Nein'
    )
    page.select_radio(
        'dauerbelegung',
        'Ja'
    )
    assert '380.00 CHF' in page.form.submit().follow()
    page.form.submit().follow().form.submit()

    # open ticket
    ticket = client.get('/tickets/ALL/open').click('Annehmen').follow()
    assert '380.00' in ticket

    # changing the submission details updates the price as expected
    edit_page = ticket.click('Details bearbeiten')
    edit_page.select_radio(
        'dauerbelegung',
        'Nein'
    )
    ticket = edit_page.form.submit().follow()
    assert '370.00' in ticket

    # create a two hour reservation on a saturday
    assert reserve2('8:00', '9:30').json == {'success': True}

    # initially there should be no price
    page = client.get('/resource/tageskarte/form')
    assert '.00 CHF' not in page

    page.form['email'] = 'john.doe@example.com'
    page.select_radio(
        'horwer_non_profit_organisation',
        'Ja'
    )
    page.select_radio(
        'dauerbelegung',
        'Nein'
    )
    assert '260.00 CHF' in page.form.submit().follow()
    page.select_radio(
        'horwer_non_profit_organisation',
        'Ja'
    )
    page.select_radio(
        'dauerbelegung',
        'Ja'
    )
    assert '220.00 CHF' in page.form.submit().follow()
    page.select_radio(
        'horwer_non_profit_organisation',
        'Nein'
    )
    page.select_radio(
        'dauerbelegung',
        'Nein'
    )
    assert '270.00 CHF' in page.form.submit().follow()
    page.select_radio(
        'horwer_non_profit_organisation',
        'Nein'
    )
    page.select_radio(
        'dauerbelegung',
        'Ja'
    )
    assert '280.00 CHF' in page.form.submit().follow()
    page.form.submit().follow().form.submit()

    # open ticket
    ticket = client.get('/tickets/ALL/open').click('Annehmen').follow()
    assert '280.00' in ticket

    # changing the submission details updates the price as expected
    edit_page = ticket.click('Details bearbeiten')
    edit_page.select_radio(
        'horwer_non_profit_organisation',
        'Ja'
    )
    ticket = edit_page.form.submit().follow()
    assert '220.00' in ticket

    # create a full day reservation on a sunday
    assert reserve3('8:00', '20:00').json == {'success': True}

    page = client.get('/resource/tageskarte/form')
    page.form['email'] = 'john.doe@example.com'
    page.select_radio(
        'horwer_non_profit_organisation',
        'Ja'
    )
    page.select_radio(
        'dauerbelegung',
        'Nein'
    )
    assert '360.00 CHF' in page.form.submit().follow()
    page.select_radio(
        'horwer_non_profit_organisation',
        'Ja'
    )
    page.select_radio(
        'dauerbelegung',
        'Ja'
    )
    assert '320.00 CHF' in page.form.submit().follow()
    page.select_radio(
        'horwer_non_profit_organisation',
        'Nein'
    )
    page.select_radio(
        'dauerbelegung',
        'Nein'
    )
    assert '570.00 CHF' in page.form.submit().follow()
    page.select_radio(
        'horwer_non_profit_organisation',
        'Nein'
    )
    page.select_radio(
        'dauerbelegung',
        'Ja'
    )
    assert '580.00 CHF' in page.form.submit().follow()


@freeze_time('2026-09-04', tick=True)
def test_horw_saal_egli(client: Client) -> None:
    client.app.configure_resource_pricing_schemes(resource_pricing_schemes={
        client.app.application_id: ['horw_saal_egli']
    })
    assert len(client.app.resource_pricing_schemes) == 1
    assert client.app.resource_pricing_schemes[0].name == 'horw_saal_egli'
    client.login_admin()

    page = client.get('/resource/tageskarte/edit')
    page.select_radio('payment_method', 'Keine Kreditkarten-Zahlungen')
    page.select_radio('pricing_method', 'Vordefiniertes Preisschema')
    page.select_radio('pricing_scheme', 'Saal Egli')
    page.select_radio('extras_pricing_method', 'Pro Eintrag')
    page.select_radio('discount_method', 'Nur den Preis pro Eintrag/Stunde')
    page.form['currency'] = 'CHF'
    # missing definition is an error
    page = page.form.submit()
    assert 'Mit Preisschema "Saal Egli" braucht es' in page
    assert '"Horwer Non-Profit-Organisationen (Vereine)"' in page

    # a category field with the wrong options is an error
    page.form['definition'] = '\n'.join((
        'Kategorie * =',
        '    ( ) Horwer Non-Profit-Organisationen',
        '    ( ) Übrige Organisationen und Privatpersonen',
        '    ( ) Auswärtige',
        'Räumlichkeiten und Anlagen * =',
        '    ( ) Saal Egli mit Foyer',
        '    ( ) Saal Egli mit Foyer, Küche und Geräte',
        '    ( ) Saal Egli mit Foyer, Küche, Geräte und Geschirr',
    ))
    page = page.form.submit()
    assert 'Mit Preisschema "Saal Egli" braucht es' in page
    assert '"Horwer Non-Profit-Organisationen (Vereine)"' in page

    # a correct category field that is non-required is also invalid
    page.form['definition'] = '\n'.join((
        'Kategorie =',
        '    ( ) Horwer Non-Profit-Organisationen (Vereine)',
        '    ( ) Übrige Organisationen und Privatpersonen',
        '    ( ) Auswärtige',
        'Räumlichkeiten und Anlagen * =',
        '    ( ) Saal Egli mit Foyer',
        '    ( ) Saal Egli mit Foyer, Küche und Geräte',
        '    ( ) Saal Egli mit Foyer, Küche, Geräte und Geschirr',
    ))
    page = page.form.submit()
    assert '"Kategorie" nicht optional sein' in page

    # a missing room field is an error
    page.form['definition'] = '\n'.join((
        'Kategorie * =',
        '    ( ) Horwer Non-Profit-Organisationen (Vereine)',
        '    ( ) Übrige Organisationen und Privatpersonen',
        '    ( ) Auswärtige',
    ))
    page = page.form.submit()
    assert 'Mit Preisschema "Saal Egli" braucht es' in page
    assert '"Saal Egli mit Foyer"' in page

    # a room field with a missing option is an error
    page.form['definition'] = '\n'.join((
        'Kategorie * =',
        '    ( ) Horwer Non-Profit-Organisationen (Vereine)',
        '    ( ) Übrige Organisationen und Privatpersonen',
        '    ( ) Auswärtige',
        'Räumlichkeiten und Anlagen * =',
        '    ( ) Saal Egli mit Foyer',
        '    ( ) Saal Egli mit Foyer, Küche und Geräte',
    ))
    page = page.form.submit()
    assert 'Mit Preisschema "Saal Egli" braucht es' in page
    assert '"Saal Egli mit Foyer"' in page

    # a correct room field that is non-required is also invalid
    page.form['definition'] = '\n'.join((
        'Kategorie * =',
        '    ( ) Horwer Non-Profit-Organisationen (Vereine)',
        '    ( ) Übrige Organisationen und Privatpersonen',
        '    ( ) Auswärtige',
        'Räumlichkeiten und Anlagen =',
        '    ( ) Saal Egli mit Foyer',
        '    ( ) Saal Egli mit Foyer, Küche und Geräte',
        '    ( ) Saal Egli mit Foyer, Küche, Geräte und Geschirr',
    ))
    page = page.form.submit()
    assert '"Räumlichkeiten und Anlagen" nicht optional sein' in page

    # the field names don't matter, only the options do
    page.form['definition'] = '\n'.join((
        'Organisation * =',
        '    ( ) Horwer Non-Profit-Organisationen (Vereine)',
        '    ( ) Übrige Organisationen und Privatpersonen',
        '    ( ) Auswärtige',
        'Räumlichkeiten * =',
        '    ( ) Saal Egli mit Foyer',
        '    ( ) Saal Egli mit Foyer, Küche und Geräte',
        '    ( ) Saal Egli mit Foyer, Küche, Geräte und Geschirr',
    ))
    page.form.submit().follow()

    transaction.begin()

    scheduler = (
        ResourceCollection(client.app.libres_context)
        .by_name('tageskarte')
        .get_scheduler(client.app.libres_context)  # type: ignore[union-attr]
    )

    allocations = scheduler.allocate(
        dates=[
            # friday
            (datetime(2026, 9, 4, 8), datetime(2026, 9, 4, 20)),
            # satuday
            (datetime(2026, 9, 5, 8), datetime(2026, 9, 5, 20)),
            # sunday
            (datetime(2026, 9, 6, 8), datetime(2026, 9, 6, 20)),
        ],
        whole_day=False,
        partly_available=True,
    )
    reserve1 = client.bound_reserve(allocations[0])
    reserve2 = client.bound_reserve(allocations[1])
    reserve3 = client.bound_reserve(allocations[2])

    transaction.commit()

    # create a two hour reservation on a friday
    assert reserve1('8:00', '9:30').json == {'success': True}

    # initially there should be no price
    page = client.get('/resource/tageskarte/form')
    assert '.00 CHF' not in page

    page.form['email'] = 'john.doe@example.com'
    page.select_radio(
        'organisation',
        'Horwer Non-Profit-Organisationen (Vereine)'
    )
    page.select_radio(
        'raumlichkeiten',
        'Saal Egli mit Foyer'
    )
    assert '30.00 CHF' in page.form.submit().follow()
    page.select_radio(
        'organisation',
        'Übrige Organisationen und Privatpersonen'
    )
    page.select_radio(
        'raumlichkeiten',
        'Saal Egli mit Foyer, Küche und Geräte'
    )
    assert '80.00 CHF' in page.form.submit().follow()
    page.select_radio(
        'organisation',
        'Auswärtige'
    )
    page.select_radio(
        'raumlichkeiten',
        'Saal Egli mit Foyer, Küche, Geräte und Geschirr'
    )
    assert '170.00 CHF' in page.form.submit().follow()
    page.form.submit().follow().form.submit()

    # open ticket
    ticket = client.get('/tickets/ALL/open').click('Annehmen').follow()
    assert '170.00' in ticket

    # changing the submission details updates the price as expected
    edit_page = ticket.click('Details bearbeiten')
    edit_page.select_radio(
        'raumlichkeiten',
        'Saal Egli mit Foyer'
    )
    ticket = edit_page.form.submit().follow()
    assert '150.00' in ticket

    # create a half day reservation on a saturday
    assert reserve2('8:00', '12:30').json == {'success': True}

    # initially there should be no price
    page = client.get('/resource/tageskarte/form')
    assert '.00 CHF' not in page

    page.form['email'] = 'john.doe@example.com'
    page.select_radio(
        'organisation',
        'Horwer Non-Profit-Organisationen (Vereine)'
    )
    page.select_radio(
        'raumlichkeiten',
        'Saal Egli mit Foyer'
    )
    assert '70.00 CHF' in page.form.submit().follow()
    page.select_radio(
        'organisation',
        'Übrige Organisationen und Privatpersonen'
    )
    page.select_radio(
        'raumlichkeiten',
        'Saal Egli mit Foyer, Küche und Geräte'
    )
    assert '160.00 CHF' in page.form.submit().follow()
    page.select_radio(
        'organisation',
        'Auswärtige'
    )
    page.select_radio(
        'raumlichkeiten',
        'Saal Egli mit Foyer, Küche, Geräte und Geschirr'
    )
    assert '350.00 CHF' in page.form.submit().follow()
    page.form.submit().follow().form.submit()

    # open ticket
    ticket = client.get('/tickets/ALL/open').click('Annehmen').follow()
    assert '350.00' in ticket

    # changing the submission details updates the price as expected
    edit_page = ticket.click('Details bearbeiten')
    edit_page.select_radio(
        'organisation',
        'Horwer Non-Profit-Organisationen (Vereine)'
    )
    ticket = edit_page.form.submit().follow()
    assert '90.00' in ticket

    # create a full day reservation on a sunday
    assert reserve3('8:00', '20:00').json == {'success': True}

    page = client.get('/resource/tageskarte/form')
    page.form['email'] = 'john.doe@example.com'
    page.select_radio(
        'organisation',
        'Horwer Non-Profit-Organisationen (Vereine)'
    )
    page.select_radio(
        'raumlichkeiten',
        'Saal Egli mit Foyer, Küche und Geräte'
    )
    assert '110.00 CHF' in page.form.submit().follow()
    page.select_radio(
        'organisation',
        'Übrige Organisationen und Privatpersonen'
    )
    page.select_radio(
        'raumlichkeiten',
        'Saal Egli mit Foyer, Küche, Geräte und Geschirr'
    )
    assert '220.00 CHF' in page.form.submit().follow()
    page.select_radio(
        'organisation',
        'Auswärtige'
    )
    page.select_radio(
        'raumlichkeiten',
        'Saal Egli mit Foyer'
    )
    assert '400.00 CHF' in page.form.submit().follow()
