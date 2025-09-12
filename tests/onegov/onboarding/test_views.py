from __future__ import annotations

import morepath
import onegov.onboarding
import os

from onegov.core.utils import Bunch, scan_morepath_modules
from tests.shared import Client, utils
from onegov.town6 import TownApp


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.onboarding.app import OnboardingApp


def test_view_permissions() -> None:
    utils.assert_explicit_permissions(
        onegov.onboarding, onegov.onboarding.OnboardingApp)


def test_default_assistant(onboarding_app: OnboardingApp) -> None:
    c = Client(onboarding_app)
    assert c.get('/').follow().request.url.endswith('for-towns/1')


def test_town_go_back(onboarding_app: OnboardingApp) -> None:
    c = Client(onboarding_app)
    a = c.get('/for-towns/1')

    a.form['name'] = 'New York'
    a.form['user'] = 'admin@example.org'
    a.form['color'] = '#ff00ff'
    a.form['user_name'] = 'Major'
    a.form['phone_number'] = '+41791112233'
    a.form['checkbox'].value = True
    a = a.form.submit().follow()

    assert 'New York' in a
    assert 'admin@example.org' in a
    assert '#ff00ff' in a
    assert 'new-york.example.org' in a
    a = a.click("Zurück")
    assert 'New York' in a
    assert 'admin@example.org' in a
    assert '#ff00ff' in a

    a.form['name'] = 'New Jersey'
    a.form['user'] = 'major@example.org'
    a.form['user_name'] = 'Major'
    a.form['phone_number'] = '+41791112233'
    a.form['checkbox'].value = True
    a = a.form.submit().follow()

    assert 'New Jersey' in a
    assert 'major@example.org' in a
    assert '#ff00ff' in a
    assert 'new-jersey.example.org' in a


def test_town_valid_values(onboarding_app: OnboardingApp) -> None:
    c = Client(onboarding_app)
    a = c.get('/for-towns/1')

    a.form['name'] = 'a' * 64
    a.form['user'] = 'admin'
    a.form['color'] = 'grüen'
    a.form['user_name'] = 'Major'
    a.form['phone_number'] = '07911233'
    a.form['checkbox'].value = True
    a = a.form.submit()

    assert "Feld kann nicht länger als 63 Zeichen sein" in a
    assert "Ungültige Email-Adresse" in a
    assert "Ungültige Farbe" in a
    assert "Ungültige Telefonnummer" in a


def test_town_create(
    onboarding_app: OnboardingApp,
    temporary_directory: str,
    maildir: str,
    redis_url: str
) -> None:

    c = Client(onboarding_app)
    a = c.get('/for-towns/1')

    a.form['name'] = 'New York0'
    a.form['user'] = 'admin@example.org'
    a.form['color'] = '#ff00ff'
    a.form['user_name'] = 'Major'
    a.form['phone_number'] = '+41791112233'
    a.form['checkbox'].value = True

    assert 'Nur Buchstaben sind erlaubt' in a.form.submit()
    a.form['name'] = 'New York'
    a = a.form.submit().follow()

    assert 'New York' in a
    assert 'admin@example.org' in a
    assert '#ff00ff' in a
    assert 'new-york.example.org' in a

    a = a.form.submit()

    assert 'https://new-york.example.org' in a
    assert 'admin@example.org' in a
    assert len(os.listdir(maildir)) == 1

    username = 'admin@example.org'
    password = a.pyquery('.product dd:nth-child(4)').text()

    scan_morepath_modules(onegov.town6.TownApp)
    morepath.commit(onegov.town6.TownApp)

    town = TownApp()
    town.namespace = onboarding_app.onboarding['onegov.town6']['namespace']
    town.configure_application(
        dsn=onboarding_app.dsn,
        filestorage='fs.osfs.OSFS',
        filestorage_options={
            'root_path': temporary_directory,
            'create': True
        },
        identity_secure=False,
        redis_url=redis_url,
        enable_elasticsearch=False,
        depot_backend='depot.io.memory.MemoryFileStorage',
        websockets={
            'client_url': 'ws://localhost:8766',
            'manage_url': 'ws://localhost:8766',
            'manage_token': 'super-super-secret-token'
        }
    )
    town.set_application_id(town.namespace + '/' + 'new_york')
    town.settings.cronjobs = Bunch(enabled=False)  # type: ignore[attr-defined]

    c2 = Client(town)
    p = c2.get('/')

    assert "New York" in p

    p = c2.get('/auth/login')
    p.forms[1]['username'] = username
    p.forms[1]['password'] = password
    p = p.forms[1].submit().follow()

    assert 'Benutzerprofil' in p
