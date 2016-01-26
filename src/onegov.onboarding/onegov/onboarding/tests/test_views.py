import onegov.onboarding

from morepath import setup
from onegov.core.utils import Bunch, scan_morepath_modules
from onegov.testing import utils
from onegov.town import TownApp
from webtest import TestApp as Client


def test_view_permissions():
    utils.assert_explicit_permissions(onegov.onboarding)


def test_default_assistant(onboarding_app):
    c = Client(onboarding_app)
    assert c.get('/').follow().request.url.endswith('for-towns/1')


def test_town_go_back(onboarding_app):
    c = Client(onboarding_app)
    a = c.get('/for-towns/1')

    a.form['name'] = 'New York'
    a.form['user'] = 'admin@example.org'
    a.form['color'] = '#ff00ff'
    a = a.form.submit().follow()

    assert 'New York' in a
    assert 'admin@example.org' in a
    assert '#f0f' in a
    assert 'new-york.example.org' in a

    a = a.click("Zurück")
    assert 'New York' in a
    assert 'admin@example.org' in a
    assert '#f0f' in a

    a.form['name'] = 'New Jersey'
    a.form['user'] = 'major@example.org'
    a = a.form.submit().follow()

    assert 'New Jersey' in a
    assert 'major@example.org' in a
    assert '#f0f' in a
    assert 'new-jersey.example.org' in a


def test_town_valid_values(onboarding_app):
    c = Client(onboarding_app)
    a = c.get('/for-towns/1')

    a.form['name'] = 'a' * 64
    a.form['user'] = 'admin'
    a.form['color'] = 'grüen'
    a = a.form.submit()

    assert "Feld kann nicht länger als 63 Zeichen sein" in a
    assert "Ungültige Email-Adresse" in a
    assert "'grüen' is not a recognized color" in a


def test_town_create(onboarding_app, temporary_directory, smtp):
    c = Client(onboarding_app)
    a = c.get('/for-towns/1')

    a.form['name'] = 'New York'
    a.form['user'] = 'admin@example.org'
    a.form['color'] = '#ff00ff'
    a = a.form.submit().follow()

    assert 'New York' in a
    assert 'admin@example.org' in a
    assert '#f0f' in a
    assert 'new-york.example.org' in a

    a = a.form.submit()

    assert 'https://new-york.example.org' in a
    assert 'admin@example.org' in a
    assert len(smtp.outbox) == 1

    username = 'admin@example.org'
    password = a.pyquery('.product dd:nth-child(4)').text()

    config = setup()
    scan_morepath_modules(onegov.town.TownApp, config)
    config.commit()

    town = TownApp()
    town.namespace = onboarding_app.onboarding['onegov.town']['namespace']
    town.configure_application(
        dsn=onboarding_app.dsn,
        filestorage='fs.osfs.OSFS',
        filestorage_options={
            'root_path': temporary_directory,
            'create': True
        },
        identity_secure=False,
        disable_memcached=True,
        enable_elasticsearch=False
    )
    town.set_application_id(town.namespace + '/' + 'new_york')
    town.registry.settings.cronjobs = Bunch(enabled=False)

    c = Client(town)
    p = c.get('/')

    assert "Willkommen bei OneGov" in p
    assert "New York" in p

    p = c.get('/auth/login')
    p.forms[1]['username'] = username
    p.forms[1]['password'] = password
    p = p.forms[1].submit().follow()

    assert 'Benutzerprofil' in p
