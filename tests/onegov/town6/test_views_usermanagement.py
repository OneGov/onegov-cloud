from __future__ import annotations

import transaction


from onegov.user import User


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import pytest

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
    user = client.app.session().query(User).filter_by(
        username='editor@example.org'
    ).one()
    user.release_features = None
    transaction.commit()

    client.login_editor()

    changes_root = tmp_path / 'changes'
    release_changes = changes_root / '2026.47'
    release_changes.mkdir(parents=True)
    (release_changes / 'new-feature.yaml').write_text(
        'title: A new feature\n'
        'description: A useful new feature\n',
        encoding='utf-8'
    )

    monkeypatch.setattr(
        'onegov.town6.layout.resource_files',
        lambda _: tmp_path
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
        username='editor@example.org'
    ).one()
    assert user.release_features == client.app.version

    client.logout()
    client.login_editor()
    assert '#newFeaturesModal' not in client.get('/')
