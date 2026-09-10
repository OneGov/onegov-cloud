from __future__ import annotations


import importlib

import pytest

from onegov.user import User


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pathlib import Path
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


def test_new_feature_close_and_read(
    client: Client,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    client.login_admin()

    changes_root = tmp_path / 'changes'
    current_changes = changes_root / 'current'
    current_changes.mkdir(parents=True)
    (current_changes / 'new-feature.yaml').write_text(
        'title: A new feature\n'
        'description: A useful new feature\n'
        'applications:\n'
        '  - all\n',
        encoding='utf-8'
    )

    town6_layout = importlib.import_module('onegov.town6.layout')
    monkeypatch.setattr(
        town6_layout,
        '__file__',
        str(tmp_path / 'src' / 'onegov' / 'town6' / 'layout.py')
    )

    page = client.get('/')
    assert 'A new feature' in page
    assert page.pyquery('#newFeaturesModal')

    read_button = page.pyquery('#newFeaturesModal .footer button.button').eq(1)
    read_url = read_button.attr('ic-post-to')
    assert read_url is not None
    client.post(read_url)
    assert '#newFeaturesModal' not in client.get('/')

    user = client.app.session().query(User).filter_by(
        username='admin@example.org'
    ).one()
    assert user.release_features == client.app.version

    client.logout()
    client.login_admin()
    assert '#newFeaturesModal' not in client.get('/')
