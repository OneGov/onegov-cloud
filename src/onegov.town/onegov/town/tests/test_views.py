# -*- coding: utf-8 -*-
import onegov.core
import onegov.town

from mock import patch
from morepath import setup
from pyquery import PyQuery as pq
from webtest import TestApp as Client
from webtest import Upload


@patch('morepath.directive.register_view')
def test_view_permissions(register_view):
    config = setup()
    config.scan(onegov.core)
    config.scan(onegov.town)
    config.commit()

    # make sure that all registered views have an explicit permission
    for call in register_view.call_args_list:
        view = call[0][2]
        module = view.__venusian_callbacks__[None][0][1]
        permission = call[0][5]

        if module.startswith('onegov.town') and permission is None:
            assert permission is not None, (
                'view {}.{} has no permission'.format(module, view.__name__))


def test_view_login(town_app):

    client = Client(town_app)

    assert client.get('/logout', expect_errors=True).status_code == 403

    response = client.get('/login')

    # German is the default translation and there's no English translation yet
    # (the default *is* English, but it needs to be added as a locale, or it
    # won't be used)
    assert response.status_code == 200
    assert u"E-Mail Adresse" in response.text
    assert u"Passwort" in response.text

    assert 'userid' not in client.cookies
    assert 'role' not in client.cookies
    assert 'application_id' not in client.cookies
    assert client.get('/logout', expect_errors=True).status_code == 403

    response.form.set('email', 'admin@example.org')
    response = response.form.submit()
    assert response.status_code == 200
    assert u"E-Mail Adresse" in response.text
    assert u"Passwort" in response.text
    assert u"Dieses Feld wird benötigt." in response.text

    assert 'userid' not in client.cookies
    assert 'role' not in client.cookies
    assert 'application_id' not in client.cookies
    assert client.get('/logout', expect_errors=True).status_code == 403

    response.form.set('email', 'admin@example.org')
    response.form.set('password', 'hunter2')
    response = response.form.submit()
    assert response.status_code == 302

    assert 'userid' in client.cookies
    assert 'role' in client.cookies
    assert 'application_id' in client.cookies

    assert client.get('/logout').status_code == 302
    assert 'userid' not in client.cookies
    assert 'role' not in client.cookies
    assert 'application_id' not in client.cookies

    assert client.get('/logout', expect_errors=True).status_code == 403


def test_view_images(town_app):

    client = Client(town_app)

    assert client.get('/bilder', expect_errors=True).status_code == 403

    login_page = client.get('/login')
    login_page.form.set('email', 'admin@example.org')
    login_page.form.set('password', 'hunter2')
    login_page.form.submit()

    images_page = client.get('/bilder')

    assert "Noch keine Bilder hochgeladen" in images_page

    images_page.form['file'] = Upload('Test.txt', b'x')
    assert images_page.form.submit(expect_errors=True).status_code == 415

    images_page.form['file'] = Upload('Test.jpg', b'x')
    images_page = images_page.form.submit().follow()

    assert "Noch keine Bilder hochgeladen" not in images_page


def test_startpage(town_app):
    client = Client(town_app)

    links = pq(client.get('/').text).find('.top-bar-section a')

    links[0].text == 'Leben & Wohnen'
    links[0].attrib.get('href') == '/gemeinde/leben-wohnen'

    links[1].text == 'Kultur & Freizeit'
    links[1].attrib.get('href') == '/gemeinde/kultur-freizeit'

    links[2].text == 'Bildung & Gesellschaft'
    links[2].attrib.get('href') == '/gemeinde/bildung-gesellschaft'

    links[3].text == 'Gewerbe & Tourismus'
    links[3].attrib.get('href') == '/gemeinde/gewerbe-tourismus'

    links[4].text == 'Politik & Verwaltung'
    links[4].attrib.get('href') == '/gemeinde/politik-verwaltung'


def test_login(town_app):
    client = Client(town_app)

    links = pq(client.get('/').text).find('.bottom-links a')
    assert links[0].text == 'Login'

    login_page = client.get(links[0].attrib.get('href'))
    login_page.form['email'] = 'admin@example.org'
    login_page.form['password'] = ''
    login_page = login_page.form.submit()

    assert u"Dieses Feld wird benötigt" in login_page.text

    login_page.form['email'] = 'admin@example.org'
    login_page.form['password'] = 'wrong'
    login_page = login_page.form.submit()

    assert "Unbekannter Benutzername oder falsches Passwort" in login_page.text

    login_page.form['email'] = 'admin@example.org'
    login_page.form['password'] = 'hunter2'

    index_page = login_page.form.submit().follow()
    assert "Sie wurden eingeloggt" in index_page.text

    links = pq(index_page.text).find('.bottom-links a')
    assert links[0].text == 'Logout'

    index_page = client.get(links[0].attrib.get('href')).follow()
    assert "Sie wurden ausgeloggt" in index_page.text

    links = pq(index_page.text).find('.bottom-links a')
    assert links[0].text == 'Login'


def test_settings(town_app):
    client = Client(town_app)

    assert client.get('/einstellungen', expect_errors=True).status_code == 403

    login_page = client.get('/login')
    login_page.form['email'] = 'admin@example.org'
    login_page.form['password'] = 'hunter2'
    login_page.form.submit()

    settings_page = client.get('/einstellungen')
    document = pq(settings_page.text)

    assert document.find('input[name=name]').val() == 'Govikon'
    assert document.find('input[name=primary_color]').val() == '#006fba'

    settings_page.form['primary_color'] = '#xxx'
    settings_page = settings_page.form.submit()

    assert u"Ungültige Farbe." in settings_page.text

    settings_page.form['primary_color'] = '#ccddee'
    settings_page = settings_page.form.submit()

    assert u"Ungültige Farbe." not in settings_page.text

    settings_page.form['logo_url'] = 'https://seantis.ch/logo.img'
    settings_page = settings_page.form.submit()

    print(settings_page.text)
    assert '<img src="https://seantis.ch/logo.img"' in settings_page.text


def test_unauthorized(town_app):
    client = Client(town_app)

    unauth_page = client.get('/einstellungen', expect_errors=True)
    assert u"Zugriff verweigert" in unauth_page.text
    assert u"folgen Sie diesem Link um sich anzumelden" in unauth_page.text

    link = pq(unauth_page.text).find('#alternate-login-link')[0]
    login_page = client.get(link.attrib.get('href'))
    login_page.form['email'] = 'editor@example.org'
    login_page.form['password'] = 'hunter2'
    unauth_page = login_page.form.submit().follow(expect_errors=True)

    assert u"Zugriff verweigert" in unauth_page.text
    assert u"mit einem anderen Benutzer anzumelden" in unauth_page.text

    link = pq(unauth_page.text).find('#alternate-login-link')[0]
    login_page = client.get(link.attrib.get('href'))
    login_page.form['email'] = 'admin@example.org'
    login_page.form['password'] = 'hunter2'
    settings_page = login_page.form.submit().follow()

    assert settings_page.status_code == 200
    assert u"Zugriff verweigert" not in settings_page
