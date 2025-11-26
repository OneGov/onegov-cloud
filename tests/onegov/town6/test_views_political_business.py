from __future__ import annotations

from freezegun import freeze_time

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .conftest import Client


def test_political_businesses(client: Client) -> None:
    client.login_admin().follow()

    # ris views not enabled
    assert client.get('/political-businesses', status=404)
    assert client.get('/political-businesses/new', status=404)

    # enable ris
    settings = client.get('/ris-enable')
    settings.form['ris_enabled'] = True
    settings.form.submit()

    # add parliamentary groups first
    groups = client.get('/parliamentary-groups')
    assert 'Noch keine Fraktionen erfasst' in groups

    page = client.get('/parliamentary-groups/new')
    page.form['name'] = 'Für ein schöneres Luzern'
    page = page.form.submit().follow()
    assert 'Für ein schöneres Luzern' in page

    page = client.get('/parliamentary-groups/new')
    page.form['name'] = 'Oberfraktion'
    page = page.form.submit().follow()
    assert 'Oberfraktion' in page

    # add parliamentarians
    new = client.get('/parliamentarians/new')
    new.form['first_name'] = 'Bau'
    new.form['last_name'] = 'Mann'
    new.form['email_primary'] = 'bau.mann@example.org'
    page = new.form.submit().follow()
    assert 'Bau' in page
    assert 'Mann' in page

    # add parliamentarian role
    role = page.click('Neue Fraktionsfunktion')
    options = role.form['parliamentary_group_id'].options
    id = next(
        (opt[0] for opt in options if opt[2] == 'Für ein schöneres Luzern'))
    role.form['parliamentary_group_id'] = id
    role.form['parliamentary_group_role'] = 'member'
    role.form.submit().follow()

    with freeze_time('2025-11-04 8:00'):
        page = client.get('/political-businesses')
        assert 'Es wurden noch keine politischen Geschäfte erfasst' in page

        page = page.click('Politisches Geschäft')
        title = 'How many congressmen does it take to change a light bulb?'
        page.form['title'] = title
        page.form['number'] = '25.10'
        page.form['political_business_type'] = 'inquiry'
        page.form['entry_date'] = '2025-10-02'
        page.form['status'] = 'pendent_legislative'
        options = page.form['parliamentary_groups'].options
        # id = next((opt[0] for opt in options if opt[2] ==
        #            'Für ein schöneres Luzern'))
        page.form['parliamentary_groups'] = [o[0] for o in options]
        page = page.form.submit().follow()
        assert title in page
        keywords = ['Für ein schöneres Luzern', 'Oberfraktion',
                    'Geschäftsart', 'Anfrage', 'Status', 'Pendent Legislative',
                    'Einreichungs-/Publikationsdatum', '02.10.2025']
        for keyword in keywords:
            assert keyword in page

        # edit adding author
        edit = page.click('Bearbeiten')
        options = edit.form['participants-0-parliamentarian_id'].options
        id = next(
            (opt[0] for opt in options if opt[2] == 'Mann Bau'))
        edit.form['participants-0-parliamentarian_id'] = id
        edit.form['participants-0-participant_type'] = 'First signatory'
        page = edit.form.submit().follow()
        assert 'Erstunterzeichner' in page
        keywords = ['Verfasser/Beteiligte', 'Mann', 'Bau', 'Erstunterzeichner',
                    'Fraktion', 'Geschäftsart', 'Anfrage',
                    'Status', 'Pendent Legislative',
                    'Einreichungs-/Publikationsdatum', '02.10.2025']
        for keyword in keywords:
            assert keyword in page
        assert 'Dokumente' not in page

        # test business overview and filters
        page = client.get('/political-businesses')
        keywords = [
            'Politische Geschäfte', '02.10.2025',
            'How many congressmen does it take to change a light bulb?',
            'Geschäftsart', 'Anfrage (1)',
            'Status', 'Pendent Legislative (1)', 'Jahr', '2025 (1)']
        for keyword in keywords:
            assert keyword in page

    # delete businesses
    (client.get('/political-businesses')
     .click('ow many congressmen does it take to change a light bulb?')
     .click('Löschen'))
    assert "Es wurden noch keine politischen Geschäfte erfasst" in client.get(
        "/political-businesses"
    )

    # delete parliamentarian
    client.get('/parliamentarians').click('Mann Bau').click('Löschen')
    assert (
        "Keine Filterergebnisse gefunden oder noch keine "
        "Parlamentarier erfasst"
        in client.get("/parliamentarians")
    )

    # delete parliamentary groups
    (client.get('/parliamentary-groups')
     .click('Für ein schöneres Luzern').click('Löschen'))
    (client.get('/parliamentary-groups')
     .click('Oberfraktion').click('Löschen'))
    groups = client.get('/parliamentary-groups')
    assert 'Noch keine Fraktionen erfasst' in groups
