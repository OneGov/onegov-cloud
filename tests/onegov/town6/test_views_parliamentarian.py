from __future__ import annotations

from typing import TYPE_CHECKING

from freezegun import freeze_time

if TYPE_CHECKING:
    from .conftest import Client


def test_parliamentarians(client: Client) -> None:
    client.login_admin()

    # ris views not enabled
    assert client.get('/parliamentarian', status=404)
    assert client.get('/parliamentarian/new', status=404)

    # enable ris
    settings = client.get('/ris-enable')
    settings.form['ris_enabled'] = True
    settings.form.submit()

    # add parliamentary group
    page = client.get('/parliamentary-groups/new')
    page.form['name'] = 'Die Moderne Fraktion'
    page.form.submit()

    page = client.get('/parliamentary-groups/new')
    page.form['name'] = 'Old Party Fraktion'
    page.form.submit()

    # add commission

    # configure interest ties
    # TODO

    with freeze_time("2025-11-03 8:00"):
        parliamentarian_pages = []

        page = client.get('/parliamentarians')
        assert ('Keine Filterergebnisse gefunden oder noch keine '
                'Parlamentarier erfasst') in page

        # filter keywords
        for keyword in ['Aktiv', 'Inaktiv', 'Partei']:
            assert keyword in page

        # add parliamentarian
        new = client.get('/parliamentarians/new')
        new.form['first_name'] = 'Funny'
        new.form['last_name'] = 'Comedian'
        new.form['email_primary'] = 'funny.comedian@fun.org'
        new.form['party'] = 'Die Moderne'
        # TODO: set interest tie

        parliamentarian = new.form.submit().follow()
        parliamentarian_pages.append(parliamentarian)
        assert 'Funny' in parliamentarian
        assert 'Comedian' in parliamentarian
        assert 'funny.comedian@fun.org' in parliamentarian
        assert 'Die Moderne' in parliamentarian

        # edit parliamentarian
        edit = parliamentarian.click('Bearbeiten')
        edit.form['first_name'] = 'Laugh'
        parliamentarian = edit.form.submit().follow()
        assert 'Laugh' in parliamentarian

        # TODO: add new role
        role = parliamentarian.click('Neue Fraktionsfunktion')
        options = role.form['parliamentary_group_id'].options
        id = next(
            (opt[0] for opt in options if opt[2] == 'Die Moderne Fraktion'))
        role.form['parliamentary_group_id'] = id
        role.form['parliamentary_group_role'] = 'member'
        parliamentarian = role.form.submit().follow()
        assert 'Neue Rolle hinzugefügt' in parliamentarian
        assert 'Mitglied Parlament' in parliamentarian
        assert 'Mitglied Fraktion' in parliamentarian
        assert 'Die Moderne Fraktion' in parliamentarian

        # TODO: add new commission

        # add another parliamentarian
        new = client.get('/parliamentarians/new')
        new.form['first_name'] = 'Old'
        new.form['last_name'] = 'Man'
        new.form['email_primary'] = 'old.man@cov.org'
        new.form['party'] = 'Old Party'

        parliamentarian = new.form.submit().follow()
        parliamentarian_pages.append(parliamentarian)
        assert 'Old' in parliamentarian
        assert 'Man' in parliamentarian
        assert 'old.man@cov.org' in parliamentarian
        assert 'Old Party' in parliamentarian

        # Test filters on overview
        page = client.get('/parliamentarians')
        page = page.click('Inaktiv')  # inactive by default for now
        assert 'Comedian Laugh' in page
        assert 'Die Moderne' in page
        assert 'Man Old' in page
        assert 'Old Party' in page
        # TODO: test more

        # delete parliamentarian
        for parliamentarian in parliamentarian_pages:
            parliamentarian.click('Löschen')
        page = client.get('/parliamentarians')
        assert ('Keine Filterergebnisse gefunden oder noch keine '
                'Parlamentarier erfasst') in page
