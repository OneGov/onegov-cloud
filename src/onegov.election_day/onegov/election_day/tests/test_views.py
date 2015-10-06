# -*- coding: utf-8 -*-
import onegov.election_day
import transaction

from datetime import date
from onegov.ballot import Vote
from onegov.testing import utils
from webtest import TestApp as Client


def test_view_permissions():
    utils.assert_explicit_permissions(onegov.election_day)


def test_view_login_logout(election_day_app):
    client = Client(election_day_app)

    login = client.get('/').click('Anmelden')
    login.form['username'] = 'admin@example.org'
    login.form['password'] = 'hunter1'

    assert "Unbekannter Benutzername oder falsches Passwort" \
        in login.form.submit()
    assert 'Anmelden' in client.get('/')

    login.form['password'] = 'hunter2'
    homepage = login.form.submit().follow()

    assert 'Sie sind angemeldet' in homepage
    assert 'Abmelden' in homepage
    assert 'Anmelden' not in homepage

    assert 'Anmelden' in client.get('/').click('Abmelden').follow()


def test_view_manage(election_day_app):
    client = Client(election_day_app)

    assert client.get('/manage', expect_errors=True).status_code == 403

    login = client.get('/auth/login')
    login.form['username'] = 'admin@example.org'
    login.form['password'] = 'hunter2'
    login.form.submit()

    manage = client.get('/manage')
    assert "Noch keine Abstimmungen erfasst" in manage

    election_day_app.session().add(Vote(
        title="Vote for a better tomorrow",
        domain='federation',
        date=date(2015, 6, 14)
    ))

    transaction.commit()

    manage = client.get('/manage')
    assert "Vote for a better tomorrow" in manage

    delete = manage.click(u"Löschen")
    assert u"Bestätigung" in delete
    assert "Vote for a better tomorrow" in delete
    assert "Bearbeiten" in delete.click("Abbrechen")

    manage = delete.form.submit().follow()
    assert "Noch keine Abstimmungen erfasst" in manage
