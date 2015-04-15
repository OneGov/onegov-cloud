# -*- coding: utf-8 -*-
import onegov.core
import onegov.town

from mock import patch
from morepath import setup
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

    assert client.get('/images', expect_errors=True).status_code == 403

    login_page = client.get('/login')
    login_page.form.set('email', 'admin@example.org')
    login_page.form.set('password', 'hunter2')
    login_page.form.submit()

    images_page = client.get('/images')

    assert "Noch keine Bilder hochgeladen" in images_page

    images_page.form['file'] = Upload('Test.txt', b'x')
    assert images_page.form.submit(expect_errors=True).status_code == 415

    images_page.form['file'] = Upload('Test.jpg', b'x')
    images_page = images_page.form.submit().follow()

    assert "Noch keine Bilder hochgeladen" not in images_page
