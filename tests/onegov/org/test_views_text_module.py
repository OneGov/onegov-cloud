from __future__ import annotations


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .conftest import Client


def test_view_text_modules(client: Client) -> None:
    client.login_editor()

    # create
    manage = client.get('/text-modules').click('Textbaustein', href='add')
    manage.form['name'] = 'Reservation ablehnen'
    manage.form['text'] = (
        'Wir müssen Ihre Reservation leider ablehnen.\n'
        'Wir hoffen um Ihr Verständnis\n'
        '\n'
        'Freundliche Grüsse'
    )
    page = manage.form.submit().maybe_follow()
    assert 'Reservation ablehnen' in page
    assert 'Wir müssen Ihre Reservation leider ablehnen. ...' in page

    # modify
    manage = client.get('/text-modules').click('Ansicht').click('Bearbeiten')
    manage.form['name'] = 'Reservation akzeptieren'
    manage.form['text'] = (
        'Ihre Reservation wurde akzeptiert.'
        '\n'
        'Freundliche Grüsse'
    )
    page = manage.form.submit().maybe_follow()
    assert 'Reservation akzeptieren' in page
    assert 'Reservation ablehnen' not in page
    assert 'Ihre Reservation wurde akzeptiert. ...' in page

    # delete
    client.get('/text-modules').click('Ansicht').click('Löschen')
    assert 'Alle (0)' in client.get('/text-modules')
