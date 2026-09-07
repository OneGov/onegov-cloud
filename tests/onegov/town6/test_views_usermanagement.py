from __future__ import annotations


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .conftest import Client


def test_add_new_user_hides_editmode_links(client: Client) -> None:
    client.login_admin()

    client.app.enable_yubikey = False

    new = client.get('/usermanagement').click('Benutzer', href='new')
    assert 'save-link' in new
    assert 'cancel-link' in new

    new.form['username'] = 'newuser@example.org'
    new.form['role'] = 'member'
    new.form['send_activation_email'] = False
    added = new.form.submit()

    assert 'Passwort' in added
    assert 'save-link' not in added
    assert 'cancel-link' not in added
