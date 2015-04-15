# -*- coding: utf-8 -*-
import onegov.core
import onegov.town

from mock import patch
from morepath import setup
from webtest import TestApp as Client


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
