from __future__ import annotations


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .conftest import Client


def test_view_user_groups(client: Client) -> None:
    client.login_admin()

    # create
    manage = client.get('/usergroups').click('Benutzergruppe', href='new')
    manage.form['name'] = 'Gruppe A'
    manage.form['users'].select_multiple(texts=['editor@example.org'])
    manage.form['ticket_permissions'].select_multiple(texts=['DIR', 'EVN'])
    page = manage.form.submit().maybe_follow()
    assert 'Gruppe A' in page
    assert 'editor@example.org' in page
    assert 'DIR' in page
    assert 'EVN' in page

    page = client.get('/usermanagement').click('Ansicht', index=1)
    assert 'editor@example.org' in page
    assert 'Gruppe A' in page

    # modify
    manage = client.get('/usergroups').click('Ansicht').click('Bearbeiten')
    manage.form['name'] = 'Gruppe B'
    manage.form['users'].select_multiple(texts=['admin@example.org'])
    manage.form['ticket_permissions'].select_multiple(texts=['DIR', 'FRM'])
    page = manage.form.submit().maybe_follow()
    assert 'Gruppe B' in page
    assert 'admin@example.org' in page
    assert 'editor@example.org' not in page
    assert 'DIR' in page
    assert 'EVN' not in page
    assert 'FRM' in page

    page = client.get('/usermanagement').click('Ansicht', index=0)
    assert 'admin@example.org' in page
    assert 'Gruppe A' not in page
    assert 'Gruppe B' in page

    page = client.get('/usermanagement').click('Ansicht', index=1)
    assert 'editor@example.org' in page
    assert 'Gruppe A' not in page
    assert 'Gruppe B' not in page

    # delete
    client.get('/usergroups').click('Ansicht').click('Löschen')
    assert 'Alle (0)' in client.get('/usergroups')
