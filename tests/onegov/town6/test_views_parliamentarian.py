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

    # configure interest ties
    # TODO

    with freeze_time("2025-11-03 8:00"):
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
        assert 'Funny' in parliamentarian
        assert 'Comedian' in parliamentarian
        assert 'funny.comedian@fun.org' in parliamentarian
        assert 'Die Moderne' in parliamentarian

        # add another parliamentarian
        # TODO

        # Test filters
        # TODO

        # edit parliamentarian
        edit = parliamentarian.click('Bearbeiten')
        edit.form['first_name'] = 'Laugh'
        # TODO: add new role
        # TODO: add new commission
        parliamentarian = edit.form.submit().follow()
        assert 'Laugh' in parliamentarian

        # delete parliamentarian
        parliamentarian.click('Löschen')
        assert ('Keine Filterergebnisse gefunden oder noch keine '
                'Parlamentarier erfasst') in page
