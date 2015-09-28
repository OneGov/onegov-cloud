# -*- coding: utf-8 -*-
import onegov.core
import onegov.town
import pytest
import re
import textwrap
import transaction

from datetime import datetime, date, timedelta
from libres.db.models import Reservation
from libres.modules.errors import AffectedReservationError
from lxml.html import document_fromstring
from onegov.form import FormCollection, FormSubmission
from onegov.libres import ResourceCollection
from onegov.testing import utils
from onegov.ticket import TicketCollection
from webtest import (
    TestApp as BaseApp,
    TestResponse as BaseResponse,
    TestRequest as BaseRequest
)
from webtest import Upload


class SkipFirstForm(object):

    @property
    def form(self):
        """ Ignore the first form, which is the general search form on
        the top of the page.

        """
        if len(self.forms) > 1:
            return self.forms[1]
        else:
            return super(SkipFirstForm, self).form


class Response(SkipFirstForm, BaseResponse):
    pass


class Request(SkipFirstForm, BaseRequest):
    ResponseClass = Response


class Client(SkipFirstForm, BaseApp):
    RequestClass = Request


def extract_href(link):
    """ Takes a link (<a href...>) and returns the href address. """
    result = re.search(r'(?:href|ic-delete-from)="([^"]+)', link)

    return result and result.group(1) or None


def test_view_permissions():
    utils.assert_explicit_permissions(onegov.town)


def test_view_form_alert(town_app):

    login = Client(town_app).get('/login')
    login = login.form.submit()

    assert u'Das Formular enthält Fehler' in login


def test_view_login(town_app):

    client = Client(town_app)

    assert client.get('/logout', expect_errors=True).status_code == 403

    response = client.get('/login')

    # German is the default translation and there's no English translation yet
    # (the default *is* English, but it needs to be added as a locale, or it
    # won't be used)
    assert response.status_code == 200
    assert u"E-Mail Adresse" in response
    assert u"Passwort" in response

    assert client.get('/logout', expect_errors=True).status_code == 403

    response.form.set('email', 'admin@example.org')
    response = response.form.submit()
    assert response.status_code == 200
    assert u"E-Mail Adresse" in response
    assert u"Passwort" in response
    assert u"Dieses Feld wird benötigt." in response
    assert client.get('/logout', expect_errors=True).status_code == 403

    response.form.set('email', 'admin@example.org')
    response.form.set('password', 'hunter2')
    response = response.form.submit()

    assert response.status_code == 302
    assert client.get('/logout').status_code == 302
    assert client.get('/logout', expect_errors=True).status_code == 403


def test_view_files(town_app):

    client = Client(town_app)

    assert client.get('/dateien', expect_errors=True).status_code == 403

    login_page = client.get('/login')
    login_page.form.set('email', 'admin@example.org')
    login_page.form.set('password', 'hunter2')
    login_page.form.submit()

    files_page = client.get('/dateien')

    assert "Noch keine Dateien hochgeladen" in files_page

    files_page.form['file'] = Upload('Test.txt', b'File content.')
    files_page = files_page.form.submit().follow()

    assert "Noch keine Dateien hochgeladen" not in files_page
    assert 'Test.txt' in files_page


def test_view_images(town_app):

    client = Client(town_app)

    assert client.get('/bilder', expect_errors=True).status_code == 403

    login_page = client.get('/login')
    login_page.form.set('email', 'admin@example.org')
    login_page.form.set('password', 'hunter2')
    login_page.form.submit()

    images_page = client.get('/bilder')

    assert "Noch keine Bilder hochgeladen" in images_page

    images_page.form['file'] = Upload('Test.txt', b'File content')
    assert images_page.form.submit(expect_errors=True).status_code == 415

    images_page.form['file'] = Upload('Test.jpg', utils.create_image().read())
    images_page = images_page.form.submit().follow()

    assert "Noch keine Bilder hochgeladen" not in images_page

    name = images_page.pyquery('img').attr('src').split('/')[-1]

    # thumbnails are created on the fly
    assert town_app.filestorage.exists('images/' + name)
    assert not town_app.filestorage.exists('images/thumbnails' + name)
    client.get('/thumbnails/' + name)
    assert town_app.filestorage.exists('images/thumbnails/' + name)

    # thumbnails are deleted with the image
    delete_link = images_page.pyquery('a.delete').attr('ic-delete-from')
    client.delete(delete_link)
    assert not town_app.filestorage.exists('images/' + name)
    assert not town_app.filestorage.exists('images/thumbnails/' + name)


def test_startpage(town_app):
    client = Client(town_app)

    links = client.get('/').pyquery('.top-bar-section a')

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

    links = client.get('/').pyquery('.homepage-tiles a')

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

    links = client.get('/').pyquery('.bottom-links li:first-child a')
    assert links.text() == 'Login'

    login_page = client.get(links.attr('href'))
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

    links = index_page.pyquery('.bottom-links li:first-child a')
    assert links.text() == 'Logout'

    index_page = client.get(links.attr('href')).follow()
    assert "Sie wurden ausgeloggt" in index_page.text

    links = index_page.pyquery('.bottom-links li:first-child a')
    assert links.text() == 'Login'


def test_reset_password(town_app):
    client = Client(town_app)

    links = client.get('/').pyquery('.bottom-links li:first-child a')
    assert links.text() == 'Login'
    login_page = client.get(links.attr('href'))

    request_page = login_page.click(u'Passwort zurücksetzen')
    assert u'Passwort zurücksetzen' in request_page.text

    request_page.form['email'] = 'someone@example.org'
    assert 'someone@example.org' in request_page.form.submit().follow()
    assert len(town_app.smtpserver.outbox) == 0

    request_page.form['email'] = 'admin@example.org'
    assert 'admin@example.org' in request_page.form.submit().follow()
    assert len(town_app.smtpserver.outbox) == 1

    message = town_app.smtpserver.outbox[0]
    message = message.get_payload(0).get_payload(decode=True)
    message = message.decode('iso-8859-1')
    link = list(document_fromstring(message).iterlinks())[0][2]
    token = link.split('token=')[1]

    reset_page = client.get(link)
    assert token in reset_page.text

    reset_page.form['email'] = 'someone_else@example.org'
    reset_page.form['password'] = 'new_password'
    reset_page = reset_page.form.submit()
    assert u"Ungültiger Addresse oder abgelaufener Link" in reset_page.text
    assert token in reset_page.text

    reset_page.form['email'] = 'admin@example.org'
    reset_page.form['password'] = '1234'
    reset_page = reset_page.form.submit()
    assert "Feld muss mindestens 8 Zeichen beinhalten" in reset_page.text
    assert token in reset_page.text

    reset_page.form['email'] = 'admin@example.org'
    reset_page.form['password'] = 'new_password'
    assert u"Passwort geändert" in reset_page.form.submit().follow().text

    reset_page.form['email'] = 'admin@example.org'
    reset_page.form['password'] = 'new_password'
    reset_page = reset_page.form.submit()
    assert u"Ungültiger Addresse oder abgelaufener Link" in reset_page.text

    login_page.form['email'] = 'admin@example.org'
    login_page.form['password'] = 'hunter2'
    login_page = login_page.form.submit()
    assert "Unbekannter Benutzername oder falsches Passwort" in login_page.text

    login_page.form['email'] = 'admin@example.org'
    login_page.form['password'] = 'new_password'
    assert "Sie wurden eingeloggt" in login_page.form.submit().follow().text


def test_settings(town_app):
    client = Client(town_app)

    assert client.get('/einstellungen', expect_errors=True).status_code == 403

    login_page = client.get('/login')
    login_page.form['email'] = 'admin@example.org'
    login_page.form['password'] = 'hunter2'
    login_page.form.submit()

    settings_page = client.get('/einstellungen')
    document = settings_page.pyquery

    assert document.find('input[name=name]').val() == 'Govikon'
    assert document.find('input[name=primary_color]').val() == '#006fba'

    settings_page.form['primary_color'] = '#xxx'
    settings_page.form['reply_to'] = 'info@govikon.ch'
    settings_page = settings_page.form.submit()

    assert u"Ungültige Farbe." in settings_page.text

    settings_page.form['primary_color'] = '#ccddee'
    settings_page.form['reply_to'] = 'info@govikon.ch'
    settings_page = settings_page.form.submit()

    assert u"Ungültige Farbe." not in settings_page.text

    settings_page.form['logo_url'] = 'https://seantis.ch/logo.img'
    settings_page.form['reply_to'] = 'info@govikon.ch'
    settings_page = settings_page.form.submit()

    assert '<img src="https://seantis.ch/logo.img"' in settings_page.text

    settings_page.form['homepage_images'] = """
        http://images/one
        http://images/two
    """
    settings_page = settings_page.form.submit()

    assert 'http://images/one' in settings_page
    assert 'http://images/two' in settings_page

    settings_page.form['analytics_code'] = '<script>alert("Hi!");</script>'
    settings_page = settings_page.form.submit()
    assert '<script>alert("Hi!");</script>' in settings_page.text


def test_unauthorized(town_app):
    client = Client(town_app)

    unauth_page = client.get('/einstellungen', expect_errors=True)
    assert u"Zugriff verweigert" in unauth_page.text
    assert u"folgen Sie diesem Link um sich anzumelden" in unauth_page.text

    link = unauth_page.pyquery('#alternate-login-link')[0]
    login_page = client.get(link.attrib.get('href'))
    login_page.form['email'] = 'editor@example.org'
    login_page.form['password'] = 'hunter2'
    unauth_page = login_page.form.submit().follow(expect_errors=True)

    assert u"Zugriff verweigert" in unauth_page.text
    assert u"mit einem anderen Benutzer anzumelden" in unauth_page.text

    link = unauth_page.pyquery('#alternate-login-link')[0]
    login_page = client.get(link.attrib.get('href'))
    login_page.form['email'] = 'admin@example.org'
    login_page.form['password'] = 'hunter2'
    settings_page = login_page.form.submit().follow()

    assert settings_page.status_code == 200
    assert u"Zugriff verweigert" not in settings_page


def test_pages(town_app):
    client = Client(town_app)

    root_url = client.get('/').pyquery('.top-bar-section a').attr('href')
    assert len(client.get(root_url).pyquery('.edit-bar')) == 0

    login_page = client.get('/login?to={}'.format(root_url))
    login_page.form['email'] = 'admin@example.org'
    login_page.form['password'] = 'hunter2'
    root_page = login_page.form.submit().follow()

    assert len(root_page.pyquery('.edit-bar')) == 1
    new_page = root_page.click('Thema')
    assert "Neues Thema" in new_page

    new_page.form['title'] = "Living in Govikon is Swell"
    new_page.form['text'] = (
        "<h2>Living in Govikon is Really Great</h2>"
        "<i>Experts say it's the fact that Govikon does not really exist.</i>"
    )
    page = new_page.form.submit().follow()

    assert page.pyquery('.main-title').text() == "Living in Govikon is Swell"
    assert page.pyquery('h2').text() == "Living in Govikon is Really Great"
    assert page.pyquery('i').text().startswith("Experts say it's the fact")

    edit_page = page.click("Bearbeiten")

    assert "Thema Bearbeiten" in edit_page
    assert "&lt;h2&gt;Living in Govikon is Really Great&lt;/h2&gt" in edit_page

    edit_page.form['title'] = "Living in Govikon is Awful"
    edit_page.form['text'] = (
        "<h2>Living in Govikon Really Sucks</h2>"
        "<i>Experts say hiring more experts would help.</i>"
        "<script>alert('yes')</script>"
    )
    page = edit_page.form.submit().follow()

    assert page.pyquery('.main-title').text() == "Living in Govikon is Awful"
    assert page.pyquery('h2').text() == "Living in Govikon Really Sucks"
    assert page.pyquery('i').text().startswith("Experts say hiring more")
    assert "<script>alert('yes')</script>" not in page
    assert "&lt;script&gt;alert('yes')&lt;/script&gt;" in page

    page.click("Logout")
    root_page = client.get(root_url)

    assert len(root_page.pyquery('.edit-bar')) == 0

    assert page.pyquery('.main-title').text() == "Living in Govikon is Awful"
    assert page.pyquery('h2').text() == "Living in Govikon Really Sucks"
    assert page.pyquery('i').text().startswith("Experts say hiring more")


def test_news(town_app):
    client = Client(town_app)

    login_page = client.get('/login')
    login_page.form['email'] = 'admin@example.org'
    login_page.form['password'] = 'hunter2'
    page = login_page.form.submit().follow()

    assert len(page.pyquery('.latest-news')) == 0

    page = page.click('Aktuelles', index=1)
    page = page.click('Nachricht')

    page.form['title'] = "We have a new homepage"
    page.form['lead'] = "It is very good"
    page.form['text'] = "It is lots of fun"

    page = page.form.submit().follow()

    assert "We have a new homepage" in page.text
    assert "It is very good" in page.text
    assert "It is lots of fun" in page.text

    page = client.get('/aktuelles')

    assert "We have a new homepage" in page.text
    assert "It is very good" in page.text
    assert "It is lots of fun" not in page.text

    page = client.get('/')

    assert "We have a new homepage" in page.text
    assert "It is very good" in page.text
    assert "It is lots of fun" not in page.text

    page = page.click('weiterlesen...')

    assert "We have a new homepage" in page.text
    assert "It is very good" in page.text
    assert "It is lots of fun" in page.text

    client.delete(page.pyquery('a[ic-delete-from]').attr('ic-delete-from'))
    page = client.get('/aktuelles')

    assert "We have a new homepage" not in page.text
    assert "It is very good" not in page.text
    assert "It is lots of fun" not in page.text


def test_delete_pages(town_app):
    client = Client(town_app)

    root_url = client.get('/').pyquery('.top-bar-section a').attr('href')

    login_page = client.get('/login?to={}'.format(root_url))
    login_page.form['email'] = 'admin@example.org'
    login_page.form['password'] = 'hunter2'

    root_page = login_page.form.submit().follow()
    new_page = root_page.click('Thema')

    new_page.form['title'] = "Living in Govikon is Swell"
    new_page.form['text'] = (
        "## Living in Govikon is Really Great\n"
        "*Experts say it's the fact that Govikon does not really exist.*"
    )
    page = new_page.form.submit().follow()
    delete_link = page.pyquery('a[ic-delete-from]')[0].attrib['ic-delete-from']

    result = client.delete(delete_link.split('?')[0], expect_errors=True)
    assert result.status_code == 403

    assert client.delete(delete_link).status_code == 200
    assert client.delete(delete_link, expect_errors=True).status_code == 404


def test_links(town_app):
    client = Client(town_app)

    root_url = client.get('/').pyquery('.top-bar-section a').attr('href')

    login_page = client.get('/login?to={}'.format(root_url))
    login_page.form['email'] = 'admin@example.org'
    login_page.form['password'] = 'hunter2'
    root_page = login_page.form.submit().follow()

    new_link = root_page.click(u"Verknüpfung")
    assert u"Neue Verknüpfung" in new_link

    new_link.form['title'] = 'Google'
    new_link.form['url'] = 'https://www.google.ch'
    link = new_link.form.submit().follow()

    assert "Sie wurden nicht automatisch weitergeleitet" in link
    assert 'https://www.google.ch' in link

    link.click('Logout')

    root_page = client.get(root_url)
    assert "Google" in root_page
    google = root_page.click("Google", index=0)

    assert google.status_code == 302
    assert google.location == 'https://www.google.ch'


def test_submit_form(town_app):
    collection = FormCollection(town_app.session())
    collection.definitions.add('Profile', definition=textwrap.dedent("""
        # Your Details
        First name * = ___
        Last name * = ___
        E-Mail * = @@@
    """), type='custom')

    transaction.commit()

    client = Client(town_app)
    form_page = client.get('/formulare').click('Profile')
    assert 'Your Details' in form_page
    assert 'First name' in form_page
    assert 'Last name' in form_page
    assert 'E-Mail' in form_page

    assert 'formular/' in form_page.request.url
    form_page = form_page.form.submit().follow()

    assert 'formular/' not in form_page.request.url
    assert 'formular-eingabe' in form_page.request.url
    assert len(form_page.pyquery('small.error')) == 3

    form_page.form['your_details_first_name'] = 'Kung'
    form_page = form_page.form.submit()

    assert len(form_page.pyquery('small.error')) == 2

    form_page.form['your_details_last_name'] = 'Fury'
    form_page.form['your_details_e_mail'] = 'kung.fury@example.org'
    form_page = form_page.form.submit()

    assert len(form_page.pyquery('small.error')) == 0
    ticket_page = form_page.form.submit().follow()

    # make sure a ticket has been created
    assert 'FRM-' in ticket_page
    assert 'ticket-state-open' in ticket_page

    tickets = TicketCollection(town_app.session()).by_handler_code('FRM')
    assert len(tickets) == 1

    assert tickets[0].title == 'Kung, Fury, kung.fury@example.org'
    assert tickets[0].group == 'Profile'


def test_pending_submission_error_file_upload(town_app):
    collection = FormCollection(town_app.session())
    collection.definitions.add('Statistics', definition=textwrap.dedent("""
        Name * = ___
        Datei * = *.txt|*.csv
    """), type='custom')
    transaction.commit()

    client = Client(town_app)
    form_page = client.get('/formulare').click('Statistics')
    form_page.form['datei'] = Upload('test.jpg', utils.create_image().read())

    form_page = form_page.form.submit().follow()
    assert 'formular-eingabe' in form_page.request.url
    assert len(form_page.pyquery('small.error')) == 2


def test_pending_submission_successful_file_upload(town_app):
    collection = FormCollection(town_app.session())
    collection.definitions.add('Statistics', definition=textwrap.dedent("""
        Name * = ___
        Datei * = *.txt|*.csv
    """), type='custom')
    transaction.commit()

    client = Client(town_app)
    form_page = client.get('/formulare').click('Statistics')
    form_page.form['datei'] = Upload('README.txt', b'1;2;3')
    form_page = form_page.form.submit().follow()

    assert "README.txt" in form_page.text
    assert u"Datei ersetzen" in form_page.text
    assert u"Datei löschen" in form_page.text
    assert u"Datei behalten" in form_page.text

    # unfortunately we can't test more here, as webtest doesn't support
    # multiple differing fields of the same name...


def test_edit_builtin_form(town_app):
    client = Client(town_app)

    login_page = client.get('/login')
    login_page.form.set('email', 'editor@example.org')
    login_page.form.set('password', 'hunter2')
    login_page.form.submit()

    # the definition is read only and must be discarded in any case
    form_page = client.get('/formular/wohnsitzbestaetigung/bearbeiten')
    existing_definition = form_page.form['definition']
    form_page.form['definition'] = 'x = ___'
    form_page.form.submit()

    form_page = client.get('/formular/wohnsitzbestaetigung/bearbeiten')
    form_page.form['definition'] == existing_definition


def test_add_custom_form(town_app):
    client = Client(town_app)

    login_page = client.get('/login')
    login_page.form.set('email', 'editor@example.org')
    login_page.form.set('password', 'hunter2')
    login_page.form.submit()

    # this error is not strictly line based, so there's a general error
    form_page = client.get('/formulare/neu')
    form_page.form['title'] = "My Form"
    form_page.form['lead'] = "This is a form"
    form_page.form['text'] = "There are many like it, but this one's mine"
    form_page.form['definition'] = "abc ="
    form_page = form_page.form.submit()

    assert u"Das Formular ist nicht gültig." in form_page

    # this error is line based
    form_page = client.get('/formulare/neu')
    form_page.form['title'] = "My Form"
    form_page.form['lead'] = "This is a form"
    form_page.form['text'] = "There are many like it, but this one's mine"
    form_page.form['definition'] = "xxx = !!!"
    form_page = form_page.form.submit()

    assert u"Der Syntax in der 1. Zeile ist ungültig." in form_page
    assert 'data-highlight-line="1"' in form_page

    form_page.form['definition'] = "Name * = ___\nE-Mail * = @@@"
    form_page = form_page.form.submit().follow()

    form_page.form['name'] = 'My name'
    form_page.form['e_mail'] = 'my@name.com'
    form_page = form_page.form.submit().follow()

    form_page = client.get('/formular/my-form/bearbeiten')
    form_page.form['definition'] = "Nom * = ___\nMail * = @@@"
    form_page = form_page.form.submit().follow()

    form_page.form['nom'] = 'My name'
    form_page.form['mail'] = 'my@name.com'
    form_page.form.submit().follow()


def test_delete_builtin_form(town_app):
    client = Client(town_app)
    builtin_form = '/formular/wohnsitzbestaetigung'

    response = client.delete(builtin_form, expect_errors=True)
    assert response.status_code == 403

    login_page = client.get('/login')
    login_page.form.set('email', 'editor@example.org')
    login_page.form.set('password', 'hunter2')
    login_page.form.submit()

    response = client.delete(builtin_form, expect_errors=True)
    assert response.status_code == 403


def test_delete_custom_form(town_app):
    client = Client(town_app)

    login_page = client.get('/login')
    login_page.form.set('email', 'editor@example.org')
    login_page.form.set('password', 'hunter2')
    login_page.form.submit()

    form_page = client.get('/formulare/neu')
    form_page.form['title'] = "My Form"
    form_page.form['definition'] = "e-mail * = @@@"
    form_page = form_page.form.submit().follow()

    client.delete(
        form_page.pyquery('a.delete-link')[0].attrib['ic-delete-from'])


def test_show_uploaded_file(town_app):
    collection = FormCollection(town_app.session())
    collection.definitions.add(
        'Text', definition="File * = *.txt\nE-Mail * = @@@", type='custom')
    transaction.commit()

    client = Client(town_app)

    login_page = client.get('/login')
    login_page.form.set('email', 'editor@example.org')
    login_page.form.set('password', 'hunter2')
    login_page.form.submit()

    form_page = client.get('/formular/text')
    form_page.form['e_mail'] = 'info@example.org'
    form_page.form['file'] = Upload('test.txt', b'foobar')
    form_page = form_page.form.submit().follow()  # preview
    form_page = form_page.form.submit().follow()  # finalize

    ticket_page = client.get(
        form_page.pyquery('.ticket-number a').attr('href'))

    assert 'test.txt' in ticket_page.text
    file_response = ticket_page.click('test.txt')

    assert file_response.content_type == 'text/plain'
    assert file_response.text == 'foobar'


def test_hide_page(town_app):
    client = Client(town_app)

    login_page = client.get('/login')
    login_page.form.set('email', 'editor@example.org')
    login_page.form.set('password', 'hunter2')
    login_page.form.submit()

    new_page = client.get('/themen/leben-wohnen').click('Thema')

    new_page.form['title'] = "Test"
    new_page.form['is_hidden_from_public'] = True
    page = new_page.form.submit().follow()

    anonymous = Client(town_app)
    response = anonymous.get(page.request.url, expect_errors=True)
    assert response.status_code == 403

    edit_page = page.click("Bearbeiten")
    edit_page.form['is_hidden_from_public'] = False
    page = edit_page.form.submit().follow()

    response = anonymous.get(page.request.url)
    assert response.status_code == 200


def test_hide_news(town_app):
    client = Client(town_app)

    login_page = client.get('/login')
    login_page.form.set('email', 'editor@example.org')
    login_page.form.set('password', 'hunter2')
    login_page.form.submit()

    new_page = client.get('/aktuelles').click('Nachricht')

    new_page.form['title'] = "Test"
    new_page.form['is_hidden_from_public'] = True
    page = new_page.form.submit().follow()

    anonymous = Client(town_app)
    response = anonymous.get(page.request.url, expect_errors=True)
    assert response.status_code == 403

    edit_page = page.click("Bearbeiten")
    edit_page.form['is_hidden_from_public'] = False
    page = edit_page.form.submit().follow()

    response = anonymous.get(page.request.url)
    assert response.status_code == 200


def test_hide_form(town_app):
    client = Client(town_app)

    login_page = client.get('/login')
    login_page.form.set('email', 'editor@example.org')
    login_page.form.set('password', 'hunter2')
    login_page.form.submit()

    form_page = client.get('/formular/wohnsitzbestaetigung/bearbeiten')
    form_page.form['is_hidden_from_public'] = True
    page = form_page.form.submit().follow()

    anonymous = Client(town_app)
    response = anonymous.get(
        '/formular/wohnsitzbestaetigung', expect_errors=True)
    assert response.status_code == 403

    edit_page = page.click("Bearbeiten")
    edit_page.form['is_hidden_from_public'] = False
    page = edit_page.form.submit().follow()

    response = anonymous.get(page.request.url)
    assert response.status_code == 200


def test_people_view(town_app):
    client = Client(town_app)

    login_page = client.get('/login')
    login_page.form.set('email', 'editor@example.org')
    login_page.form.set('password', 'hunter2')
    login_page.form.submit()

    people = client.get('/personen')
    assert 'noch keine Personen' in people

    new_person = people.click('Person')
    new_person.form['first_name'] = 'Flash'
    new_person.form['last_name'] = 'Gordon'
    person = new_person.form.submit().follow()

    assert 'Flash Gordon' in person

    people = client.get('/personen')

    assert 'Flash Gordon' in people

    edit_person = person.click('Bearbeiten')
    edit_person.form['first_name'] = 'Merciless'
    edit_person.form['last_name'] = 'Ming'
    person = edit_person.form.submit().follow()

    assert 'Merciless Ming' in person

    client.delete(person.request.url)

    people = client.get('/personen')
    assert 'noch keine Personen' in people


def test_with_people(town_app):
    client = Client(town_app)

    login_page = client.get('/login')
    login_page.form.set('email', 'editor@example.org')
    login_page.form.set('password', 'hunter2')
    login_page.form.submit()

    people = client.get('/personen')

    new_person = people.click('Person')
    new_person.form['first_name'] = 'Flash'
    new_person.form['last_name'] = 'Gordon'
    new_person.form.submit()

    new_person = people.click('Person')
    new_person.form['first_name'] = 'Merciless'
    new_person.form['last_name'] = 'Ming'
    new_person.form.submit()

    new_page = client.get('/themen/leben-wohnen').click('Thema')

    assert 'Flash Gordon' in new_page
    assert 'Merciless Ming' in new_page

    new_page.form['title'] = 'About Flash'
    new_page.form['people_flash_gordon'] = True
    new_page.form['people_flash_gordon_function'] = 'Astronaut'
    edit_page = new_page.form.submit().follow().click('Bearbeiten')

    assert edit_page.form['people_flash_gordon'].value == 'y'
    assert edit_page.form['people_flash_gordon_function'].value == 'Astronaut'

    assert edit_page.form['people_merciless_ming'].value is None
    assert edit_page.form['people_merciless_ming_function'].value == ''


def test_tickets(town_app):
    client = Client(town_app)

    assert client.get(
        '/tickets/ALL/open', expect_errors=True).status_code == 403

    assert len(client.get('/').pyquery('.ticket-count')) == 0

    login_page = client.get('/login')
    login_page.form.set('email', 'editor@example.org')
    login_page.form.set('password', 'hunter2')
    login_page.form.submit()

    assert client.get('/').pyquery('.ticket-count div').text()\
        == '0 Offen 0 In Bearbeitung'

    form_page = client.get('/formulare/neu')
    form_page.form['title'] = "Newsletter"
    form_page.form['definition'] = "E-Mail *= @@@"
    form_page = form_page.form.submit()

    client.get('/logout')

    form_page = client.get('/formular/newsletter')
    form_page.form['e_mail'] = 'info@seantis.ch'

    assert len(town_app.smtpserver.outbox) == 0

    status_page = form_page.form.submit().follow().form.submit().follow()

    assert len(town_app.smtpserver.outbox) == 1

    message = town_app.smtpserver.outbox[0]
    message = message.get_payload(0).get_payload(decode=True)
    message = message.decode('iso-8859-1')

    assert 'FRM-' in message
    assert '/status' in message

    assert 'FRM-' in status_page
    assert 'Offen' in status_page

    login_page = client.get('/login')
    login_page.form.set('email', 'editor@example.org')
    login_page.form.set('password', 'hunter2')
    login_page.form.submit()

    assert client.get('/').pyquery('.ticket-count div').text()\
        == '1 Offen 0 In Bearbeitung'

    tickets_page = client.get('/tickets/ALL/open')
    assert len(tickets_page.pyquery('tr.ticket')) == 1

    ticket_page = tickets_page.click('Annehmen').follow()
    assert len(tickets_page.pyquery('tr.ticket')) == 1

    tickets_page = client.get('/tickets/ALL/pending')
    assert len(tickets_page.pyquery('tr.ticket')) == 1

    assert client.get('/').pyquery('.ticket-count div').text()\
        == '0 Offen 1 In Bearbeitung'

    assert 'editor@example.org' in ticket_page
    assert 'Newsletter' in ticket_page
    assert 'info@seantis.ch' in ticket_page
    assert 'In Bearbeitung' in ticket_page
    assert 'FRM-' in ticket_page

    ticket_url = ticket_page.request.path
    ticket_page = ticket_page.click('Ticket abschliessen').follow()

    assert client.get('/').pyquery('.ticket-count div').text()\
        == '0 Offen 0 In Bearbeitung'

    assert len(town_app.smtpserver.outbox) == 2

    message = town_app.smtpserver.outbox[1]
    message = message.get_payload(0).get_payload(decode=True)
    message = message.decode('iso-8859-1')

    assert 'FRM-' in message
    assert '/status' not in message

    assert 'FRM-' in status_page
    assert 'Offen' in status_page

    assert 'Abgeschlossen' in ticket_page
    tickets_page = client.get('/tickets/ALL/closed')
    assert len(tickets_page.pyquery('tr.ticket')) == 1

    ticket_page = client.get(ticket_url)
    ticket_page = ticket_page.click('Ticket wieder öffnen').follow()

    tickets_page = client.get('/tickets/ALL/pending')
    assert len(tickets_page.pyquery('tr.ticket')) == 1

    assert client.get('/').pyquery('.ticket-count div').text()\
        == '0 Offen 1 In Bearbeitung'

    message = town_app.smtpserver.outbox[2]
    message = message.get_payload(0).get_payload(decode=True)
    message = message.decode('iso-8859-1')

    assert 'FRM-' in message
    assert '/status' in message


def test_resource_slots(town_app):

    resources = ResourceCollection(town_app.libres_context)
    resource = resources.add("Foo", 'Europe/Zurich')

    scheduler = resource.get_scheduler(town_app.libres_context)
    scheduler.allocate(
        dates=[
            (datetime(2015, 8, 4), datetime(2015, 8, 4)),
            (datetime(2015, 8, 5), datetime(2015, 8, 5))
        ],
        whole_day=True
    )
    scheduler.allocate(
        dates=[
            (datetime(2015, 8, 6, 12, 0), datetime(2015, 8, 6, 16, 0)),
        ],
        whole_day=False
    )
    scheduler.approve_reservations(
        scheduler.reserve(
            'info@example.org',
            (datetime(2015, 8, 6, 12, 0), datetime(2015, 8, 6, 16, 0)),
        )
    )

    transaction.commit()

    client = Client(town_app)

    url = '/ressource/foo/slots'
    assert client.get(url).json == []

    url = '/ressource/foo/slots?start=2015-08-04&end=2015-08-05'
    result = client.get(url).json

    assert len(result) == 2

    assert result[0]['start'] == '2015-08-04T00:00:00+02:00'
    assert result[0]['end'] == '2015-08-05T00:00:00+02:00'
    assert result[0]['className'] == 'event-available'
    assert result[0]['title'] == u"Ganztägig\nVerfügbar"

    assert result[1]['start'] == '2015-08-05T00:00:00+02:00'
    assert result[1]['end'] == '2015-08-06T00:00:00+02:00'
    assert result[1]['className'] == 'event-available'
    assert result[1]['title'] == u"Ganztägig\nVerfügbar"

    url = '/ressource/foo/slots?start=2015-08-06&end=2015-08-06'
    result = client.get(url).json

    assert len(result) == 1
    assert result[0]['className'] == 'event-unavailable'
    assert result[0]['title'] == u"12:00 - 16:00\nBesetzt"


def test_resources(town_app):
    client = Client(town_app)

    login_page = client.get('/login')
    login_page.form.set('email', 'admin@example.org')
    login_page.form.set('password', 'hunter2')
    login_page.form.submit()

    resources = client.get('/ressourcen')
    assert 'SBB-Tageskarte' in resources

    resource = resources.click('SBB-Tageskarte')
    assert 'calendar' in resource

    new = resources.click('Raum')
    new.form['title'] = 'Meeting Room'
    resource = new.form.submit().follow()

    assert 'calendar' in resource
    assert 'Meeting Room' in resource

    edit = resource.click('Bearbeiten')
    edit.form['title'] = 'Besprechungsraum'
    edit.form.submit()

    assert 'Besprechungsraum' in client.get('/ressourcen')

    assert client.delete('/ressource/meeting-room').status_code == 200


def test_clipboard(town_app):
    client = Client(town_app)

    login_page = client.get('/login')
    login_page.form.set('email', 'admin@example.org')
    login_page.form.set('password', 'hunter2')
    login_page.form.submit()

    page = client.get('/themen/bildung-gesellschaft')
    assert 'paste-link' not in page

    page = page.click(
        'Kopieren',
        extra_environ={'HTTP_REFERER': page.request.url}
    ).follow()

    assert 'paste-link' in page

    page = page.click('Einf').form.submit().follow()
    assert '/bildung-gesellschaft/bildung-gesellschaft' in page.request.url


def test_clipboard_separation(town_app):
    client = Client(town_app)

    login_page = client.get('/login')
    login_page.form.set('email', 'admin@example.org')
    login_page.form.set('password', 'hunter2')
    login_page.form.submit()

    page = client.get('/themen/bildung-gesellschaft')
    page = page.click('Kopieren')

    assert 'paste-link' in client.get('/themen/bildung-gesellschaft')

    # new client (browser) -> new clipboard
    client = Client(town_app)

    login_page = client.get('/login')
    login_page.form.set('email', 'admin@example.org')
    login_page.form.set('password', 'hunter2')
    login_page.form.submit()

    assert 'paste-link' not in client.get('/themen/bildung-gesellschaft')


def test_copy_pages_to_news(town_app):
    client = Client(town_app)

    login_page = client.get('/login')
    login_page.form.set('email', 'admin@example.org')
    login_page.form.set('password', 'hunter2')
    login_page.form.submit()

    page = client.get('/themen/bildung-gesellschaft')
    edit = page.click('Bearbeiten')

    edit.form['lead'] = '0xdeadbeef'
    page = edit.form.submit().follow()

    page.click('Kopieren')

    edit = client.get('/aktuelles').click('Einf')

    assert '0xdeadbeef' in edit
    page = edit.form.submit().follow()

    assert '/aktuelles/bildung-gesellschaft' in page.request.url


def test_sitecollection(town_app):
    client = Client(town_app)

    assert client.get('/sitecollection', expect_errors=True).status_code == 403

    login_page = client.get('/login')
    login_page.form.set('email', 'admin@example.org')
    login_page.form.set('password', 'hunter2')
    login_page.form.submit()

    collection = client.get('/sitecollection').json

    assert collection[0] == {
        'name': 'Bildung & Gesellschaft',
        'url': 'http://localhost/themen/bildung-gesellschaft',
        'group': 'Themen'
    }


def test_allocations(town_app):
    client = Client(town_app)

    login_page = client.get('/login')
    login_page.form.set('email', 'admin@example.org')
    login_page.form.set('password', 'hunter2')
    login_page.form.submit()

    # create a new daypass allocation
    new = client.get((
        '/ressource/sbb-tageskarte/neue-einteilung'
        '?start=2015-08-04&end=2015-08-05'
    ))

    new.form['daypasses'] = 1
    new.form['daypasses_limit'] = 1
    new.form.submit()

    # view the daypasses
    slots = client.get((
        '/ressource/sbb-tageskarte/slots'
        '?start=2015-08-04&end=2015-08-05'
    ))

    assert len(slots.json) == 2
    assert slots.json[0]['title'] == u"Ganztägig\nVerfügbar"

    # change the daypasses
    edit = client.get(extract_href(slots.json[0]['actions'][1]))
    edit.form['daypasses'] = 2
    edit.form.submit()

    slots = client.get((
        '/ressource/sbb-tageskarte/slots'
        '?start=2015-08-04&end=2015-08-04'
    ))

    assert len(slots.json) == 1
    assert slots.json[0]['title'] == u"Ganztägig\n2/2 Verfügbar"

    # try to create a new allocation over an existing one
    new = client.get((
        '/ressource/sbb-tageskarte/neue-einteilung'
        '?start=2015-08-04&end=2015-08-04'
    ))

    new.form['daypasses'] = 1
    new.form['daypasses_limit'] = 1
    new = new.form.submit()

    assert u"Es besteht bereits eine Einteilung im gewünschten Zeitraum" in new

    # move the existing allocations
    slots = client.get((
        '/ressource/sbb-tageskarte/slots'
        '?start=2015-08-04&end=2015-08-05'
    ))

    edit = client.get(extract_href(slots.json[0]['actions'][1]))
    edit.form['date'] = '2015-08-06'
    edit.form.submit()

    edit = client.get(extract_href(slots.json[1]['actions'][1]))
    edit.form['date'] = '2015-08-07'
    edit.form.submit()

    # get the new slots
    slots = client.get((
        '/ressource/sbb-tageskarte/slots'
        '?start=2015-08-06&end=2015-08-07'
    ))

    assert len(slots.json) == 2

    # delete an allocation
    client.delete(extract_href(slots.json[0]['actions'][3]))

    # get the new slots
    slots = client.get((
        '/ressource/sbb-tageskarte/slots'
        '?start=2015-08-06&end=2015-08-07'
    ))

    assert len(slots.json) == 1

    # delete an allocation
    client.delete(extract_href(slots.json[0]['actions'][3]))

    # get the new slots
    slots = client.get((
        '/ressource/sbb-tageskarte/slots'
        '?start=2015-08-06&end=2015-08-07'
    ))

    assert len(slots.json) == 0


def test_allocation_times(town_app):
    client = Client(town_app)

    login_page = client.get('/login')
    login_page.form.set('email', 'admin@example.org')
    login_page.form.set('password', 'hunter2')
    login_page.form.submit()

    new = client.get('/ressourcen').click('Raum')
    new.form['title'] = 'Meeting Room'
    new.form.submit()

    # 12:00 - 24:00
    new = client.get('/ressource/meeting-room/neue-einteilung')
    new.form['start'] = '2015-08-20'
    new.form['end'] = '2015-08-20'
    new.form['start_time'] = '12:00'
    new.form['end_time'] = '24:00'
    new.form['as_whole_day'] = 'no'
    new.form.submit()

    slots = client.get(
        '/ressource/meeting-room/slots?start=2015-08-20&end=2015-08-20'
    )

    assert len(slots.json) == 1
    assert slots.json[0]['start'] == '2015-08-20T12:00:00+02:00'
    assert slots.json[0]['end'] == '2015-08-21T00:00:00+02:00'

    # 00:00 - 02:00
    new = client.get('/ressource/meeting-room/neue-einteilung')
    new.form['start'] = '2015-08-22'
    new.form['end'] = '2015-08-22'
    new.form['start_time'] = '00:00'
    new.form['end_time'] = '02:00'
    new.form['as_whole_day'] = 'no'
    new.form.submit()

    slots = client.get(
        '/ressource/meeting-room/slots?start=2015-08-22&end=2015-08-22'
    )

    assert len(slots.json) == 1
    assert slots.json[0]['start'] == '2015-08-22T00:00:00+02:00'
    assert slots.json[0]['end'] == '2015-08-22T02:00:00+02:00'

    # 12:00 - 24:00 over two days
    new = client.get('/ressource/meeting-room/neue-einteilung')
    new.form['start'] = '2015-08-24'
    new.form['end'] = '2015-08-25'
    new.form['start_time'] = '12:00'
    new.form['end_time'] = '24:00'
    new.form['as_whole_day'] = 'no'
    new.form.submit()

    slots = client.get(
        '/ressource/meeting-room/slots?start=2015-08-24&end=2015-08-25'
    )

    assert len(slots.json) == 2
    assert slots.json[0]['start'] == '2015-08-24T12:00:00+02:00'
    assert slots.json[0]['end'] == '2015-08-25T00:00:00+02:00'
    assert slots.json[1]['start'] == '2015-08-25T12:00:00+02:00'
    assert slots.json[1]['end'] == '2015-08-26T00:00:00+02:00'


def test_reserve_allocation(town_app):

    client = Client(town_app)

    # prepate the required data
    resources = ResourceCollection(town_app.libres_context)
    resource = resources.by_name('sbb-tageskarte')
    resource.definition = 'Note = ___'
    scheduler = resource.get_scheduler(town_app.libres_context)

    allocations = scheduler.allocate(
        dates=(datetime(2015, 8, 28), datetime(2015, 8, 28)),
        whole_day=True,
        quota=4,
        quota_limit=4
    )
    reserve_url = '/einteilung/{}/{}/reservieren'.format(
        allocations[0].resource,
        allocations[0].id
    )

    transaction.commit()

    # create a reservation
    reserve = client.get(reserve_url)
    reserve.form['e_mail'] = 'info@example.org'
    reserve.form['quota'] = 4

    details = reserve.form.submit().follow()
    details.form['note'] = 'Foobar'

    ticket = details.form.submit().follow().follow()

    assert 'RSV-' in ticket.text
    assert len(town_app.smtpserver.outbox) == 1

    # try to create another reservation the same time
    reserve = client.get(reserve_url)
    reserve.form['e_mail'] = 'info@example.org'
    result = reserve.form.submit()

    assert u"Der gewünschte Zeitraum ist nicht mehr verfügbar." in result

    # try deleting the allocation with the existing reservation
    login_page = client.get('/login')
    login_page.form.set('email', 'admin@example.org')
    login_page.form.set('password', 'hunter2')
    login_page.form.submit()

    slots = client.get((
        '/ressource/sbb-tageskarte/slots'
        '?start=2015-08-28&end=2015-08-28'
    ))

    assert len(slots.json) == 1

    with pytest.raises(AffectedReservationError):
        client.delete(extract_href(slots.json[0]['actions'][3]))

    # open the created ticket
    ticket = client.get('/tickets/ALL/open').click('Annehmen').follow()

    assert 'Foobar' in ticket
    assert '28.08.2015' in ticket
    assert '4' in ticket

    # accept it
    assert 'Reservation annehmen' in ticket
    ticket = ticket.click('Reservation annehmen').follow()

    assert 'Reservation annehmen' not in ticket
    assert len(town_app.smtpserver.outbox) == 2

    message = town_app.smtpserver.outbox[1]
    message = message.get_payload(0).get_payload(decode=True)
    message = message.decode('iso-8859-1')

    assert 'SBB-Tageskarte' in message
    assert '28.08.2015' in message
    assert '4' in message

    # edit its details
    details = ticket.click('Details bearbeiten')
    details.form['note'] = '0xdeadbeef'
    ticket = details.form.submit().follow()

    assert '0xdeadbeef' in ticket

    # reject it
    assert town_app.session().query(Reservation).count() == 1
    assert town_app.session().query(FormSubmission).count() == 1

    link = ticket.pyquery('a.delete-link')[0].attrib['ic-get-from']
    ticket = client.get(link).follow()

    assert town_app.session().query(Reservation).count() == 0
    assert town_app.session().query(FormSubmission).count() == 0

    assert u"Der hinterlegte Datensatz wurde entfernt" in ticket
    assert '28.08.2015' in ticket
    assert '4' in ticket
    assert '0xdeadbeef' in ticket

    assert len(town_app.smtpserver.outbox) == 3

    message = town_app.smtpserver.outbox[2]
    message = message.get_payload(0).get_payload(decode=True)
    message = message.decode('iso-8859-1')

    assert 'SBB-Tageskarte' in message
    assert '28.08.2015' in message
    assert '4' in message

    # close the ticket
    ticket.click('Ticket abschliessen')

    assert len(town_app.smtpserver.outbox) == 4


def test_reserve_no_definition(town_app):

    client = Client(town_app)

    # prepate the required data
    resources = ResourceCollection(town_app.libres_context)
    resource = resources.by_name('sbb-tageskarte')
    scheduler = resource.get_scheduler(town_app.libres_context)

    allocations = scheduler.allocate(
        dates=(datetime(2015, 8, 28), datetime(2015, 8, 28)),
        whole_day=True,
        quota=4,
        quota_limit=4
    )
    reserve_url = '/einteilung/{}/{}/reservieren'.format(
        allocations[0].resource,
        allocations[0].id
    )

    transaction.commit()

    # create a reservation
    reserve = client.get(reserve_url)
    reserve.form['e_mail'] = 'info@example.org'
    reserve.form['quota'] = 4

    ticket = reserve.form.submit().follow().follow()

    assert 'RSV-' in ticket.text
    assert len(town_app.smtpserver.outbox) == 1


def test_reserve_session_bound(town_app):

    client = Client(town_app)

    # prepate the required data
    resources = ResourceCollection(town_app.libres_context)
    resource = resources.by_name('sbb-tageskarte')
    scheduler = resource.get_scheduler(town_app.libres_context)

    allocations = scheduler.allocate(
        dates=(datetime(2015, 8, 28), datetime(2015, 8, 28)),
        whole_day=True,
        quota=4,
        quota_limit=4
    )
    reserve_url = '/einteilung/{}/{}/reservieren'.format(
        allocations[0].resource,
        allocations[0].id
    )

    transaction.commit()

    # create a reservation
    reserve = client.get(reserve_url)
    reserve.form['e_mail'] = 'info@example.org'
    reserve.form['quota'] = 4

    finalize = reserve.form.submit()

    # make sure the finalize step can only be called by the original client
    c2 = Client(town_app)

    assert c2.get(finalize.location, expect_errors=True).status_code == 403
    assert client.get(finalize.location).follow().status_code == 200


def test_two_parallel_reservations(town_app):

    # prepate the required data
    resources = ResourceCollection(town_app.libres_context)
    resource = resources.by_name('sbb-tageskarte')
    scheduler = resource.get_scheduler(town_app.libres_context)

    allocations = scheduler.allocate(
        dates=(datetime(2015, 8, 28), datetime(2015, 8, 28)),
        whole_day=True
    )
    reserve_url = '/einteilung/{}/{}/reservieren'.format(
        allocations[0].resource,
        allocations[0].id
    )

    transaction.commit()

    # create a reservation
    c1 = Client(town_app)
    reserve = c1.get(reserve_url)
    reserve.form['e_mail'] = 'info@example.org'

    f1 = reserve.form.submit()

    # make sure the finalize step can only be called by the original client
    c2 = Client(town_app)
    reserve = c2.get(reserve_url)
    reserve.form['e_mail'] = 'info@example.org'

    f2 = reserve.form.submit()

    # one will win, one will lose
    assert f1.follow().status_code == 302
    assert u"Der gewünschte Zeitraum ist nicht mehr verfügbar." in f2.follow()


def test_cleanup_allocations(town_app):

    # prepate the required data
    resources = ResourceCollection(town_app.libres_context)
    resource = resources.by_name('sbb-tageskarte')
    scheduler = resource.get_scheduler(town_app.libres_context)

    allocations = scheduler.allocate(
        dates=(
            datetime(2015, 8, 28), datetime(2015, 8, 28),
            datetime(2015, 8, 29), datetime(2015, 8, 29)
        ),
        whole_day=True
    )
    scheduler.reserve(
        'info@example.org', (allocations[0]._start, allocations[0]._end))

    transaction.commit()

    # clean up the data
    client = Client(town_app)

    login_page = client.get('/login')
    login_page.form.set('email', 'admin@example.org')
    login_page.form.set('password', 'hunter2')
    login_page.form.submit()

    cleanup = client.get('/ressource/sbb-tageskarte').click(u"Aufräumen")
    cleanup.form['start'] = date(2015, 8, 31)
    cleanup.form['end'] = date(2015, 8, 1)
    cleanup = cleanup.form.submit()

    assert u"Das End-Datum muss nach dem Start-Datum liegen" in cleanup

    cleanup.form['start'] = date(2015, 8, 1)
    cleanup.form['end'] = date(2015, 8, 31)
    resource = cleanup.form.submit().follow()

    assert u"1 Einteilungen wurden erfolgreich entfernt" in resource


def test_view_occurrences_on_startpage(town_app):
    client = Client(town_app)
    links = [
        a.text for a in client.get('/').pyquery('.homepage-links-panel li a')
    ]
    events = (
        '150 Jahre Govikon',
        'Alle Veranstaltungen',
        'Gemeindeversammlung',
        'MuKi Turnen',
    )
    assert set(events) <= set(links)


def test_view_occurrences(town_app):
    client = Client(town_app)

    def events(query=''):
        page = client.get('/veranstaltungen/?{}'.format(query))
        return [event.text for event in page.pyquery('h2 a')]

    def total_events(query=''):
        page = client.get('/veranstaltungen/?{}'.format(query))
        return int(page.pyquery('.occurrences-filter-result span')[0].text)

    def dates(query=''):
        page = client.get('/veranstaltungen/?{}'.format(query))
        return [datetime.strptime(div.text, '%d.%m.%Y').date() for div
                in page.pyquery('.occurrence-date')]

    def tags(query=''):
        page = client.get('/veranstaltungen/?{}'.format(query))
        tags = [tag.text.strip() for tag in page.pyquery('.occurrence-tag')]
        return list(set([tag for tag in tags if tag]))

    assert total_events() == 12
    assert len(events()) == 10
    assert total_events('page=1') == 12
    assert len(events('page=1')) == 2
    assert dates() == sorted(dates())

    query = 'tags=Party'
    assert tags(query) == ["Party"]
    assert total_events(query) == 1
    assert events(query) == ["150 Jahre Govikon"]

    query = 'tags=Politics'
    assert tags(query) == ["Politik"]
    assert total_events(query) == 1
    assert events(query) == ["Gemeindeversammlung"]

    query = 'tags=Sports'
    assert tags(query) == ["Sport"]
    assert total_events(query) == 10
    assert set(events(query)) == set(["MuKi Turnen", u"Grümpelturnier"])

    query = 'tags=Politics&tags=Party'
    assert sorted(tags(query)) == ["Party", "Politik"]
    assert total_events(query) == 2
    assert set(events(query)) == set(["150 Jahre Govikon",
                                      "Gemeindeversammlung"])

    unique_dates = sorted(set(dates()))

    query = 'start={}'.format(unique_dates[1].isoformat())
    assert unique_dates[0] not in dates(query)

    query = 'end={}'.format(unique_dates[-2].isoformat())
    assert unique_dates[-1] not in dates(query)

    query = 'start={}&end={}'.format(unique_dates[1].isoformat(),
                                     unique_dates[-2].isoformat())
    assert unique_dates[0] not in dates(query)

    query = 'start={}&end={}'.format(unique_dates[1].isoformat(),
                                     unique_dates[-2].isoformat())
    assert unique_dates[-1] not in dates(query)

    query = 'start={}&end={}&tags=Sports'.format(
        unique_dates[1].isoformat(),
        unique_dates[-2].isoformat()
    )

    assert tags(query) == ["Sport"]
    assert min(dates(query)) == unique_dates[1]
    assert max(dates(query)) == unique_dates[-2]


def test_view_occurrence(town_app):
    client = Client(town_app)
    events = client.get('/veranstaltungen')

    event = events.click("Gemeindeversammlung")
    assert event.pyquery('h1.main-title').text() == "Gemeindeversammlung"
    assert "Gemeindesaal" in event
    assert "Politik" in event
    assert "Lorem ipsum." in event
    assert len(event.pyquery('.occurrence-occurrences li')) == 1
    assert len(event.pyquery('.occurrence-exports h2')) == 1
    assert event.click('Diesen Termin exportieren').text.startswith(
        'BEGIN:VCALENDAR'
    )

    event = events.click("MuKi Turnen", index=0)
    assert event.pyquery('h1.main-title').text() == "MuKi Turnen"
    assert "Turnhalle" in event
    assert "Politik" in event
    assert "Lorem ipsum." in event
    assert len(event.pyquery('.occurrence-occurrences li')) == 9
    assert len(event.pyquery('.occurrence-exports h2')) == 2

    event.click('Diesen Termin exportieren').text.startswith('BEGIN:VCALENDAR')
    event.click('Alle Termine exportieren').text.startswith('BEGIN:VCALENDAR')


def test_submit_event(town_app):
    client = Client(town_app)
    form_page = client.get('/veranstaltungen').click("Veranstaltung melden")

    assert "Das Formular enthält Fehler" in form_page.form.submit()

    # Fill out event
    start_date = date.today() + timedelta(days=1)
    end_date = start_date + timedelta(days=4)
    form_page.form['email'] = "test@example.org"
    form_page.form['title'] = "My Ewent"
    form_page.form['description'] = "My event is an event."
    form_page.form['location'] = "Location"
    form_page.form.set('tags', True, index=0)
    form_page.form.set('tags', True, index=1)
    form_page.form['start_date'] = start_date.isoformat()
    form_page.form['start_time'] = "18:00"
    form_page.form['end_time'] = "22:00"
    form_page.form['end_date'] = end_date.isoformat()
    form_page.form.set('weekly', True, index=0)
    form_page.form.set('weekly', True, index=1)
    form_page.form.set('weekly', True, index=2)
    form_page.form.set('weekly', True, index=3)
    form_page.form.set('weekly', True, index=4)
    form_page.form.set('weekly', True, index=5)
    form_page.form.set('weekly', True, index=6)

    preview_page = form_page.form.submit().follow()
    assert "My Ewent" in preview_page
    assert "My event is an event." in preview_page
    assert "Location" in preview_page
    assert "Ausstellung" in preview_page
    assert "Gastronomie" in preview_page
    assert "{} 18:00-22:00".format(start_date.strftime('%d.%m.%Y')) in \
        preview_page
    assert "Jeden Mo, Di, Mi, Do, Fr, Sa, So bis zum {}".format(
        end_date.strftime('%d.%m.%Y')
    ) in preview_page
    for days in range(5):
        assert (start_date + timedelta(days=days)).strftime('%d.%m.%Y') in \
            preview_page

    # Edit event
    form_page = preview_page.click("Bearbeiten")
    form_page.form['title'] = "My Event"

    preview_page = form_page.form.submit().follow()

    assert "My Ewent" not in preview_page
    assert "My Event" in preview_page

    # Submit event
    confirmation_page = preview_page.form.submit().follow()

    assert "Vielen Dank für Ihre Eingabe!" in confirmation_page
    ticket_nr = confirmation_page.pyquery('.ticket-number').text()
    assert "EVN-" in ticket_nr

    assert "My Event" not in client.get('/veranstaltungen')

    assert len(town_app.smtpserver.outbox) == 1
    message = town_app.smtpserver.outbox[0]
    assert message.get('to') == "test@example.org"
    message = message.get_payload(0).get_payload(decode=True)
    message = message.decode('utf-8')
    assert ticket_nr in message

    assert "Zugriff verweigert" in preview_page.form.submit(expect_errors=True)

    # Accept ticket
    login_page = client.get('/login')
    login_page.form.set('email', 'editor@example.org')
    login_page.form.set('password', 'hunter2')
    login_page.form.submit()

    assert client.get('/').pyquery('.ticket-count div').text()\
        == "1 Offen 0 In Bearbeitung"

    ticket_page = client.get('/tickets/ALL/open').click("Annehmen").follow()
    assert ticket_nr in ticket_page
    assert "test@example.org" in ticket_page
    assert "My Event" in ticket_page
    assert "My event is an event." in ticket_page
    assert "Location" in ticket_page
    assert "Ausstellung" in ticket_page
    assert "Gastronomie" in ticket_page
    assert "{} 18:00-22:00".format(start_date.strftime('%d.%m.%Y')) in \
        ticket_page
    assert "(Europe/Zurich)" in ticket_page
    assert "Jeden Mo, Di, Mi, Do, Fr, Sa, So bis zum {}".format(
        end_date.strftime('%d.%m.%Y')
    ) in ticket_page
    for days in range(5):
        assert (start_date + timedelta(days=days)).strftime('%d.%m.%Y') in \
            ticket_page

    # Publish event
    ticket_page = ticket_page.click("Veranstaltung annehmen").follow()

    assert "My Event" in client.get('/veranstaltungen')

    assert len(town_app.smtpserver.outbox) == 2
    message = town_app.smtpserver.outbox[1]
    assert message.get('to') == "test@example.org"
    message = message.get_payload(0).get_payload(decode=True)
    message = message.decode('utf-8')
    assert "My Event" in message
    assert "My event is an event." in message
    assert "Location" in message
    assert "Ausstellung" in message
    assert "Gastronomie" in message
    assert "{} 18:00-22:00".format(start_date.strftime('%d.%m.%Y')) in message
    for days in range(5):
        assert (start_date + timedelta(days=days)).strftime('%d.%m.%Y') in \
            message
    assert "Ihre Veranstaltung wurde angenommen" in message

    # Close ticket
    ticket_page.click("Ticket abschliessen").follow()

    assert len(town_app.smtpserver.outbox) == 3
    message = town_app.smtpserver.outbox[2]
    assert message.get('to') == "test@example.org"
    message = message.get_payload(0).get_payload(decode=True)
    message = message.decode('utf-8')
    assert ticket_nr in message


def test_edit_event(town_app):
    client = Client(town_app)

    # Submit and publish an event
    form_page = client.get('/veranstaltungen').click("Veranstaltung melden")
    event_date = date.today() + timedelta(days=1)
    form_page.form['email'] = "test@example.org"
    form_page.form['title'] = "My Ewent"
    form_page.form['location'] = "Lokation"
    form_page.form['start_date'] = event_date.isoformat()
    form_page.form['start_time'] = "18:00"
    form_page.form['end_time'] = "22:00"
    form_page.form.submit().follow().form.submit().follow()

    login_page = client.get('/login')
    login_page.form.set('email', 'editor@example.org')
    login_page.form.set('password', 'hunter2')
    login_page.form.submit()

    ticket_page = client.get('/tickets/ALL/open').click("Annehmen").follow()
    ticket_page = ticket_page.click("Veranstaltung annehmen").follow()

    assert "My Ewent" in client.get('/veranstaltungen')
    assert "Lokation" in client.get('/veranstaltungen')

    # Edit a submitted event
    event_page = client.get('/veranstaltungen').click("My Ewent")
    event_page = event_page.click("Bearbeiten")
    event_page.form['title'] = "My Event"
    event_page.form.submit().follow()

    assert "My Ewent" not in client.get('/veranstaltungen')
    assert "My Event" in client.get('/veranstaltungen')

    # Edit a submitted event via the ticket
    event_page = ticket_page.click("Veranstaltung bearbeiten")
    event_page.form['location'] = "Location"
    event_page.form.submit().follow()

    assert "Lokation" not in client.get('/veranstaltungen')
    assert "Location" in client.get('/veranstaltungen')

    # Edit a non-submitted event
    event_page = client.get('/veranstaltungen').click("150 Jahre Govikon")
    event_page = event_page.click("Bearbeiten")
    event_page.form['title'] = "Stadtfest"
    event_page.form.submit().follow()

    assert "150 Jahre Govikon" not in client.get('/veranstaltungen')
    assert "Stadtfest" in client.get('/veranstaltungen')


def test_delete_event(town_app):
    client = Client(town_app)

    # Submit and publish an event
    form_page = client.get('/veranstaltungen').click("Veranstaltung melden")
    event_date = date.today() + timedelta(days=1)
    form_page.form['email'] = "test@example.org"
    form_page.form['title'] = "My Event"
    form_page.form['start_date'] = event_date.isoformat()
    form_page.form['start_time'] = "18:00"
    form_page.form['end_time'] = "22:00"
    form_page.form.submit().follow().form.submit().follow()

    login_page = client.get('/login')
    login_page.form.set('email', 'editor@example.org')
    login_page.form.set('password', 'hunter2')
    login_page.form.submit()

    ticket_page = client.get('/tickets/ALL/open').click("Annehmen").follow()
    ticket_page = ticket_page.click("Veranstaltung annehmen").follow()

    assert "My Event" in client.get('/veranstaltungen')

    # Try to delete a submitted event directly
    event_page = client.get('/veranstaltungen').click("My Event")

    assert u"Diese Veranstaltung kann nicht gelöscht werden." in \
        event_page.pyquery('a.delete-link')[0].values()

    # Delete the event via the ticket
    delete_link = ticket_page.pyquery('a.delete-link').attr('ic-delete-from')
    client.delete(delete_link)

    assert len(town_app.smtpserver.outbox) == 3
    message = town_app.smtpserver.outbox[2]
    assert message.get('to') == "test@example.org"
    message = message.get_payload(0).get_payload(decode=True)
    message = message.decode('utf-8')
    assert "My Event" in message
    assert "Ihre Veranstaltung musste leider abgelehnt werden" in message

    assert "My Event" not in client.get('/veranstaltungen')

    # Delete a non-submitted event
    event_page = client.get('/veranstaltungen').click("Gemeindeversammlung")
    assert u"Möchten Sie die Veranstaltung wirklich löschen?" in \
        event_page.pyquery('a.delete-link')[0].values()

    delete_link = event_page.pyquery('a.delete-link').attr('ic-delete-from')
    client.delete(delete_link)

    assert "Gemeindeversammlung" not in client.get('/veranstaltungen')


def test_basic_search(es_town_app):
    client = Client(es_town_app)

    login_page = client.get('/login')
    login_page.form['email'] = 'admin@example.org'
    login_page.form['password'] = 'hunter2'
    login_page.form.submit().follow()

    add_news = client.get('/aktuelles').click('Nachricht')
    add_news.form['title'] = "Now supporting fulltext search"
    add_news.form['lead'] = "It is pretty awesome"
    add_news.form['text'] = "Much <em>wow</em>"
    news = add_news.form.submit().follow()

    es_town_app.es_client.indices.refresh(index='_all')

    root_page = client.get('/')
    root_page.form['q'] = "fulltext"

    search_page = root_page.form.submit()
    assert "fulltext" in search_page
    assert "Now supporting fulltext search" in search_page
    assert "It is pretty awesome" in search_page

    search_page.form['q'] = "wow"
    search_page = search_page.form.submit()
    assert "fulltext" in search_page
    assert "Now supporting fulltext search" in search_page
    assert "It is pretty awesome" in search_page

    # make sure anonymous doesn't see hidden things in the search results
    assert "fulltext" in Client(es_town_app).get('/suche?q=fulltext')
    edit_news = news.click("Bearbeiten")
    edit_news.form['is_hidden_from_public'] = True
    edit_news.form.submit()

    es_town_app.es_client.indices.refresh(index='_all')

    assert "Now supporting" not in Client(es_town_app).get('/suche?q=fulltext')
    assert "Now supporting" in client.get('/suche?q=fulltext')


def test_basic_autocomplete(es_town_app):
    client = Client(es_town_app)

    login_page = client.get('/login')
    login_page.form.set('email', 'editor@example.org')
    login_page.form.set('password', 'hunter2')
    login_page.form.submit()

    people = client.get('/personen')

    new_person = people.click('Person')
    new_person.form['first_name'] = 'Flash'
    new_person.form['last_name'] = 'Gordon'
    new_person.form.submit()

    es_town_app.es_client.indices.refresh(index='_all')
    assert client.get('/suche/suggest?q=Fl').json == ["Flash Gordon"]
    assert client.get('/suche/suggest?q=Go').json == []
