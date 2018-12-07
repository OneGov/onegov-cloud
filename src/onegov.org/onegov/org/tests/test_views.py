import babel.dates
import onegov.core
import onegov.org
import pytest
import re
import requests_mock
import textwrap
import transaction
import vcr

from base64 import b64decode, b64encode
from datetime import datetime, date, timedelta
from freezegun import freeze_time
from libres.modules.errors import AffectedReservationError
from lxml.html import document_fromstring
from onegov.core.custom import json
from onegov.core.utils import Bunch
from onegov.core.utils import module_path
from onegov.directory import DirectoryEntry
from onegov.file import FileCollection
from onegov.form import FormCollection, FormSubmission
from onegov.gis import Coordinates
from onegov.newsletter import RecipientCollection, NewsletterCollection
from onegov.page import PageCollection
from onegov.pay import PaymentProviderCollection
from onegov.people import Person
from onegov.reservation import ResourceCollection, Reservation
from onegov.ticket import TicketCollection
from onegov.user import UserCollection
from onegov_testing import utils
from purl import URL
from sedate import replace_timezone
from unittest.mock import patch
from webtest import Upload
from yubico_client import Yubico


def encode_map_value(dictionary):
    return b64encode(json.dumps(dictionary).encode('utf-8'))


def decode_map_value(value):
    return json.loads(b64decode(value).decode('utf-8'))


def test_view_permissions():
    utils.assert_explicit_permissions(onegov.org, onegov.org.OrgApp)


def test_view_form_alert(client):
    login = client.get('/auth/login').form.submit()
    assert 'Das Formular enthält Fehler' in login


def test_view_login(client):
    assert client.get('/auth/logout', expect_errors=True).status_code == 403

    response = client.get('/auth/login')

    # German is the default translation and there's no English translation yet
    # (the default *is* English, but it needs to be added as a locale, or it
    # won't be used)
    assert response.status_code == 200
    assert "E-Mail Adresse" in response
    assert "Passwort" in response

    assert client.get('/auth/logout', expect_errors=True).status_code == 403

    response.form.set('username', 'admin@example.org')
    response = response.form.submit()
    assert response.status_code == 200
    assert "E-Mail Adresse" in response
    assert "Passwort" in response
    assert "Dieses Feld wird benötigt." in response
    assert client.get('/auth/logout', expect_errors=True).status_code == 403

    response.form.set('username', 'admin@example.org')
    response.form.set('password', 'hunter2')
    response = response.form.submit()

    assert response.status_code == 302
    assert client.logout().status_code == 302
    assert client.get('/auth/logout', expect_errors=True).status_code == 403


def test_view_files(client):
    assert client.get('/files', expect_errors=True).status_code == 403

    client.login_admin()

    files_page = client.get('/files')

    assert "Noch keine Dateien hochgeladen" in files_page

    files_page.form['file'] = Upload('Test.txt', b'File content.')
    files_page.form.submit()

    files_page = client.get('/files')
    assert "Noch keine Dateien hochgeladen" not in files_page
    assert 'Test.txt' in files_page


def test_view_images(client):
    assert client.get('/images', expect_errors=True).status_code == 403

    client.login_admin()

    images_page = client.get('/images')

    assert "Noch keine Bilder hochgeladen" in images_page

    images_page.form['file'] = Upload('Test.txt', b'File content')
    assert images_page.form.submit(expect_errors=True).status_code == 415

    images_page.form['file'] = Upload('Test.jpg', utils.create_image().read())
    images_page.form.submit()

    images_page = client.get('/images')
    assert "Noch keine Bilder hochgeladen" not in images_page


def test_login(client):
    links = client.get('/').pyquery('.globals a.login')
    assert links.text() == 'Login'

    login_page = client.get(links.attr('href'))
    login_page.form['username'] = 'admin@example.org'
    login_page.form['password'] = ''
    login_page = login_page.form.submit()

    assert "Dieses Feld wird benötigt" in login_page.text

    login_page.form['username'] = 'admin@example.org'
    login_page.form['password'] = 'wrong'
    login_page = login_page.form.submit()

    assert "Falsche E-Mail Adresse, falsches Passwort oder falscher Yubikey."\
        in login_page.text

    login_page.form['username'] = 'admin@example.org'
    login_page.form['password'] = 'hunter2'

    index_page = login_page.form.submit().follow()
    assert "Sie wurden eingeloggt" in index_page.text

    links = index_page.pyquery('.globals a.logout')
    assert links.text() == 'Logout'

    index_page = client.get(links.attr('href')).follow()
    links = index_page.pyquery('.globals a.login')
    assert links.text() == 'Login'


def test_reset_password(client):
    links = client.get('/').pyquery('.globals a.login')
    assert links.text() == 'Login'
    login_page = client.get(links.attr('href'))

    request_page = login_page.click('Passwort zurücksetzen')
    assert 'Passwort zurücksetzen' in request_page.text

    request_page.form['email'] = 'someone@example.org'
    assert 'someone@example.org' in request_page.form.submit().follow()
    assert len(client.app.smtp.outbox) == 0

    request_page.form['email'] = 'admin@example.org'
    assert 'admin@example.org' in request_page.form.submit().follow()
    assert len(client.app.smtp.outbox) == 1

    message = client.app.smtp.outbox[0]
    message = message.get_payload(1).get_payload(decode=True)
    message = message.decode('iso-8859-1')
    link = list(document_fromstring(message).iterlinks())[0][2]
    token = link.split('token=')[1]

    reset_page = client.get(link)
    assert token in reset_page.text

    reset_page.form['email'] = 'someone_else@example.org'
    reset_page.form['password'] = 'new_password'
    reset_page = reset_page.form.submit()
    assert "Ungültige Addresse oder abgelaufener Link" in reset_page.text
    assert token in reset_page.text

    reset_page.form['email'] = 'admin@example.org'
    reset_page.form['password'] = '1234'
    reset_page = reset_page.form.submit()
    assert "Feld muss mindestens 8 Zeichen beinhalten" in reset_page.text
    assert token in reset_page.text

    reset_page.form['email'] = 'admin@example.org'
    reset_page.form['password'] = 'new_password'
    homepage = reset_page.form.submit().follow().text
    assert "Passwort geändert" in homepage
    assert "Login" in homepage  # do not automatically log in the user

    reset_page.form['email'] = 'admin@example.org'
    reset_page.form['password'] = 'new_password'
    reset_page = reset_page.form.submit()
    assert "Ungültige Addresse oder abgelaufener Link" in reset_page.text

    login_page.form['username'] = 'admin@example.org'
    login_page.form['password'] = 'hunter2'
    login_page = login_page.form.submit()
    assert "Falsche E-Mail Adresse, falsches Passwort oder falscher Yubikey."\
        in login_page.text

    login_page.form['username'] = 'admin@example.org'
    login_page.form['password'] = 'new_password'
    assert "Sie wurden eingeloggt" in login_page.form.submit().follow().text


def test_unauthorized(client):

    unauth_page = client.get('/settings', expect_errors=True)
    assert "Zugriff verweigert" in unauth_page.text
    assert "folgen Sie diesem Link um sich anzumelden" in unauth_page.text

    link = unauth_page.pyquery('#alternate-login-link')[0]
    login_page = client.get(link.attrib.get('href'))
    login_page.form['username'] = 'editor@example.org'
    login_page.form['password'] = 'hunter2'
    unauth_page = login_page.form.submit().follow(expect_errors=True)

    assert "Zugriff verweigert" in unauth_page.text
    assert "mit einem anderen Benutzer anzumelden" in unauth_page.text

    link = unauth_page.pyquery('#alternate-login-link')[0]
    login_page = client.get(link.attrib.get('href'))
    login_page.form['username'] = 'admin@example.org'
    login_page.form['password'] = 'hunter2'
    settings_page = login_page.form.submit().follow()

    assert settings_page.status_code == 200
    assert "Zugriff verweigert" not in settings_page


def test_notfound(client):
    notfound_page = client.get('/foobar', expect_errors=True)
    assert "Seite nicht gefunden" in notfound_page
    assert notfound_page.status_code == 404


def test_pages(client):
    root_url = client.get('/').pyquery('.top-bar-section a').attr('href')
    assert len(client.get(root_url).pyquery('.edit-bar')) == 0

    client.login_admin()
    root_page = client.get(root_url)

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
    assert page.pyquery('h2:first').text() \
        == "Living in Govikon is Really Great"
    assert page.pyquery('.page-text i').text()\
        .startswith("Experts say it's the fact")

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
    assert page.pyquery('h2:first').text() == "Living in Govikon Really Sucks"
    assert page.pyquery('.page-text i').text().startswith("Experts say hiring")
    assert "<script>alert('yes')</script>" not in page
    assert "&lt;script&gt;alert('yes')&lt;/script&gt;" in page

    client.get('/auth/logout')
    root_page = client.get(root_url)

    assert len(root_page.pyquery('.edit-bar')) == 0

    assert page.pyquery('.main-title').text() == "Living in Govikon is Awful"
    assert page.pyquery('h2:first').text() == "Living in Govikon Really Sucks"
    assert page.pyquery('.page-text i').text().startswith("Experts say hiring")


def test_news(client):
    client.login_admin().follow()

    page = client.get('/news')
    assert str(datetime.utcnow().year) not in page.text

    page = page.click('Nachricht')

    page.form['title'] = "We have a new homepage"
    page.form['lead'] = "It is very good"
    page.form['text'] = "It is lots of fun"

    page = page.form.submit().follow()

    assert "We have a new homepage" in page.text
    assert "It is very good" in page.text
    assert "It is lots of fun" in page.text
    assert str(datetime.utcnow().year) not in page.text

    page = client.get('/news')

    assert "We have a new homepage" in page.text
    assert "It is very good" in page.text
    assert "It is lots of fun" not in page.text

    # do not show the year in the news list if there's only one
    assert str(datetime.utcnow().year) not in page.text

    page = client.get('/news/we-have-a-new-homepage')

    client.delete(page.pyquery('a[ic-delete-from]').attr('ic-delete-from'))
    page = client.get('/news')

    assert "We have a new homepage" not in page.text
    assert "It is very good" not in page.text
    assert "It is lots of fun" not in page.text


def test_news_on_homepage(client):
    client.login_admin()
    anon = client.spawn()

    news_list = client.get('/news')

    page = news_list.click('Nachricht')
    page.form['title'] = "Foo"
    page.form['lead'] = "Lorem"
    page.form.submit()

    page = news_list.click('Nachricht')
    page.form['title'] = "Bar"
    page.form['lead'] = "Lorem"
    page.form.submit()

    page = news_list.click('Nachricht')
    page.form['title'] = "Baz"
    page.form['lead'] = "Lorem"
    page.form.submit()

    # only two items are shown on the homepage
    homepage = client.get('/')
    assert "Baz" in homepage
    assert "Bar" in homepage
    assert "Foo" not in homepage

    # sticky news don't count toward that limit
    foo = PageCollection(client.app.session()).by_path('news/foo')
    foo.is_visible_on_homepage = True

    transaction.commit()

    homepage = client.get('/')
    assert "Baz" in homepage
    assert "Bar" in homepage
    assert "Foo" in homepage

    # hidden news don't count for anonymous users
    baz = PageCollection(client.app.session()).by_path('news/baz')
    baz.is_hidden_from_public = True

    transaction.commit()

    homepage = anon.get('/')
    assert "Baz" not in homepage
    assert "Bar" in homepage
    assert "Foo" in homepage

    homepage = client.get('/')
    assert "Baz" in homepage
    assert "Bar" in homepage
    assert "Foo" in homepage

    # even if they are stickied
    baz = PageCollection(client.app.session()).by_path('news/baz')
    baz.is_hidden_from_public = True
    baz.is_visible_on_homepage = True

    transaction.commit()

    homepage = anon.get('/')
    assert "Baz" not in homepage
    assert "Bar" in homepage
    assert "Foo" in homepage

    homepage = client.get('/')
    assert "Baz" in homepage
    assert "Bar" in homepage
    assert "Foo" in homepage


def test_delete_pages(client):
    root_url = client.get('/').pyquery('.top-bar-section a').attr('href')

    client.login_admin()
    root_page = client.get(root_url)
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


def test_links(client):
    root_url = client.get('/').pyquery('.top-bar-section a').attr('href')
    client.login_admin()
    root_page = client.get(root_url)

    new_link = root_page.click("Verknüpfung")
    assert "Neue Verknüpfung" in new_link

    new_link.form['title'] = 'Google'
    new_link.form['url'] = 'https://www.google.ch'
    link = new_link.form.submit().follow()

    assert "Sie wurden nicht automatisch weitergeleitet" in link
    assert 'https://www.google.ch' in link

    client.get('/auth/logout')

    root_page = client.get(root_url)
    assert "Google" in root_page
    google = root_page.click("Google", index=0)

    assert google.status_code == 302
    assert google.location == 'https://www.google.ch'


def test_submit_form(client):
    collection = FormCollection(client.app.session())
    collection.definitions.add('Profile', definition=textwrap.dedent("""
        # Your Details
        First name * = ___
        Last name * = ___
        E-Mail * = @@@
    """), type='custom')

    transaction.commit()

    form_page = client.get('/forms').click('Profile')
    assert 'Your Details' in form_page
    assert 'First name' in form_page
    assert 'Last name' in form_page
    assert 'E-Mail' in form_page

    assert 'form/' in form_page.request.url
    form_page = form_page.form.submit().follow()

    assert 'form/' not in form_page.request.url
    assert 'form-preview' in form_page.request.url
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

    tickets = TicketCollection(client.app.session()).by_handler_code('FRM')
    assert len(tickets) == 1

    assert tickets[0].title == 'Kung, Fury, kung.fury@example.org'
    assert tickets[0].group == 'Profile'

    # the user should have gotten an e-mail with the entered data
    message = client.app.smtp.outbox[-1]
    message = message.get_payload(0).get_payload(decode=True)
    message = message.decode('iso-8859-1')

    assert 'Fury' in message

    # unless he opts out of it
    form_page = client.get('/forms').click('Profile')
    form_page = form_page.form.submit().follow()
    form_page.form['your_details_first_name'] = 'Kung'
    form_page.form['your_details_last_name'] = 'Fury'
    form_page.form['your_details_e_mail'] = 'kung.fury@example.org'
    form_page = form_page.form.submit()

    form_page.form.get('send_by_email', index=0).value = False
    ticket_page = form_page.form.submit().follow()

    message = client.app.smtp.outbox[-1]
    message = message.get_payload(0).get_payload(decode=True)
    message = message.decode('iso-8859-1')

    assert 'Fury' not in message


def test_pending_submission_error_file_upload(client):
    collection = FormCollection(client.app.session())
    collection.definitions.add('Statistics', definition=textwrap.dedent("""
        Name * = ___
        Datei * = *.txt|*.csv
    """), type='custom')
    transaction.commit()

    form_page = client.get('/forms').click('Statistics')
    form_page.form['datei'] = Upload('test.jpg', utils.create_image().read())

    form_page = form_page.form.submit().follow()
    assert 'form-preview' in form_page.request.url
    assert len(form_page.pyquery('small.error')) == 2


def test_pending_submission_successful_file_upload(client):
    collection = FormCollection(client.app.session())
    collection.definitions.add('Statistics', definition=textwrap.dedent("""
        Name * = ___
        Datei * = *.txt|*.csv
    """), type='custom')
    transaction.commit()

    form_page = client.get('/forms').click('Statistics')
    form_page.form['datei'] = Upload('README.txt', b'1;2;3')
    form_page = form_page.form.submit().follow()

    assert "README.txt" in form_page.text
    assert "Datei ersetzen" in form_page.text
    assert "Datei löschen" in form_page.text
    assert "Datei behalten" in form_page.text

    # unfortunately we can't test more here, as webtest doesn't support
    # multiple differing fields of the same name...


def test_add_custom_form(client):
    client.login_editor()

    # this error is not strictly line based, so there's a general error
    form_page = client.get('/forms/new')
    form_page.form['title'] = "My Form"
    form_page.form['lead'] = "This is a form"
    form_page.form['text'] = "There are many like it, but this one's mine"
    form_page.form['definition'] = "abc ="
    form_page = form_page.form.submit()

    assert "Das Formular ist nicht gültig." in form_page

    # this error is line based
    form_page = client.get('/forms/new')
    form_page.form['title'] = "My Form"
    form_page.form['lead'] = "This is a form"
    form_page.form['text'] = "There are many like it, but this one's mine"
    form_page.form['definition'] = "xxx = !!!"
    form_page = form_page.form.submit()

    assert "Der Syntax in der 1. Zeile ist ungültig." in form_page
    assert 'data-highlight-line="1"' in form_page

    form_page.form['definition'] = "Name * = ___\nE-Mail * = @@@"
    form_page = form_page.form.submit().follow()

    form_page.form['name'] = 'My name'
    form_page.form['e_mail'] = 'my@name.com'
    form_page = form_page.form.submit().follow()

    form_page = client.get('/form/my-form/edit')
    form_page.form['definition'] = "Nom * = ___\nMail * = @@@"
    form_page = form_page.form.submit().follow()

    form_page.form['nom'] = 'My name'
    form_page.form['mail'] = 'my@name.com'
    form_page.form.submit().follow()


def test_add_duplicate_form(client):
    client.login_editor()

    form_page = client.get('/forms/new')
    form_page.form['title'] = "My Form"
    form_page.form['lead'] = "This is a form"
    form_page.form['text'] = "There are many like it, but this one's mine"
    form_page.form['definition'] = "email *= @@@"
    form_page = form_page.form.submit().follow()

    assert "Ein neues Formular wurd hinzugefügt" in form_page

    form_page = client.get('/forms/new')
    form_page.form['title'] = "My Form"
    form_page.form['lead'] = "This is a form"
    form_page.form['text'] = "There are many like it, but this one's mine"
    form_page.form['definition'] = "email *= @@@"
    form_page = form_page.form.submit()

    assert "Ein Formular mit diesem Namen existiert bereits" in form_page


def test_delete_builtin_form(client):
    builtin_form = '/form/anmeldung'

    response = client.delete(builtin_form, expect_errors=True)
    assert response.status_code == 403

    client.login_editor()

    response = client.delete(builtin_form, expect_errors=True)
    assert response.status_code == 403


def test_delete_custom_form(client):
    client.login_editor()

    form_page = client.get('/forms/new')
    form_page.form['title'] = "My Form"
    form_page.form['definition'] = "e-mail * = @@@"
    form_page = form_page.form.submit().follow()

    client.delete(
        form_page.pyquery('a.delete-link')[0].attrib['ic-delete-from'])


def test_show_uploaded_file(client):
    collection = FormCollection(client.app.session())
    collection.definitions.add(
        'Text', definition="File * = *.txt\nE-Mail * = @@@", type='custom')
    transaction.commit()

    client.login_editor()

    form_page = client.get('/form/text')
    form_page.form['e_mail'] = 'info@example.org'
    form_page.form['file'] = Upload('test.txt', b'foobar')
    form_page = form_page.form.submit().follow()  # preview
    form_page = form_page.form.submit().follow()  # finalize

    ticket_page = client.get(
        form_page.pyquery('.ticket-number a').attr('href'))

    assert 'test.txt' in ticket_page.text
    file_response = ticket_page.click('test.txt', index=0)

    assert file_response.content_type == 'text/plain'
    assert file_response.text == 'foobar'

    assert file_response.cache_control.private
    assert file_response.cache_control.no_cache
    assert not file_response.cache_control.public

    assert client.spawn().get(file_response.request.url, status=404)


def test_hide_page(client):
    client.login_editor()

    new_page = client.get('/topics/organisation').click('Thema')

    new_page.form['title'] = "Test"
    new_page.form['is_hidden_from_public'] = True
    page = new_page.form.submit().follow()

    anonymous = client.spawn()
    response = anonymous.get(page.request.url, expect_errors=True)
    assert response.status_code == 403

    edit_page = page.click("Bearbeiten")
    edit_page.form['is_hidden_from_public'] = False
    page = edit_page.form.submit().follow()

    response = anonymous.get(page.request.url)
    assert response.status_code == 200


def test_hide_news(client):
    client.login_editor()

    new_page = client.get('/news').click('Nachricht')

    new_page.form['title'] = "Test"
    new_page.form['is_hidden_from_public'] = True
    page = new_page.form.submit().follow()

    anonymous = client.spawn()
    response = anonymous.get(page.request.url, expect_errors=True)
    assert response.status_code == 403

    edit_page = page.click("Bearbeiten")
    edit_page.form['is_hidden_from_public'] = False
    page = edit_page.form.submit().follow()

    response = anonymous.get(page.request.url)
    assert response.status_code == 200


def test_hide_form(client):
    client.login_editor()

    form_page = client.get('/form/anmeldung/edit')
    form_page.form['is_hidden_from_public'] = True
    page = form_page.form.submit().follow()

    anonymous = client.spawn()
    response = anonymous.get(
        '/form/anmeldung', expect_errors=True)
    assert response.status_code == 403

    edit_page = page.click("Bearbeiten")
    edit_page.form['is_hidden_from_public'] = False
    page = edit_page.form.submit().follow()

    response = anonymous.get(page.request.url)
    assert response.status_code == 200


def test_people_view(client):
    client.login_admin()
    settings = client.get('/settings')
    settings.form['hidden_people_fields'] = ['academic_title', 'profession']
    settings.form.submit()
    client.logout()

    client.login_editor()

    people = client.get('/people')
    assert 'noch keine Personen' in people

    new_person = people.click('Person')
    new_person.form['academic_title'] = 'Dr.'
    new_person.form['first_name'] = 'Flash'
    new_person.form['last_name'] = 'Gordon'
    new_person.form['profession'] = 'Hero'
    person = new_person.form.submit().follow()

    assert 'Gordon Flash' in person
    assert 'Dr.' in person
    assert 'Hero' in person

    vcard = person.click('Elektronische Visitenkarte').text
    assert 'FN:Dr. Flash Gordon' in vcard
    assert 'N:Gordon;Flash;;Dr.;' in vcard

    client.logout()
    people = client.get('/people')
    assert 'Gordon Flash' in people

    person = people.click('Gordon Flash')
    assert 'Gordon Flash' in person
    assert 'Dr.' not in person
    assert 'Hero' not in person

    vcard = person.click('Elektronische Visitenkarte').text
    assert 'FN:Flash Gordon' in vcard
    assert 'N:Gordon;Flash;;;' in vcard

    client.login_editor()

    person = client.get('/people').click('Gordon Flash')
    edit_person = person.click('Bearbeiten')
    edit_person.form['first_name'] = 'Merciless'
    edit_person.form['last_name'] = 'Ming'
    person = edit_person.form.submit().follow()

    assert 'Ming Merciless' in person

    delete_link = person.pyquery('a.delete-link').attr('ic-delete-from')
    client.delete(delete_link)

    people = client.get('/people')
    assert 'noch keine Personen' in people


def test_with_people(client):
    client.login_editor()

    people = client.get('/people')

    new_person = people.click('Person')
    new_person.form['first_name'] = 'Flash'
    new_person.form['last_name'] = 'Gordon'
    new_person.form.submit()

    new_person = people.click('Person')
    new_person.form['first_name'] = 'Merciless'
    new_person.form['last_name'] = 'Ming'
    new_person.form.submit()

    new_page = client.get('/topics/organisation').click('Thema')

    assert 'Gordon Flash' in new_page
    assert 'Ming Merciless' in new_page

    gordon = client.app.session().query(Person)\
        .filter(Person.last_name == 'Gordon')\
        .one()

    ming = client.app.session().query(Person)\
        .filter(Person.last_name == 'Ming')\
        .one()

    new_page.form['title'] = 'About Flash'
    new_page.form['people_' + gordon.id.hex] = True
    new_page.form['people_' + gordon.id.hex + '_function'] = 'Astronaut'
    edit_page = new_page.form.submit().follow().click('Bearbeiten')

    assert edit_page.form['people_' + gordon.id.hex].value == 'y'
    assert edit_page.form['people_' + gordon.id.hex + '_function'].value \
        == 'Astronaut'

    assert edit_page.form['people_' + ming.id.hex].value is None
    assert edit_page.form['people_' + ming.id.hex + '_function'].value == ''


def test_delete_linked_person_issue_149(client):
    client.login_editor()

    people = client.get('/people')

    new_person = people.click('Person')
    new_person.form['first_name'] = 'Flash'
    new_person.form['last_name'] = 'Gordon'
    new_person.form.submit()

    gordon = client.app.session().query(Person)\
        .filter(Person.last_name == 'Gordon')\
        .one()

    new_page = client.get('/topics/organisation').click('Thema')
    new_page.form['title'] = 'About Flash'
    new_page.form['people_' + gordon.id.hex] = True
    new_page.form['people_' + gordon.id.hex + '_function'] = 'Astronaut'
    edit_page = new_page.form.submit().follow().click('Bearbeiten')

    person = client.get('/people').click('Gordon Flash')
    delete_link = person.pyquery('a.delete-link').attr('ic-delete-from')
    client.delete(delete_link)

    # this used to throw an error before issue 149 was fixed
    edit_page.form.submit().follow()


def test_tickets(client):

    assert client.get(
        '/tickets/ALL/open', expect_errors=True).status_code == 403

    assert len(client.get('/').pyquery(
        '.open-tickets, .pending-tickets, .closed-tickets'
    )) == 0

    client.login_editor()

    page = client.get('/')
    assert len(page.pyquery(
        '.open-tickets, .pending-tickets, .closed-tickets'
    )) == 3

    assert page.pyquery('.open-tickets').attr('data-count') == '0'
    assert page.pyquery('.pending-tickets').attr('data-count') == '0'
    assert page.pyquery('.closed-tickets').attr('data-count') == '0'

    form_page = client.get('/forms/new')
    form_page.form['title'] = "Newsletter"
    form_page.form['definition'] = "E-Mail *= @@@"
    form_page = form_page.form.submit()

    client.logout()

    form_page = client.get('/form/newsletter')
    form_page.form['e_mail'] = 'info@seantis.ch'

    assert len(client.app.smtp.outbox) == 0

    status_page = form_page.form.submit().follow().form.submit().follow()

    assert len(client.app.smtp.outbox) == 1

    message = client.app.smtp.outbox[0]
    message = message.get_payload(0).get_payload(decode=True)
    message = message.decode('iso-8859-1')

    assert 'FRM-' in message
    assert '/status' in message

    assert 'FRM-' in status_page
    assert 'Offen' in status_page

    client.login_editor()

    page = client.get('/')
    assert page.pyquery('.open-tickets').attr('data-count') == '1'
    assert page.pyquery('.pending-tickets').attr('data-count') == '0'
    assert page.pyquery('.closed-tickets').attr('data-count') == '0'

    tickets_page = client.get('/tickets/ALL/open')
    assert len(tickets_page.pyquery('tr.ticket')) == 1

    ticket_page = tickets_page.click('Annehmen').follow()
    assert len(tickets_page.pyquery('tr.ticket')) == 1

    tickets_page = client.get('/tickets/ALL/pending')
    assert len(tickets_page.pyquery('tr.ticket')) == 1

    page = client.get('/')
    assert page.pyquery('.open-tickets').attr('data-count') == '0'
    assert page.pyquery('.pending-tickets').attr('data-count') == '1'
    assert page.pyquery('.closed-tickets').attr('data-count') == '0'

    assert 'editor@example.org' in ticket_page
    assert 'Newsletter' in ticket_page
    assert 'info@seantis.ch' in ticket_page
    assert 'In Bearbeitung' in ticket_page
    assert 'FRM-' in ticket_page

    ticket_url = ticket_page.request.path
    ticket_page = ticket_page.click('Ticket abschliessen').follow()

    page = client.get('/')
    assert page.pyquery('.open-tickets').attr('data-count') == '0'
    assert page.pyquery('.pending-tickets').attr('data-count') == '0'
    assert page.pyquery('.closed-tickets').attr('data-count') == '1'

    assert len(client.app.smtp.outbox) == 2

    message = client.app.smtp.outbox[1]
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

    page = client.get('/')
    assert page.pyquery('.open-tickets').attr('data-count') == '0'
    assert page.pyquery('.pending-tickets').attr('data-count') == '1'
    assert page.pyquery('.closed-tickets').attr('data-count') == '0'

    message = client.app.smtp.outbox[2]
    message = message.get_payload(0).get_payload(decode=True)
    message = message.decode('iso-8859-1')

    assert 'FRM-' in message
    assert '/status' in message


def test_ticket_states_idempotent(client):
    client.login_editor()

    page = client.get('/forms/new')
    page.form['title'] = "Newsletter"
    page.form['definition'] = "E-Mail *= @@@"
    page = page.form.submit()

    page = client.get('/form/newsletter')
    page.form['e_mail'] = 'info@seantis.ch'

    page.form.submit().follow().form.submit().follow()
    assert len(client.app.smtp.outbox) == 1
    assert len(client.get('/timeline/feed').json['messages']) == 1

    page = client.get('/tickets/ALL/open')
    page.click('Annehmen')
    page.click('Annehmen')
    page = page.click('Annehmen').follow()
    assert len(client.app.smtp.outbox) == 1
    assert len(client.get('/timeline/feed').json['messages']) == 2

    page.click('Ticket abschliessen')
    page.click('Ticket abschliessen')
    page = page.click('Ticket abschliessen').follow()
    assert len(client.app.smtp.outbox) == 2
    assert len(client.get('/timeline/feed').json['messages']) == 3

    page = client.get(
        client.get('/tickets/ALL/closed')
        .pyquery('.ticket-number-plain a').attr('href'))

    page.click('Ticket wieder öffnen')
    page.click('Ticket wieder öffnen')
    page = page.click('Ticket wieder öffnen').follow()
    assert len(client.app.smtp.outbox) == 3
    assert len(client.get('/timeline/feed').json['messages']) == 4


def test_resource_slots(client):

    resources = ResourceCollection(client.app.libres_context)
    resource = resources.add("Foo", 'Europe/Zurich')

    scheduler = resource.get_scheduler(client.app.libres_context)
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

    url = '/resource/foo/slots'
    assert client.get(url).json == []

    url = '/resource/foo/slots?start=2015-08-04&end=2015-08-05'
    result = client.get(url).json

    assert len(result) == 2

    assert result[0]['start'] == '2015-08-04T00:00:00+02:00'
    assert result[0]['end'] == '2015-08-05T00:00:00+02:00'
    assert result[0]['className'] == 'event-available'
    assert result[0]['title'] == "Ganztägig \nVerfügbar"

    assert result[1]['start'] == '2015-08-05T00:00:00+02:00'
    assert result[1]['end'] == '2015-08-06T00:00:00+02:00'
    assert result[1]['className'] == 'event-available'
    assert result[1]['title'] == "Ganztägig \nVerfügbar"

    url = '/resource/foo/slots?start=2015-08-06&end=2015-08-06'
    result = client.get(url).json

    assert len(result) == 1
    assert result[0]['className'] == 'event-unavailable'
    assert result[0]['title'] == "12:00 - 16:00 \nBesetzt"


def test_resources(client):
    client.login_admin()

    resources = client.get('/resources')

    new = resources.click('Raum')
    new.form['title'] = 'Meeting Room'
    resource = new.form.submit().follow()

    assert 'calendar' in resource
    assert 'Meeting Room' in resource

    edit = resource.click('Bearbeiten')
    edit.form['title'] = 'Besprechungsraum'
    edit.form.submit()

    assert 'Besprechungsraum' in client.get('/resources')

    resource = client.get('/resource/meeting-room')
    delete_link = resource.pyquery('a.delete-link').attr('ic-delete-from')

    assert client.delete(delete_link, status=200)


def test_reserved_resources_fields(client):
    client.login_admin()

    room = client.get('/resources').click('Raum')
    room.form['title'] = 'Meeting Room'
    room.form['definition'] = "Email *= @@@"
    room = room.form.submit()

    assert "'Email' ist ein reservierter Name" in room

    # fieldsets act as a namespace for field names
    room.form['definition'] = "# Title\nEmail *= @@@"
    room = room.form.submit().follow()

    assert "calendar" in room
    assert "Meeting Room" in room


def test_clipboard(client):
    client.login_admin()

    page = client.get('/topics/organisation')
    assert 'paste-link' not in page

    page = page.click(
        'Kopieren',
        extra_environ={'HTTP_REFERER': page.request.url}
    ).follow()

    assert 'paste-link' in page

    page = page.click('Einf').form.submit().follow()
    assert '/organisation/organisation' in page.request.url


def test_clipboard_separation(client):
    client.login_admin()

    page = client.get('/topics/organisation')
    page = page.click('Kopieren')

    assert 'paste-link' in client.get('/topics/organisation')

    # new client (browser) -> new clipboard
    client = client.spawn()
    client.login_admin()

    assert 'paste-link' not in client.get('/topics/organisation')


def test_copy_pages_to_news(client):
    client.login_admin()

    page = client.get('/topics/organisation')
    edit = page.click('Bearbeiten')

    edit.form['lead'] = '0xdeadbeef'
    page = edit.form.submit().follow()

    page.click('Kopieren')

    edit = client.get('/news').click('Einf')

    assert '0xdeadbeef' in edit
    page = edit.form.submit().follow()

    assert '/news/organisation' in page.request.url


def test_sitecollection(client):

    assert client.get('/sitecollection', expect_errors=True).status_code == 403

    client.login_admin()

    collection = client.get('/sitecollection').json

    assert collection[0] == {
        'name': 'Kontakt',
        'url': 'http://localhost/topics/kontakt',
        'group': 'Themen'
    }


def test_allocations(client):
    client.login_admin()

    # create a new daypass allocation
    new = client.get((
        '/resource/tageskarte/new-allocation'
        '?start=2015-08-04&end=2015-08-05'
    ))

    new.form['daypasses'] = 1
    new.form['daypasses_limit'] = 1
    new.form.submit()

    # view the daypasses
    slots = client.get((
        '/resource/tageskarte/slots'
        '?start=2015-08-04&end=2015-08-05'
    ))

    assert len(slots.json) == 2
    assert slots.json[0]['title'] == "Ganztägig \nVerfügbar"

    # change the daypasses
    edit = client.get(client.extract_href(slots.json[0]['actions'][0]))
    edit.form['daypasses'] = 2
    edit.form.submit()

    slots = client.get((
        '/resource/tageskarte/slots'
        '?start=2015-08-04&end=2015-08-04'
    ))

    assert len(slots.json) == 1
    assert slots.json[0]['title'] == "Ganztägig \n2/2 Verfügbar"

    # try to create a new allocation over an existing one
    new = client.get((
        '/resource/tageskarte/new-allocation'
        '?start=2015-08-04&end=2015-08-04'
    ))

    new.form['daypasses'] = 1
    new.form['daypasses_limit'] = 1
    new = new.form.submit()

    assert "Es besteht bereits eine Einteilung im gewünschten Zeitraum" in new

    # move the existing allocations
    slots = client.get((
        '/resource/tageskarte/slots'
        '?start=2015-08-04&end=2015-08-05'
    ))

    edit = client.get(client.extract_href(slots.json[0]['actions'][0]))
    edit.form['date'] = '2015-08-06'
    edit.form.submit()

    edit = client.get(client.extract_href(slots.json[1]['actions'][0]))
    edit.form['date'] = '2015-08-07'
    edit.form.submit()

    # get the new slots
    slots = client.get((
        '/resource/tageskarte/slots'
        '?start=2015-08-06&end=2015-08-07'
    ))

    assert len(slots.json) == 2

    # delete an allocation
    client.delete(client.extract_href(slots.json[0]['actions'][2]))

    # get the new slots
    slots = client.get((
        '/resource/tageskarte/slots'
        '?start=2015-08-06&end=2015-08-07'
    ))

    assert len(slots.json) == 1

    # delete an allocation
    client.delete(client.extract_href(slots.json[0]['actions'][2]))

    # get the new slots
    slots = client.get((
        '/resource/tageskarte/slots'
        '?start=2015-08-06&end=2015-08-07'
    ))

    assert len(slots.json) == 0


def test_allocation_times(client):
    client.login_admin()

    new = client.get('/resources').click('Raum')
    new.form['title'] = 'Meeting Room'
    new.form.submit()

    # 12:00 - 00:00
    new = client.get('/resource/meeting-room/new-allocation')
    new.form['start'] = '2015-08-20'
    new.form['end'] = '2015-08-20'
    new.form['start_time'] = '12:00'
    new.form['end_time'] = '00:00'
    new.form['as_whole_day'] = 'no'
    new.form.submit()

    slots = client.get(
        '/resource/meeting-room/slots?start=2015-08-20&end=2015-08-20'
    )

    assert len(slots.json) == 1
    assert slots.json[0]['start'] == '2015-08-20T12:00:00+02:00'
    assert slots.json[0]['end'] == '2015-08-21T00:00:00+02:00'

    # 00:00 - 02:00
    new = client.get('/resource/meeting-room/new-allocation')
    new.form['start'] = '2015-08-22'
    new.form['end'] = '2015-08-22'
    new.form['start_time'] = '00:00'
    new.form['end_time'] = '02:00'
    new.form['as_whole_day'] = 'no'
    new.form.submit()

    slots = client.get(
        '/resource/meeting-room/slots?start=2015-08-22&end=2015-08-22'
    )

    assert len(slots.json) == 1
    assert slots.json[0]['start'] == '2015-08-22T00:00:00+02:00'
    assert slots.json[0]['end'] == '2015-08-22T02:00:00+02:00'

    # 12:00 - 00:00 over two days
    new = client.get('/resource/meeting-room/new-allocation')
    new.form['start'] = '2015-08-24'
    new.form['end'] = '2015-08-25'
    new.form['start_time'] = '12:00'
    new.form['end_time'] = '00:00'
    new.form['as_whole_day'] = 'no'
    new.form.submit()

    slots = client.get(
        '/resource/meeting-room/slots?start=2015-08-24&end=2015-08-25'
    )

    assert len(slots.json) == 2
    assert slots.json[0]['start'] == '2015-08-24T12:00:00+02:00'
    assert slots.json[0]['end'] == '2015-08-25T00:00:00+02:00'
    assert slots.json[1]['start'] == '2015-08-25T12:00:00+02:00'
    assert slots.json[1]['end'] == '2015-08-26T00:00:00+02:00'


def test_reserve_allocation(client):

    # prepate the required data
    resources = ResourceCollection(client.app.libres_context)
    resource = resources.by_name('tageskarte')
    resource.definition = 'Note = ___'
    scheduler = resource.get_scheduler(client.app.libres_context)

    allocations = scheduler.allocate(
        dates=(datetime(2015, 8, 28), datetime(2015, 8, 28)),
        whole_day=True,
        quota=4,
        quota_limit=4
    )

    reserve = client.bound_reserve(allocations[0])
    transaction.commit()

    # create a reservation
    result = reserve(quota=4, whole_day=True)
    assert result.json == {'success': True}
    assert result.headers['X-IC-Trigger'] == 'rc-reservations-changed'

    # and fill out the form
    formular = client.get('/resource/tageskarte/form')
    formular.form['email'] = 'info@example.org'
    formular.form['note'] = 'Foobar'

    ticket = formular.form.submit().follow().form.submit().follow()

    assert 'RSV-' in ticket.text
    assert len(client.app.smtp.outbox) == 1

    # make sure the resulting reservation has no session_id set
    ids = [r.session_id for r in scheduler.managed_reservations()]
    assert not any(ids)

    # try to create another reservation the same time
    result = reserve(quota=4, whole_day=True)
    assert result.json == {
        'success': False,
        'message': 'Der gewünschte Zeitraum ist nicht mehr verfügbar.'
    }

    assert result.headers['X-IC-Trigger'] == 'rc-reservation-error'
    assert json.loads(result.headers['X-IC-Trigger-Data']) == result.json

    # try deleting the allocation with the existing reservation
    client.login_admin()

    slots = client.get((
        '/resource/tageskarte/slots'
        '?start=2015-08-28&end=2015-08-28'
    ))

    assert len(slots.json) == 1

    with pytest.raises(AffectedReservationError):
        client.delete(client.extract_href(slots.json[0]['actions'][2]))

    # open the created ticket
    ticket = client.get('/tickets/ALL/open').click('Annehmen').follow()

    assert 'Foobar' in ticket
    assert '28. August 2015' in ticket
    assert '4' in ticket

    # accept it
    assert 'Alle Reservationen annehmen' in ticket
    ticket = ticket.click('Alle Reservationen annehmen').follow()

    assert 'Alle Reservationen annehmen' not in ticket
    assert len(client.app.smtp.outbox) == 2

    message = client.app.smtp.outbox[1]
    message = message.get_payload(0).get_payload(decode=True)
    message = message.decode('iso-8859-1')

    assert 'Tageskarte' in message
    assert '28. August 2015' in message
    assert '4' in message

    # edit its details
    details = ticket.click('Details bearbeiten')
    details.form['note'] = '0xdeadbeef'
    ticket = details.form.submit().follow()

    assert '0xdeadbeef' in ticket

    # reject it
    assert client.app.session().query(Reservation).count() == 1
    assert client.app.session().query(FormSubmission).count() == 1

    link = ticket.pyquery('a.delete-link')[0].attrib['ic-get-from']
    ticket = client.get(link).follow()

    assert client.app.session().query(Reservation).count() == 0
    assert client.app.session().query(FormSubmission).count() == 0

    assert "Der hinterlegte Datensatz wurde entfernt" in ticket
    assert '28. August 2015' in ticket
    assert '4' in ticket
    assert '0xdeadbeef' in ticket

    assert len(client.app.smtp.outbox) == 3

    message = client.app.smtp.outbox[2]
    message = message.get_payload(0).get_payload(decode=True)
    message = message.decode('iso-8859-1')

    assert 'Tageskarte' in message
    assert '28. August 2015' in message
    assert '4' in message

    # close the ticket
    ticket.click('Ticket abschliessen')

    assert len(client.app.smtp.outbox) == 4


def test_reserve_allocation_partially(client):

    # prepate the required data
    resources = ResourceCollection(client.app.libres_context)
    resource = resources.by_name('tageskarte')
    scheduler = resource.get_scheduler(client.app.libres_context)

    allocations = scheduler.allocate(
        dates=(datetime(2015, 8, 28, 10), datetime(2015, 8, 28, 14)),
        whole_day=False,
        partly_available=True
    )

    reserve = client.bound_reserve(allocations[0])
    transaction.commit()

    # create a reservation
    assert reserve('10:00', '12:00').json == {'success': True}

    # fill out the form
    formular = client.get('/resource/tageskarte/form')
    formular.form['email'] = 'info@example.org'

    ticket = formular.form.submit().follow().form.submit().follow()

    assert 'RSV-' in ticket.text
    assert len(client.app.smtp.outbox) == 1

    # open the created ticket
    client.login_admin()

    ticket = client.get('/tickets/ALL/open').click('Annehmen').follow()

    assert "info@example.org" in ticket
    assert "10:00" in ticket
    assert "12:00" in ticket

    # accept it
    ticket = ticket.click('Alle Reservationen annehmen').follow()

    message = client.app.smtp.outbox[1]
    message = message.get_payload(0).get_payload(decode=True)
    message = message.decode('iso-8859-1')

    assert "Tageskarte" in message
    assert "28. August 2015" in message
    assert "10:00" in message
    assert "12:00" in message

    # see if the slots are partitioned correctly
    url = '/resource/tageskarte/slots?start=2015-08-01&end=2015-08-30'
    slots = client.get(url).json
    assert slots[0]['partitions'] == [[50.0, True], [50.0, False]]


def test_reserve_no_definition(client):

    # prepate the required data
    resources = ResourceCollection(client.app.libres_context)
    resource = resources.by_name('tageskarte')
    scheduler = resource.get_scheduler(client.app.libres_context)

    allocations = scheduler.allocate(
        dates=(datetime(2015, 8, 28), datetime(2015, 8, 28)),
        whole_day=True,
        quota=4,
        quota_limit=4
    )

    reserve = client.bound_reserve(allocations[0])
    transaction.commit()

    # create a reservation
    result = reserve(quota=4)
    assert result.json == {'success': True}

    # fill out the reservation form
    formular = client.get('/resource/tageskarte/form')
    formular.form['email'] = 'info@example.org'

    ticket = formular.form.submit().follow().form.submit().follow()

    assert 'RSV-' in ticket.text
    assert len(client.app.smtp.outbox) == 1


def test_reserve_confirmation_no_definition(client):

    resources = ResourceCollection(client.app.libres_context)
    resource = resources.by_name('tageskarte')
    scheduler = resource.get_scheduler(client.app.libres_context)

    allocations = scheduler.allocate(
        dates=(datetime(2015, 8, 28), datetime(2015, 8, 28)),
        whole_day=True,
        quota=4,
        quota_limit=4
    )

    reserve = client.bound_reserve(allocations[0])
    transaction.commit()

    # create a reservation
    assert reserve(quota=4).json == {'success': True}

    formular = client.get('/resource/tageskarte/form')
    formular.form['email'] = "info@example.org"

    confirmation = formular.form.submit().follow()

    assert "Bestätigen Sie Ihre Reservation" in confirmation
    assert "Ganztägig" in confirmation
    assert "4" in confirmation
    assert "info@example.org" in confirmation

    formular = confirmation.click("Bearbeiten")
    assert "info@example.org" in formular
    assert "4" in formular

    formular.form['email'] = "changed@example.org"
    confirmation = formular.form.submit().follow()

    assert "Bestätigen Sie Ihre Reservation" in confirmation
    assert "Ganztägig" in confirmation
    assert "changed@example.org" in confirmation


def test_reserve_confirmation_with_definition(client):

    resources = ResourceCollection(client.app.libres_context)
    resource = resources.by_name('tageskarte')
    resource.definition = "Vorname *= ___\nNachname *= ___"

    scheduler = resource.get_scheduler(client.app.libres_context)

    allocations = scheduler.allocate(
        dates=(datetime(2015, 8, 28, 10), datetime(2015, 8, 28, 12)),
        whole_day=False,
        partly_available=True
    )
    reserve = client.bound_reserve(allocations[0])

    transaction.commit()

    # create a reservation
    assert reserve("10:30", "12:00").json == {'success': True}

    formular = client.get('/resource/tageskarte/form')
    formular.form['email'] = "info@example.org"
    formular.form['vorname'] = "Thomas"
    formular.form['nachname'] = "Anderson"

    confirmation = formular.form.submit().follow()
    assert "10:30" in confirmation
    assert "12:00" in confirmation
    assert "Thomas" in confirmation
    assert "Anderson" in confirmation

    # edit the reservation
    formular = confirmation.click("Bearbeiten")
    formular.form['vorname'] = "Elliot"
    formular.form['nachname'] = "Alderson"

    confirmation = formular.form.submit().follow()
    assert "10:30" in confirmation
    assert "12:00" in confirmation
    assert "Elliot" in confirmation
    assert "Alderson" in confirmation


def test_reserve_session_bound(client):

    # prepate the required data
    resources = ResourceCollection(client.app.libres_context)
    resource = resources.by_name('tageskarte')
    scheduler = resource.get_scheduler(client.app.libres_context)

    allocations = scheduler.allocate(
        dates=(datetime(2015, 8, 28), datetime(2015, 8, 28)),
        whole_day=True,
        quota=4,
        quota_limit=4
    )

    reserve = client.bound_reserve(allocations[0])
    transaction.commit()

    # create a reservation
    assert reserve(quota=4).json == {'success': True}

    formular = client.get('/resource/tageskarte/form')
    formular.form['email'] = 'info@example.org'

    confirm = formular.form.submit().follow()
    complete_url = confirm.pyquery('form:last').attr('action')

    # make sure the finalize step can only be called by the original client
    c2 = client.spawn()

    assert c2.post(complete_url, expect_errors=True).status_code == 403
    assert client.post(complete_url).follow().status_code == 200


def test_delete_reservation_anonymous(client):

    # prepate the required data
    resources = ResourceCollection(client.app.libres_context)
    resource = resources.by_name('tageskarte')
    scheduler = resource.get_scheduler(client.app.libres_context)

    allocations = scheduler.allocate(
        dates=(datetime(2015, 8, 28), datetime(2015, 8, 28)),
        whole_day=True,
        quota=4,
        quota_limit=4
    )

    reserve = client.bound_reserve(allocations[0])
    transaction.commit()

    # create a reservation
    assert reserve(quota=4).json == {'success': True}

    # get the delete url
    reservations_url = '/resource/tageskarte/reservations'

    reservations = client.get(reservations_url).json['reservations']
    url = reservations[0]['delete']

    # the url does not have csrf (anonymous does not)
    assert url.endswith('?csrf-token=')

    # other clients still can't use the link
    assert client.spawn().delete(url, status=403)
    assert len(client.get(reservations_url).json['reservations']) == 1

    # only the original client can
    client.delete(url)
    assert len(client.get(reservations_url).json['reservations']) == 0


def test_reserve_in_parallel(client):

    # prepate the required data
    resources = ResourceCollection(client.app.libres_context)
    resource = resources.by_name('tageskarte')
    scheduler = resource.get_scheduler(client.app.libres_context)

    allocations = scheduler.allocate(
        dates=(datetime(2015, 8, 28), datetime(2015, 8, 28)),
        whole_day=True
    )

    c1 = client.spawn()
    c2 = client.spawn()

    c1_reserve = c1.bound_reserve(allocations[0])
    c2_reserve = c2.bound_reserve(allocations[0])
    transaction.commit()

    # create a reservation
    assert c1_reserve().json == {'success': True}
    formular = c1.get('/resource/tageskarte/form')
    formular.form['email'] = 'info@example.org'
    f1 = formular.form.submit().follow()

    # create a parallel reservation
    assert c2_reserve().json == {'success': True}
    formular = c2.get('/resource/tageskarte/form')
    formular.form['email'] = 'info@example.org'
    f2 = formular.form.submit().follow()

    # one will win, one will lose
    assert f1.form.submit().status_code == 302
    assert "Der gewünschte Zeitraum ist nicht mehr verfügbar."\
        in f2.form.submit().follow()


def test_occupancy_view(client):

    # prepate the required data
    resources = ResourceCollection(client.app.libres_context)
    resource = resources.by_name('tageskarte')
    scheduler = resource.get_scheduler(client.app.libres_context)

    allocations = scheduler.allocate(
        dates=(datetime(2015, 8, 28), datetime(2015, 8, 28)),
        whole_day=True
    )

    reserve = client.bound_reserve(allocations[0])
    transaction.commit()

    client.login_admin()

    # create a reservation
    assert reserve().json == {'success': True}
    formular = client.get('/resource/tageskarte/form')
    formular.form['email'] = 'info@example.org'
    formular.form.submit().follow().form.submit()

    ticket = client.get('/tickets/ALL/open').click('Annehmen').follow()

    # at this point, the reservation won't show up in the occupancy view
    occupancy = client.get('/resource/tageskarte/occupancy?date=20150828')
    assert len(occupancy.pyquery('.occupancy-block')) == 0

    # ..until we accept it
    ticket.click('Alle Reservationen annehmen')
    occupancy = client.get('/resource/tageskarte/occupancy?date=20150828')
    assert len(occupancy.pyquery('.occupancy-block')) == 1


def test_reservation_export_view(client):

    # prepate the required data
    resources = ResourceCollection(client.app.libres_context)
    resource = resources.by_name('tageskarte')
    resource.definition = "Vorname *= ___\nNachname *= ___"

    scheduler = resource.get_scheduler(client.app.libres_context)

    allocations = scheduler.allocate(
        dates=(datetime(2015, 8, 28), datetime(2015, 8, 28)),
        whole_day=True
    )

    reserve = client.bound_reserve(allocations[0])
    transaction.commit()

    client.login_admin()

    # create a reservation
    assert reserve().json == {'success': True}
    formular = client.get('/resource/tageskarte/form')
    formular.form['email'] = 'info@example.org'
    formular.form['vorname'] = 'Charlie'
    formular.form['nachname'] = 'Carson'
    formular.form.submit().follow().form.submit()

    ticket = client.get('/tickets/ALL/open').click('Annehmen').follow()

    # at this point, the reservation won't show up in the export
    export = client.get('/resource/tageskarte/export')
    export.form['start'] = date(2015, 8, 28)
    export.form['end'] = date(2015, 8, 28)
    export.form['file_format'] = 'json'
    assert not export.form.submit().json

    # until we confirm the reservation
    ticket.click('Alle Reservationen annehmen')
    charlie = export.form.submit().json[0]

    assert charlie['email'] == 'info@example.org'
    assert charlie['title'] == 'info@example.org, Charlie, Carson'
    assert charlie['start'] == '2015-08-28T00:00:00+02:00'
    assert charlie['end'] == '2015-08-29T00:00:00+02:00'
    assert charlie['ticket'].startswith('RSV-')
    assert charlie['quota'] == 1
    assert charlie['form'] == {'vorname': 'Charlie', 'nachname': 'Carson'}


def test_reserve_session_separation(client):
    c1 = client.spawn()
    c1.login_admin()

    c2 = client.spawn()
    c2.login_admin()

    reserve = []

    # check both for separation by resource and by client
    for room in ('meeting-room', 'gym'):
        new = c1.get('/resources').click('Raum')
        new.form['title'] = room
        new.form.submit()

        resource = client.app.libres_resources.by_name(room)
        allocations = resource.scheduler.allocate(
            dates=(datetime(2016, 4, 28, 12, 0), datetime(2016, 4, 28, 13, 0)),
            whole_day=False
        )

        reserve.append(c1.bound_reserve(allocations[0]))
        reserve.append(c2.bound_reserve(allocations[0]))
        transaction.commit()

    c1_reserve_room, c2_reserve_room, c1_reserve_gym, c2_reserve_gym = reserve

    assert c1_reserve_room().json == {'success': True}
    assert c1_reserve_gym().json == {'success': True}
    assert c2_reserve_room().json == {'success': True}
    assert c2_reserve_gym().json == {'success': True}

    for room in ('meeting-room', 'gym'):
        result = c1.get('/resource/{}/reservations'.format(room)).json
        assert len(result['reservations']) == 1

        result = c2.get('/resource/{}/reservations'.format(room)).json
        assert len(result['reservations']) == 1

    formular = c1.get('/resource/meeting-room/form')
    formular.form['email'] = 'info@example.org'
    formular.form.submit()

    # make sure if we confirm one reservation, only one will be written
    formular.form.submit().follow().form.submit().follow()

    resource = client.app.libres_resources.by_name('meeting-room')
    assert resource.scheduler.managed_reserved_slots().count() == 1

    result = c1.get('/resource/meeting-room/reservations'.format(room)).json
    assert len(result['reservations']) == 0

    result = c1.get('/resource/gym/reservations'.format(room)).json
    assert len(result['reservations']) == 1

    result = c2.get('/resource/meeting-room/reservations'.format(room)).json
    assert len(result['reservations']) == 1

    result = c2.get('/resource/gym/reservations'.format(room)).json
    assert len(result['reservations']) == 1


def test_reserve_reservation_prediction(client):
    client.login_admin()

    new = client.get('/resources').click('Raum')
    new.form['title'] = 'Gym'
    new.form.submit()

    transaction.begin()

    resource = client.app.libres_resources.by_name('gym')

    a1 = resource.scheduler.allocate(
        dates=(datetime(2017, 1, 1, 12, 0), datetime(2017, 1, 1, 13, 0)),
        whole_day=False
    )[0]
    a2 = resource.scheduler.allocate(
        dates=(datetime(2017, 1, 2, 12, 0), datetime(2017, 1, 2, 13, 0)),
        whole_day=False
    )[0]

    reserve_a1 = client.bound_reserve(a1)
    reserve_a2 = client.bound_reserve(a2)

    transaction.commit()

    reserve_a1()
    reserve_a2()

    reservations_url = '/resource/gym/reservations'
    assert not client.get(reservations_url).json['prediction']

    transaction.begin()

    resource = client.app.libres_resources.by_name('gym')
    a3 = resource.scheduler.allocate(
        dates=(datetime(2017, 1, 3, 12, 0), datetime(2017, 1, 3, 13, 0)),
        whole_day=False
    )[0]
    resource.scheduler.allocate(
        dates=(datetime(2017, 1, 4, 12, 0), datetime(2017, 1, 4, 13, 0)),
        whole_day=False
    )

    reserve_a3 = client.bound_reserve(a3)
    transaction.commit()

    reserve_a3()

    prediction = client.get(reservations_url).json['prediction']

    assert prediction['start'] == '2017-01-04T12:00:00+01:00'
    assert prediction['end'] == '2017-01-04T13:00:00+01:00'
    assert prediction['quota'] == 1
    assert prediction['time'] == '12:00 - 13:00'
    assert prediction['url'].endswith('/reserve')
    assert prediction['wholeDay'] is False


def test_reserve_multiple_allocations(client):
    client.login_admin()

    transaction.begin()

    resource = client.app.libres_resources.by_name('tageskarte')
    thursday = resource.scheduler.allocate(
        dates=(datetime(2016, 4, 28), datetime(2016, 4, 28)),
        whole_day=True
    )[0]
    friday = resource.scheduler.allocate(
        dates=(datetime(2016, 4, 29), datetime(2016, 4, 29)),
        whole_day=True
    )[0]

    reserve_thursday = client.bound_reserve(thursday)
    reserve_friday = client.bound_reserve(friday)

    transaction.commit()

    assert reserve_thursday().json == {'success': True}
    assert reserve_friday().json == {'success': True}

    formular = client.get('/resource/tageskarte/form')
    assert "28. April 2016" in formular
    assert "29. April 2016" in formular
    formular.form['email'] = "info@example.org"

    confirmation = formular.form.submit().follow()
    assert "28. April 2016" in confirmation
    assert "29. April 2016" in confirmation

    ticket = confirmation.form.submit().follow()
    assert 'RSV-' in ticket.text
    assert len(client.app.smtp.outbox) == 1

    ticket = client.get('/tickets/ALL/open').click('Annehmen').follow()
    assert "info@example.org" in ticket
    assert "28. April 2016" in ticket
    assert "29. April 2016" in ticket

    # accept it
    ticket.click('Alle Reservationen annehmen')

    message = client.app.smtp.outbox[1]
    message = message.get_payload(0).get_payload(decode=True)
    message = message.decode('iso-8859-1')

    assert "Tageskarte" in message
    assert "28. April 2016" in message
    assert "29. April 2016" in message

    # make sure the reservations are no longer pending
    resource = client.app.libres_resources.by_name('tageskarte')

    reservations = resource.scheduler.managed_reservations()
    assert reservations.filter(Reservation.status == 'approved').count() == 2
    assert reservations.filter(Reservation.status == 'pending').count() == 0
    assert resource.scheduler.managed_reserved_slots().count() == 2

    # now deny them
    client.get(ticket.pyquery('a.delete-link')[0].attrib['ic-get-from'])

    message = client.app.smtp.outbox[2]
    message = message.get_payload(0).get_payload(decode=True)
    message = message.decode('iso-8859-1')

    assert "Tageskarte" in message
    assert "28. April 2016" in message
    assert "29. April 2016" in message

    # make sure the reservations are now gone, together with the reserved slots
    reservations = resource.scheduler.managed_reservations()
    assert reservations.filter(Reservation.status == 'approved').count() == 0
    assert reservations.filter(Reservation.status == 'pending').count() == 0
    assert resource.scheduler.managed_reserved_slots().count() == 0


def test_reserve_and_deny_multiple_dates(client):
    client.login_admin()

    transaction.begin()

    resource = client.app.libres_resources.by_name('tageskarte')
    wednesday = resource.scheduler.allocate(
        dates=(datetime(2016, 4, 27), datetime(2016, 4, 27)),
        whole_day=True
    )[0]
    thursday = resource.scheduler.allocate(
        dates=(datetime(2016, 4, 28), datetime(2016, 4, 28)),
        whole_day=True
    )[0]
    friday = resource.scheduler.allocate(
        dates=(datetime(2016, 4, 29), datetime(2016, 4, 29)),
        whole_day=True
    )[0]

    reserve_wednesday = client.bound_reserve(wednesday)
    reserve_thursday = client.bound_reserve(thursday)
    reserve_friday = client.bound_reserve(friday)

    transaction.commit()

    assert reserve_wednesday().json == {'success': True}
    assert reserve_thursday().json == {'success': True}
    assert reserve_friday().json == {'success': True}

    formular = client.get('/resource/tageskarte/form')
    formular.form['email'] = "info@example.org"

    confirmation = formular.form.submit().follow()
    ticket = confirmation.form.submit().follow()
    ticket = client.get('/tickets/ALL/open').click('Annehmen').follow()

    # the resource needs to be refetched after the commit
    resource = client.app.libres_resources.by_name('tageskarte')
    assert resource.scheduler.managed_reserved_slots().count() == 3

    # deny the last reservation
    client.get(ticket.pyquery('a.delete-link')[-1].attrib['ic-get-from'])
    assert resource.scheduler.managed_reserved_slots().count() == 2

    message = client.get_email(1)
    assert "abgesagt" in message
    assert "29. April 2016" in message

    # accept the others
    ticket = ticket.click('Alle Reservationen annehmen').follow()
    assert resource.scheduler.managed_reserved_slots().count() == 2

    message = client.get_email(2)
    assert "angenommen" in message
    assert "27. April 2016" in message
    assert "28. April 2016" in message

    # deny the reservations that were accepted one by one
    client.get(ticket.pyquery('a.delete-link')[-1].attrib['ic-get-from'])
    assert resource.scheduler.managed_reserved_slots().count() == 1

    message = client.get_email(3)
    assert "abgesagt" in message
    assert "27. April 2016" not in message
    assert "28. April 2016" in message

    ticket = client.get(ticket.request.url)
    client.get(ticket.pyquery('a.delete-link')[-1].attrib['ic-get-from'])
    assert resource.scheduler.managed_reserved_slots().count() == 0

    message = client.get_email(4)
    assert "abgesagt" in message
    assert "27. April 2016" in message
    assert "28. April 2016" not in message

    ticket = client.get(ticket.request.url)
    assert "Der hinterlegte Datensatz wurde entfernt" in ticket
    assert "27. April 2016" in message
    assert "28. April 2016" not in message
    assert "29. April 2016" not in message


def test_reserve_failing_multiple(client):
    c1 = client.spawn()
    c1.login_admin()

    c2 = client.spawn()
    c2.login_admin()

    transaction.begin()

    resource = client.app.libres_resources.by_name('tageskarte')
    thursday = resource.scheduler.allocate(
        dates=(datetime(2016, 4, 28), datetime(2016, 4, 28)),
        whole_day=True
    )[0]
    friday = resource.scheduler.allocate(
        dates=(datetime(2016, 4, 29), datetime(2016, 4, 29)),
        whole_day=True
    )[0]

    c1_reserve_thursday = c1.bound_reserve(thursday)
    c1_reserve_friday = c1.bound_reserve(friday)
    c2_reserve_thursday = c2.bound_reserve(thursday)
    c2_reserve_friday = c2.bound_reserve(friday)

    transaction.commit()

    assert c1_reserve_thursday().json == {'success': True}
    assert c1_reserve_friday().json == {'success': True}
    assert c2_reserve_thursday().json == {'success': True}
    assert c2_reserve_friday().json == {'success': True}

    # accept the first reservation session
    formular = c1.get('/resource/tageskarte/form')
    formular.form['email'] = "info@example.org"
    formular.form.submit().follow().form.submit().follow()

    ticket = c1.get('/tickets/ALL/open').click('Annehmen').follow()
    ticket.click('Alle Reservationen annehmen')

    # then try to accept the second one
    formular = c2.get('/resource/tageskarte/form')
    formular.form['email'] = "info@example.org"
    confirmation = formular.form.submit().follow()
    confirmation = confirmation.form.submit().follow()

    assert 'failed_reservations' in confirmation.request.url
    assert 'class="reservation failed"' in confirmation


def test_cleanup_allocations(client):

    # prepate the required data
    resources = ResourceCollection(client.app.libres_context)
    resource = resources.by_name('tageskarte')
    scheduler = resource.get_scheduler(client.app.libres_context)

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
    client.login_admin()

    cleanup = client.get('/resource/tageskarte').click("Aufräumen")
    cleanup.form['start'] = date(2015, 8, 31)
    cleanup.form['end'] = date(2015, 8, 1)
    cleanup = cleanup.form.submit()

    assert "Das End-Datum muss nach dem Start-Datum liegen" in cleanup

    cleanup.form['start'] = date(2015, 8, 1)
    cleanup.form['end'] = date(2015, 8, 31)
    resource = cleanup.form.submit().follow()

    assert "1 Einteilungen wurden erfolgreich entfernt" in resource


def test_view_occurrences(client):

    def events(query=''):
        page = client.get(f'/events/?{query}')
        return [event.text for event in page.pyquery('h3 a')]

    def total_events(query=''):
        page = client.get(f'/events/?{query}')
        return int(page.pyquery('.date-range-selector-result span')[0].text)

    def dates(query=''):
        page = client.get(f'/events/?{query}')
        return [datetime.strptime(div.text, '%d.%m.%Y').date() for div
                in page.pyquery('.occurrence-date')]

    def tags(query=''):
        page = client.get(f'/events/?{query}')
        tags = [tag.text.strip() for tag in page.pyquery('.blank-label')]
        return list(set([tag for tag in tags if tag]))

    def as_json(query=''):
        return client.get(f'/events/json?{query}').json

    assert total_events() == 12
    assert len(events()) == 10
    assert total_events('page=1') == 12
    assert len(events('page=1')) == 2
    assert dates() == sorted(dates())
    assert len(as_json()) == 12
    assert len(as_json('max=3')) == 3

    query = 'tags=Party'
    assert tags(query) == ["Party"]
    assert total_events(query) == 1
    assert events(query) == ["150 Jahre Govikon"]
    assert len(as_json('cat1=Party')) == 1
    assert len(as_json('cat1=Party&cat2=Sportanlage')) == 1

    query = 'tags=Politics'
    assert tags(query) == ["Politik"]
    assert total_events(query) == 1
    assert events(query) == ["Generalversammlung"]
    assert len(as_json('cat1=Politics')) == 1
    assert len(as_json('cat2=Saal')) == 1

    query = 'tags=Sports'
    assert tags(query) == ["Sport"]
    assert total_events(query) == 10
    assert set(events(query)) == set(["Gemeinsames Turnen", "Fussballturnier"])
    assert len(as_json('cat1=Sports')) == 10
    assert len(as_json('cat2=Turnhalle&cat2=Sportanlage')) == 11

    query = 'tags=Politics&tags=Party'
    assert sorted(tags(query)) == ["Party", "Politik"]
    assert total_events(query) == 2
    assert set(events(query)) == set(["150 Jahre Govikon",
                                      "Generalversammlung"])
    assert len(as_json('cat1=Politics&cat1=Party')) == 2
    assert len(as_json('max=1&cat1=Politics&cat1=Party')) == 1

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

    query = 'range=weekend'
    assert tags(query) == ["Party"]
    assert min(dates(query)) == unique_dates[0]
    assert max(dates(query)) == unique_dates[0]
    assert total_events(query) == 1

    query = 'range=weekend&start={}'.format(unique_dates[-2].isoformat())
    assert total_events(query) == 1

    assert client.get('/events/').click('Diese Termine exportieren').\
        text.startswith('BEGIN:VCALENDAR')


def test_view_occurrence(client):
    events = client.get('/events')

    event = events.click("Generalversammlung")
    assert event.pyquery('h1.main-title').text() == "Generalversammlung"
    assert "Gemeindesaal" in event
    assert "Politik" in event
    assert "Alle Jahre wieder" in event
    assert len(event.pyquery('.monthly-view').attr['data-dates'].split(';')) \
        == 1
    assert len(event.pyquery('.calendar-export-list li')) == 1
    assert event.click('Diesen Termin exportieren').text.startswith(
        'BEGIN:VCALENDAR'
    )

    event = events.click("Gemeinsames Turnen", index=0)
    assert event.pyquery('h1.main-title').text() == "Gemeinsames Turnen"
    assert "Turnhalle" in event
    assert "Sport" in event
    assert "fit werden" in event
    assert len(event.pyquery('.monthly-view').attr['data-dates'].split(';')) \
        == 9
    assert len(event.pyquery('.calendar-export-list li')) == 2

    assert event.click('Diesen Termin exportieren').\
        text.startswith('BEGIN:VCALENDAR')
    assert event.click('Alle Termine exportieren').\
        text.startswith('BEGIN:VCALENDAR')


def test_submit_event(client):
    form_page = client.get('/events').click("Veranstaltung melden")

    assert "Das Formular enthält Fehler" in form_page.form.submit()

    # Fill out event
    start_date = date.today() + timedelta(days=1)
    end_date = start_date + timedelta(days=4)
    form_page.form['email'] = "test@example.org"
    form_page.form['title'] = "My Ewent"
    form_page.form['description'] = "My event is an event."
    form_page.form['location'] = "Location"
    form_page.form['organizer'] = "The Organizer"
    form_page.form.set('tags', True, index=0)
    form_page.form.set('tags', True, index=1)
    form_page.form['start_date'] = start_date.isoformat()
    form_page.form['start_time'] = "18:00"
    form_page.form['end_time'] = "22:00"
    form_page.form['end_date'] = end_date.isoformat()
    form_page.form['repeat'] = 'weekly'
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
    assert "The Organizer" in preview_page
    assert "Gastronomie" in preview_page
    assert "{}, 18:00 - 22:00".format(
        babel.dates.format_date(
            start_date, format='d. MMMM yyyy', locale='de'
        )
    ) in preview_page

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

    assert "My Event" not in client.get('/events')

    assert len(client.app.smtp.outbox) == 1
    message = client.app.smtp.outbox[0]
    assert message.get('to') == "test@example.org"
    message = message.get_payload(0).get_payload(decode=True)
    message = message.decode('utf-8')
    assert ticket_nr in message

    assert "Zugriff verweigert" in preview_page.form.submit(expect_errors=True)

    # Accept ticket
    client.login_editor()

    page = client.get('/')
    assert page.pyquery('.open-tickets').attr('data-count') == '1'
    assert page.pyquery('.pending-tickets').attr('data-count') == '0'
    assert page.pyquery('.closed-tickets').attr('data-count') == '0'

    ticket_page = client.get('/tickets/ALL/open').click("Annehmen").follow()
    assert ticket_nr in ticket_page
    assert "test@example.org" in ticket_page
    assert "My Event" in ticket_page
    assert "My event is an event." in ticket_page
    assert "Location" in ticket_page
    assert "The Organizer" in ticket_page
    assert "Ausstellung" in ticket_page
    assert "Gastronomie" in ticket_page

    assert "{}, 18:00 - 22:00".format(
        babel.dates.format_date(
            start_date, format='d. MMMM yyyy', locale='de'
        )
    ) in ticket_page

    assert "Jeden Mo, Di, Mi, Do, Fr, Sa, So bis zum {}".format(
        end_date.strftime('%d.%m.%Y')
    ) in ticket_page
    for days in range(5):
        assert (start_date + timedelta(days=days)).strftime('%d.%m.%Y') in \
            ticket_page

    # Publish event
    ticket_page = ticket_page.click("Veranstaltung annehmen").follow()

    assert "My Event" in client.get('/events')

    assert len(client.app.smtp.outbox) == 2
    message = client.app.smtp.outbox[1]
    assert message.get('to') == "test@example.org"
    message = message.get_payload(0).get_payload(decode=True)
    message = message.decode('utf-8')
    assert "My Event" in message
    assert "My event is an event." in message
    assert "Location" in message
    assert "Ausstellung" in message
    assert "Gastronomie" in message
    assert "The Organizer" in message
    assert "{} 18:00 - 22:00".format(
        start_date.strftime('%d.%m.%Y')) in message
    for days in range(5):
        assert (start_date + timedelta(days=days)).strftime('%d.%m.%Y') in \
            message
    assert "Ihre Veranstaltung wurde angenommen" in message
    assert ticket_nr in message

    # Close ticket
    ticket_page.click("Ticket abschliessen").follow()

    assert len(client.app.smtp.outbox) == 3
    message = client.app.smtp.outbox[2]
    assert message.get('to') == "test@example.org"
    message = message.get_payload(0).get_payload(decode=True)
    message = message.decode('utf-8')
    assert ticket_nr in message


def test_edit_event(client):

    # Submit and publish an event
    form_page = client.get('/events').click("Veranstaltung melden")
    event_date = date.today() + timedelta(days=1)
    form_page.form['email'] = "test@example.org"
    form_page.form['title'] = "My Ewent"
    form_page.form['location'] = "Lokation"
    form_page.form['organizer'] = "Organixator"
    form_page.form['start_date'] = event_date.isoformat()
    form_page.form['start_time'] = "18:00"
    form_page.form['end_time'] = "22:00"
    form_page.form['repeat'] = 'without'
    form_page.form.submit().follow().form.submit().follow()

    client.login_editor()

    ticket_page = client.get('/tickets/ALL/open').click("Annehmen").follow()
    ticket_page = ticket_page.click("Veranstaltung annehmen").follow()

    assert "My Ewent" in client.get('/events')
    assert "Lokation" in client.get('/events')

    # Edit a submitted event
    event_page = client.get('/events').click("My Ewent")
    event_page = event_page.click("Bearbeiten")
    event_page.form['title'] = "My Event"
    event_page.form.submit().follow()

    assert "My Ewent" not in client.get('/events')
    assert "My Event" in client.get('/events')

    # Edit a submitted event via the ticket
    event_page = ticket_page.click("Veranstaltung bearbeiten")
    event_page.form['location'] = "Location"
    event_page.form.submit().follow()

    assert "Lokation" not in client.get('/events')
    assert "Location" in client.get('/events')

    # Edit a non-submitted event
    event_page = client.get('/events').click("150 Jahre Govikon")
    event_page = event_page.click("Bearbeiten")
    event_page.form['title'] = "Stadtfest"
    event_page.form.submit().follow()

    assert "150 Jahre Govikon" not in client.get('/events')
    assert "Stadtfest" in client.get('/events')


def test_delete_event(client):

    # Submit and publish an event
    form_page = client.get('/events').click("Veranstaltung melden")
    event_date = date.today() + timedelta(days=1)
    form_page.form['email'] = "test@example.org"
    form_page.form['title'] = "My Event"
    form_page.form['organizer'] = "Organizer"
    form_page.form['location'] = "Location"
    form_page.form['start_date'] = event_date.isoformat()
    form_page.form['start_time'] = "18:00"
    form_page.form['end_time'] = "22:00"
    form_page.form['repeat'] = 'without'
    form_page.form.submit().follow().form.submit().follow()

    client.login_editor()

    ticket_page = client.get('/tickets/ALL/open').click("Annehmen").follow()
    ticket_page = ticket_page.click("Veranstaltung annehmen").follow()
    ticket_nr = ticket_page.pyquery('.ticket-number').text()

    assert "My Event" in client.get('/events')

    # Try to delete a submitted event directly
    event_page = client.get('/events').click("My Event")

    assert "Diese Veranstaltung kann nicht gelöscht werden." in \
        event_page.pyquery('a.delete-link')[0].values()

    # Delete the event via the ticket
    delete_link = ticket_page.pyquery('a.delete-link').attr('ic-delete-from')
    client.delete(delete_link)

    assert len(client.app.smtp.outbox) == 3
    message = client.app.smtp.outbox[2]
    assert message.get('to') == "test@example.org"
    message = message.get_payload(0).get_payload(decode=True)
    message = message.decode('utf-8')
    assert "My Event" in message
    assert "Ihre Veranstaltung musste leider abgelehnt werden" in message
    assert ticket_nr in message

    assert "My Event" not in client.get('/events')

    # Delete a non-submitted event
    event_page = client.get('/events').click("Generalversammlung")
    assert "Möchten Sie die Veranstaltung wirklich löschen?" in \
        event_page.pyquery('a.delete-link')[0].values()

    delete_link = event_page.pyquery('a.delete-link').attr('ic-delete-from')
    client.delete(delete_link)

    assert "Generalversammlung" not in client.get('/events')


@pytest.mark.flaky(reruns=3)
def test_basic_search(client_with_es):
    client = client_with_es
    client.login_admin()

    add_news = client.get('/news').click('Nachricht')
    add_news.form['title'] = "Now supporting fulltext search"
    add_news.form['lead'] = "It is pretty awesome"
    add_news.form['text'] = "Much <em>wow</em>"
    news = add_news.form.submit().follow()

    client.app.es_client.indices.refresh(index='_all')

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
    assert "fulltext" in client.spawn().get('/search?q=fulltext')
    edit_news = news.click("Bearbeiten")
    edit_news.form['is_hidden_from_public'] = True
    edit_news.form.submit()

    client.app.es_client.indices.refresh(index='_all')

    assert "Now supporting" not in client.spawn().get('/search?q=fulltext')
    assert "Now supporting" in client.get('/search?q=fulltext')


@pytest.mark.flaky(reruns=3)
def test_view_search_is_limiting(client_with_es):
    # ensures that the search doesn't just return all results
    # a regression that occured for anonymous uses only

    client = client_with_es
    client.login_admin()

    add_news = client.get('/news').click('Nachricht')
    add_news.form['title'] = "Foobar"
    add_news.form['lead'] = "Foobar"
    add_news.form.submit()

    add_news = client.get('/news').click('Nachricht')
    add_news.form['title'] = "Deadbeef"
    add_news.form['lead'] = "Deadbeef"
    add_news.form.submit()

    client.app.es_client.indices.refresh(index='_all')

    root_page = client.get('/')
    root_page.form['q'] = "Foobar"
    search_page = root_page.form.submit()

    assert "1 Resultat" in search_page

    client.logout()

    root_page = client.get('/')
    root_page.form['q'] = "Foobar"
    search_page = root_page.form.submit()

    assert "1 Resultat" in search_page


@pytest.mark.flaky(reruns=3)
def test_basic_autocomplete(client_with_es):
    client = client_with_es
    client.login_editor()

    people = client.get('/people')

    new_person = people.click('Person')
    new_person.form['first_name'] = 'Flash'
    new_person.form['last_name'] = 'Gordon'
    new_person.form.submit()

    client.app.es_client.indices.refresh(index='_all')
    assert client.get('/search/suggest?q=Go').json == ["Gordon Flash"]
    assert client.get('/search/suggest?q=Fl').json == ["Flash Gordon"]


def test_unsubscribe_link(client):

    user = UserCollection(client.app.session())\
        .by_username('editor@example.org')

    assert not user.data

    request = Bunch(identity_secret=client.app.identity_secret, app=client.app)

    token = client.app.request_class.new_url_safe_token(request, {
        'user': 'editor@example.org'
    }, salt='unsubscribe')

    client.get('/unsubscribe?token={}'.format(token))
    page = client.get('/')
    assert "abgemeldet" in page

    user = UserCollection(client.app.session())\
        .by_username('editor@example.org')

    assert user.data['daily_ticket_statistics'] == False

    token = client.app.request_class.new_url_safe_token(request, {
        'user': 'unknown@example.org'
    }, salt='unsubscribe')

    page = client.get(
        '/unsubscribe?token={}'.format(token), expect_errors=True)
    assert page.status_code == 403

    token = client.app.request_class.new_url_safe_token(request, {
        'user': 'editor@example.org'
    }, salt='foobar')

    page = client.get(
        '/unsubscribe?token={}'.format(token), expect_errors=True)
    assert page.status_code == 403


def test_newsletters_crud(client):

    client.login_editor()

    newsletter = client.get('/newsletters')
    assert 'Es wurden noch keine Newsletter versendet' in newsletter

    new = newsletter.click('Newsletter')
    new.form['title'] = "Our town is AWESOME"
    new.form['lead'] = "Like many of you, I just love our town..."
    new.select_checkbox("occurrences", "150 Jahre Govikon")
    new.select_checkbox("occurrences", "Gemeinsames Turnen")
    newsletter = new.form.submit().follow()

    assert newsletter.pyquery('h1').text() == "Our town is AWESOME"
    assert "Like many of you" in newsletter
    assert "Gemeinsames Turnen" in newsletter
    assert "Turnhalle" in newsletter
    assert "150 Jahre Govikon" in newsletter
    assert "Sportanlage" in newsletter

    edit = newsletter.click("Bearbeiten")
    edit.form['title'] = "I can't even"
    edit.select_checkbox("occurrences", "150 Jahre Govikon", checked=False)

    newsletter = edit.form.submit().follow()

    assert newsletter.pyquery('h1').text() == "I can't even"
    assert "Like many of you" in newsletter
    assert "Gemeinsames Turnen" in newsletter
    assert "Turnhalle" in newsletter
    assert "150 Jahre Govikon" not in newsletter
    assert "Sportanlage" not in newsletter

    newsletters = client.get('/newsletters')
    assert "I can't even" in newsletters
    assert "Noch nicht gesendet." in newsletters

    # not sent, therefore not visible to the public
    assert "noch keine Newsletter" in client.spawn().get('/newsletters')

    delete_link = newsletter.pyquery('a.delete-link').attr('ic-delete-from')
    client.delete(delete_link)

    newsletters = client.get('/newsletters')
    assert "noch keine Newsletter" in newsletters


def test_newsletter_signup(client):

    page = client.get('/newsletters')
    page.form['address'] = 'asdf'
    page = page.form.submit()

    assert 'Ungültig' in page

    page.form['address'] = 'info@example.org'
    page.form.submit()

    assert len(client.app.smtp.outbox) == 1

    # make sure double submissions don't result in multiple e-mails
    page.form.submit()
    assert len(client.app.smtp.outbox) == 1

    message = client.app.smtp.outbox[0]
    message = message.get_payload(0).get_payload(decode=True)
    message = message.decode('utf-8')

    confirm = re.search(r'Anmeldung bestätigen\]\(([^\)]+)', message).group(1)

    # try an illegal token first
    illegal = confirm.split('/confirm')[0] + 'x/confirm'
    assert "falsches Token" in client.get(illegal).follow()

    # make sure double calls work
    assert "info@example.org wurde erfolgreich" in client.get(confirm).follow()
    assert "info@example.org wurde erfolgreich" in client.get(confirm).follow()

    # subscribing still works the same, but there's still no email sent
    page.form.submit()
    assert len(client.app.smtp.outbox) == 1

    # unsubscribing does not result in an e-mail either
    assert "falsches Token" in client.get(
        illegal.replace('/confirm', '/unsubscribe')
    ).follow()
    assert "erfolgreich abgemeldet" in client.get(
        confirm.replace('/confirm', '/unsubscribe')
    ).follow()

    # no e-mail is sent when unsubscribing
    assert len(client.app.smtp.outbox) == 1

    # however, we can now signup again
    page.form.submit()
    assert len(client.app.smtp.outbox) == 2


def test_newsletter_subscribers_management(client):

    page = client.get('/newsletters')
    page.form['address'] = 'info@example.org'
    page.form.submit()

    assert len(client.app.smtp.outbox) == 1

    message = client.app.smtp.outbox[0]
    message = message.get_payload(0).get_payload(decode=True)
    message = message.decode('utf-8')

    confirm = re.search(r'Anmeldung bestätigen\]\(([^\)]+)', message).group(1)
    assert "info@example.org wurde erfolgreich" in client.get(confirm).follow()

    client.login_editor()

    subscribers = client.get('/subscribers')
    assert "info@example.org" in subscribers

    unsubscribe = subscribers.pyquery('a[ic-get-from]').attr('ic-get-from')
    result = client.get(unsubscribe).follow()
    assert "info@example.org wurde erfolgreich abgemeldet" in result


def test_newsletter_send(client):
    anon = client.spawn()

    client.login_editor()

    # add a newsletter
    new = client.get('/newsletters').click('Newsletter')
    new.form['title'] = "Our town is AWESOME"
    new.form['lead'] = "Like many of you, I just love our town..."

    new.select_checkbox("news", "Willkommen bei OneGov")
    new.select_checkbox("occurrences", "150 Jahre Govikon")
    new.select_checkbox("occurrences", "Gemeinsames Turnen")

    newsletter = new.form.submit().follow()

    # add some recipients the quick wqy
    recipients = RecipientCollection(client.app.session())
    recipients.add('one@example.org', confirmed=True)
    recipients.add('two@example.org', confirmed=True)
    recipients.add('xxx@example.org', confirmed=False)

    transaction.commit()

    assert "2 Abonnenten registriert" in client.get('/newsletters')

    # send the newsletter
    send = newsletter.click('Senden')
    assert "Dieser Newsletter wurde noch nicht gesendet." in send
    assert "one@example.org" not in send
    assert "two@example.org" not in send
    assert "xxx@example.org" not in send

    newsletter = send.form.submit().follow()
    assert '"Our town is AWESOME" wurde an 2 Empfänger gesendet' in newsletter

    page = anon.get('/newsletters')
    assert "gerade eben" in page

    # the send form should now look different
    send = newsletter.click('Senden')

    assert "Zum ersten Mal gesendet gerade eben." in send
    assert "Dieser Newsletter wurde an 2 Abonnenten gesendet." in send
    assert "one@example.org" in send
    assert "two@example.org" in send
    assert "xxx@example.org" not in send

    assert len(send.pyquery('.previous-recipients li')) == 2

    # make sure the mail was sent correctly
    assert len(client.app.smtp.outbox) == 2

    message = client.app.smtp.outbox[0]
    message = message.get_payload(0).get_payload(decode=True)
    message = message.decode('utf-8')

    assert "Our town is AWESOME" in message
    assert "Like many of you" in message

    web = re.search(r'Web-Version anzuzeigen.\]\(([^\)]+)', message).group(1)
    assert web.endswith('/newsletter/our-town-is-awesome')

    # make sure the unconfirm link is different for each mail
    unconfirm_1 = re.search(r'abzumelden.\]\(([^\)]+)', message).group(1)

    message = client.app.smtp.outbox[1]
    message = message.get_payload(0).get_payload(decode=True)
    message = message.decode('utf-8')

    unconfirm_2 = re.search(r'abzumelden.\]\(([^\)]+)', message).group(1)

    assert unconfirm_1 and unconfirm_2
    assert unconfirm_1 != unconfirm_2

    # make sure the unconfirm link actually works
    anon.get(unconfirm_1)
    assert recipients.query().count() == 2

    anon.get(unconfirm_2)
    assert recipients.query().count() == 1


def test_newsletter_schedule(client):
    client.login_editor()

    # add a newsletter
    new = client.get('/newsletters').click('Newsletter')
    new.form['title'] = "Our town is AWESOME"
    new.form['lead'] = "Like many of you, I just love our town..."

    new.select_checkbox("news", "Willkommen bei OneGov")
    new.select_checkbox("occurrences", "150 Jahre Govikon")

    newsletter = new.form.submit().follow()

    # add some recipients the quick wqy
    recipients = RecipientCollection(client.app.session())
    recipients.add('one@example.org', confirmed=True)
    recipients.add('two@example.org', confirmed=True)

    transaction.commit()

    send = newsletter.click('Senden')
    send.form['send'] = 'specify'

    # schedule the newsletter too close to execute
    time = replace_timezone(datetime(2018, 5, 31, 11, 55, 1), 'Europe/Zurich')

    with freeze_time(time):
        send.form['time'] = '2018-05-31 12:00:00'
        assert '5 Minuten in der Zukunft' in send.form.submit()

        # schedule the newsletter outside the hour
        send.form['time'] = '2018-05-31 12:55:00'
        assert 'nur zur vollen Stunde' in send.form.submit()

    # schedule the newsletter at a valid time
    time = replace_timezone(datetime(2018, 5, 31, 11, 55, 0), 'Europe/Zurich')

    with freeze_time(time):
        send.form['time'] = '2018-05-31 12:00:00'
        send.form.submit().follow()


def test_newsletter_test_delivery(client):
    client.login_editor()

    # add a newsletter
    new = client.get('/newsletters').click('Newsletter')
    new.form['title'] = "Our town is AWESOME"
    new.form['lead'] = "Like many of you, I just love our town..."

    new.select_checkbox("news", "Willkommen bei OneGov")
    new.select_checkbox("occurrences", "150 Jahre Govikon")

    newsletter = new.form.submit().follow()

    # add some recipients the quick wqy
    recipients = RecipientCollection(client.app.session())
    recipients.add('one@example.org', confirmed=True)
    recipients.add('two@example.org', confirmed=True)

    recipient = recipients.query().first().id.hex

    transaction.commit()

    send = newsletter.click('Test')
    send.form['selected_recipient'] = recipient
    send.form.submit().follow()

    assert len(client.app.smtp.outbox) == 1

    send = newsletter.click('Test')
    send.form['selected_recipient'] = recipient
    send.form.submit().follow()

    assert len(client.app.smtp.outbox) == 2

    newsletter = NewsletterCollection(client.app.session()).query().one()
    assert newsletter.sent is None
    assert not newsletter.recipients


def test_map_default_view(client):
    client.login_admin()

    settings = client.get('/settings')

    assert not decode_map_value(settings.form['default_map_view'].value)

    settings.form['default_map_view'] = encode_map_value({
        'lat': 47, 'lon': 8, 'zoom': 12
    })
    settings = settings.form.submit().follow()

    coordinates = decode_map_value(settings.form['default_map_view'].value)
    assert coordinates.lat == 47
    assert coordinates.lon == 8
    assert coordinates.zoom == 12

    edit = client.get('/editor/edit/page/1')
    assert 'data-default-lat="47"' in edit
    assert 'data-default-lon="8"' in edit
    assert 'data-default-zoom="12"' in edit


def test_map_set_marker(client):
    client.login_admin()

    edit = client.get('/editor/edit/page/1')
    assert decode_map_value(edit.form['coordinates'].value) == Coordinates()
    page = edit.form.submit().follow()

    assert 'marker-map' not in page

    edit = client.get('/editor/edit/page/1')
    edit.form['coordinates'] = encode_map_value({
        'lat': 47, 'lon': 8, 'zoom': 12
    })
    page = edit.form.submit().follow()

    assert 'marker-map' in page
    assert 'data-lat="47"' in page
    assert 'data-lon="8"' in page
    assert 'data-zoom="12"' in page


def test_manage_album(client):
    client.login_editor()

    albums = client.get('/photoalbums')
    assert "Noch keine Fotoalben" in albums

    new = albums.click('Fotoalbum')
    new.form['title'] = "Comicon 2016"
    new.form.submit()

    albums = client.get('/photoalbums')
    assert "Comicon 2016" in albums

    album = albums.click("Comicon 2016")
    assert "Comicon 2016" in album
    assert "noch keine Bilder" in album

    images = albums.click("Bilder verwalten")
    images.form['file'] = Upload('test.jpg', utils.create_image().read())
    images.form.submit()

    select = album.click("Bilder auswählen")
    select.form[tuple(select.form.fields.keys())[1]] = True
    select.form.submit()

    album = albums.click("Comicon 2016")
    assert "noch keine Bilder" not in album

    images = albums.click("Bilder verwalten")

    url = re.search(r'data-note-update-url="([^"]+)"', images.text).group(1)
    client.post(url, {'note': "This is an alt text"})

    album = albums.click("Comicon 2016")
    assert "This is an alt text" in album


def test_settings(client):

    assert client.get('/settings', expect_errors=True).status_code == 403

    client.login_admin()

    settings_page = client.get('/settings')
    document = settings_page.pyquery

    assert document.find('input[name=name]').val() == 'Govikon'
    assert document.find('input[name=primary_color]').val() == '#006fba'

    settings_page.form['primary_color'] = '#xxx'
    settings_page.form['reply_to'] = 'info@govikon.ch'
    settings_page = settings_page.form.submit()

    assert "Ungültige Farbe." in settings_page.text

    settings_page.form['primary_color'] = '#ccddee'
    settings_page.form['reply_to'] = 'info@govikon.ch'
    settings_page = settings_page.form.submit().follow()

    assert "Ungültige Farbe." not in settings_page.text

    settings_page.form['logo_url'] = 'https://seantis.ch/logo.img'
    settings_page.form['reply_to'] = 'info@govikon.ch'
    settings_page = settings_page.form.submit().follow()

    assert '<img src="https://seantis.ch/logo.img"' in settings_page.text

    settings_page.form['homepage_image_1'] = "http://images/one"
    settings_page.form['homepage_image_2'] = "http://images/two"
    settings_page = settings_page.form.submit().follow()

    assert 'http://images/one' in settings_page
    assert 'http://images/two' in settings_page

    settings_page.form['analytics_code'] = '<script>alert("Hi!");</script>'
    settings_page = settings_page.form.submit().follow()
    assert '<script>alert("Hi!");</script>' in settings_page.text


def test_registration_honeypot(client):
    client.app.enable_user_registration = True

    register = client.get('/auth/register')
    register.form['username'] = 'spam@example.org'
    register.form['password'] = 'p@ssw0rd'
    register.form['confirm'] = 'p@ssw0rd'
    register.form['roboter_falle'] = 'buy pills now'

    assert "Das Feld ist nicht leer" in register.form.submit()


def test_registration(client):
    client.app.enable_user_registration = True

    register = client.get('/auth/register')
    register.form['username'] = 'user@example.org'
    register.form['password'] = 'p@ssw0rd'
    register.form['confirm'] = 'p@ssw0rd'

    assert "Vielen Dank" in register.form.submit().follow()

    message = client.get_email(0, 1)
    assert "Anmeldung bestätigen" in message

    expr = r'href="[^"]+">Anmeldung bestätigen</a>'
    url = re.search(expr, message).group()
    url = client.extract_href(url)

    faulty = URL(url).query_param('token', 'asdf').as_string()

    assert "Ungültiger Aktivierungscode" in client.get(faulty).follow()
    assert "Konto wurde aktiviert" in client.get(url).follow()
    assert "Konto wurde bereits aktiviert" in client.get(url).follow()

    logged_in = client.login('user@example.org', 'p@ssw0rd').follow()
    assert "eingeloggt" in logged_in


def test_registration_disabled(client):

    client.app.enable_user_registration = False

    assert client.get('/auth/register', status=404)


def test_disabled_yubikey(client):
    client.login_admin()

    client.app.enable_yubikey = False
    assert 'YubiKey' not in client.get('/auth/login')
    assert 'YubiKey' not in client.get('/usermanagement')

    client.app.enable_yubikey = True
    assert 'YubiKey' in client.get('/auth/login')
    assert 'YubiKey' in client.get('/usermanagement')


def test_disable_users(client):
    client.login_admin()

    users = client.get('/usermanagement')
    assert 'admin@example.org' in users
    assert 'editor@example.org' in users

    editor = users.click('Bearbeiten', index=1)
    editor.form['state'] = 'inactive'
    editor.form.submit()

    login = client.spawn().login_editor()
    assert login.status_code == 200

    editor = users.click('Bearbeiten', index=1)
    editor.form['role'] = 'member'
    editor.form['state'] = 'active'
    editor.form.submit()

    login = client.spawn().login_editor()
    assert login.status_code == 302


def test_change_role(client):
    client.login_admin()

    client.app.enable_yubikey = True

    editor = client.get('/usermanagement').click('Bearbeiten', index=1)
    assert "müssen zwingend einen YubiKey" in editor.form.submit()

    editor.form['role'] = 'member'
    assert editor.form.submit().status_code == 302

    editor.form['role'] = 'admin'
    editor.form['state'] = 'inactive'
    assert editor.form.submit().status_code == 302

    editor.form['role'] = 'admin'
    editor.form['state'] = 'active'
    editor.form['yubikey'] = 'cccccccdefgh'
    assert editor.form.submit().status_code == 302

    client.app.enable_yubikey = False
    editor.form['role'] = 'admin'
    editor.form['state'] = 'active'
    editor.form['yubikey'] = ''
    assert editor.form.submit().status_code == 302


def test_unique_yubikey(client):
    client.login_admin()

    client.app.enable_yubikey = True

    users = client.get('/usermanagement')
    admin = users.click('Bearbeiten', index=0)
    editor = users.click('Bearbeiten', index=1)

    admin.form['yubikey'] = 'cccccccdefgh'
    assert admin.form.submit().status_code == 302

    editor.form['yubikey'] = 'cccccccdefgh'
    assert "bereits von admin@example.org verwendet" in editor.form.submit()

    # make sure the current owner can save its own yubikey
    admin = users.click('Bearbeiten', index=0)
    assert admin.form.submit().status_code == 302


def test_add_new_user_without_activation_email(client):
    client.login_admin()

    client.app.enable_yubikey = True

    new = client.get('/usermanagement').click('Benutzer', index=2)
    new.form['username'] = 'admin@example.org'

    assert "existiert bereits" in new.form.submit()

    new.form['username'] = 'member@example.org'
    new.form['role'] = 'admin'

    assert "müssen zwingend einen YubiKey" in new.form.submit()

    new.form['role'] = 'member'
    new.form['send_activation_email'] = False
    added = new.form.submit()

    assert "Passwort" in added
    password = added.pyquery('.panel strong').text()

    login = client.spawn().get('/auth/login')
    login.form['username'] = 'member@example.org'
    login.form['password'] = password
    assert login.form.submit().status_code == 302


def test_add_new_user_with_activation_email(client):
    client.login_admin()

    client.app.enable_yubikey = False

    new = client.get('/usermanagement').click('Benutzer', index=2)
    new.form['username'] = 'member@example.org'
    new.form['role'] = 'member'
    new.form['send_activation_email'] = True
    added = new.form.submit()

    assert "Passwort" not in added
    assert "Anmeldungs-Anleitung wurde an den Benutzer gesendet" in added

    email = client.get_email(0)
    reset = re.search(
        r'(http://localhost/auth/reset-password[^)]+)', email).group()

    page = client.spawn().get(reset)
    page.form['email'] = 'member@example.org'
    page.form['password'] = 'p@ssw0rd'
    page.form.submit()

    login = client.spawn().get('/auth/login')
    login.form['username'] = 'member@example.org'
    login.form['password'] = 'p@ssw0rd'
    assert login.form.submit().status_code == 302


def test_edit_user_settings(client):
    client.login_admin()

    client.app.enable_yubikey = False

    new = client.get('/usermanagement').click('Benutzer', index=2)
    new.form['username'] = 'new@example.org'
    new.form['role'] = 'member'
    new.form.submit()

    users = UserCollection(client.app.session())
    assert not users.by_username('new@example.org').data

    edit = client.get('/usermanagement').click('Bearbeiten', index=2)
    assert "new@example.org" in edit

    edit.form.get('daily_ticket_statistics').checked = False
    edit.form.submit()

    assert not users.by_username('new@example.org')\
        .data['daily_ticket_statistics']


def test_homepage(client):
    client.app.org.meta['homepage_cover'] = "<b>0xdeadbeef</b>"
    client.app.org.meta['homepage_structure'] = """
        <row>
            <column span="8">
                <homepage-cover />
            </column>
            <column span="4">
                <panel>
                    <news />
                </panel>
                <panel>
                    <events />
                </panel>
            </column>
        </row>
    """

    transaction.commit()

    homepage = client.get('/')

    assert '<b>0xdeadbeef</b>' in homepage
    assert '<h2>Veranstaltungen</h2>' in homepage


def test_send_ticket_email(client):
    anon = client.spawn()

    admin = client.spawn()
    admin.login_admin()

    # make sure submitted event emails are sent to everyone, unless the
    # logged-in user is the same as the user responsible for the event
    def submit_event(client, email):
        start = date.today() + timedelta(days=1)

        page = client.get('/events').click("Veranstaltung melden")
        page.form['email'] = email
        page.form['title'] = "My Event"
        page.form['description'] = "My event is an event."
        page.form['organizer'] = "The Organizer"
        page.form['location'] = "A place"
        page.form['start_date'] = start.isoformat()
        page.form['start_time'] = "18:00"
        page.form['end_time'] = "22:00"
        page.form['repeat'] = 'without'

        page.form.submit().follow().form.submit()

    del client.app.smtp.outbox[:]

    submit_event(admin, 'admin@example.org')
    assert len(client.app.smtp.outbox) == 0

    submit_event(admin, 'someone-else@example.org')
    assert len(client.app.smtp.outbox) == 1
    assert 'someone-else@example.org' == client.app.smtp.outbox[0]['To']

    submit_event(anon, 'admin@example.org')
    assert len(client.app.smtp.outbox) == 2
    assert 'admin@example.org' == client.app.smtp.outbox[1]['To']

    # ticket notifications can be manually disabled
    page = admin.get('/tickets/ALL/open').click('Annehmen', index=1).follow()
    page = page.click('E-Mails deaktivieren').follow()

    assert 'deaktiviert' in page
    ticket_url = page.request.url
    page = page.click('Ticket abschliessen').follow()

    assert len(client.app.smtp.outbox) == 2
    page = admin.get(ticket_url)
    page = page.click('E-Mails aktivieren').follow()

    page = page.click('Ticket wieder öffnen').follow()
    assert len(client.app.smtp.outbox) == 3

    # make sure the same holds true for forms
    collection = FormCollection(client.app.session())
    collection.definitions.add('Profile', definition=textwrap.dedent("""
        Name * = ___
        E-Mail * = @@@
    """), type='custom')
    transaction.commit()

    def submit_form(client, email):
        page = client.get('/forms').click('Profile')
        page.form['name'] = 'foobar'
        page.form['e_mail'] = email
        page.form.submit().follow().form.submit()

    del client.app.smtp.outbox[:]

    submit_form(admin, 'admin@example.org')
    assert len(client.app.smtp.outbox) == 0

    submit_form(admin, 'someone-else@example.org')
    assert len(client.app.smtp.outbox) == 1
    assert 'someone-else@example.org' == client.app.smtp.outbox[0]['To']

    # and for reservations
    resources = ResourceCollection(client.app.libres_context)
    resource = resources.by_name('tageskarte')
    scheduler = resource.get_scheduler(client.app.libres_context)

    allocations = scheduler.allocate(
        dates=(datetime(2015, 8, 28, 10), datetime(2015, 8, 28, 14)),
        whole_day=False,
        partly_available=True,
        quota=10
    )

    reserve = admin.bound_reserve(allocations[0])
    transaction.commit()

    def submit_reservation(client, email):
        assert reserve('10:00', '12:00').json == {'success': True}

        # fill out the form
        formular = client.get('/resource/tageskarte/form')
        formular.form['email'] = email

        formular.form.submit().follow().form.submit().follow()

    del client.app.smtp.outbox[:]

    submit_reservation(admin, 'admin@example.org')
    assert len(client.app.smtp.outbox) == 0

    submit_reservation(admin, 'someone-else@example.org')
    assert len(client.app.smtp.outbox) == 1
    assert 'someone-else@example.org' == client.app.smtp.outbox[0]['To']


def test_login_with_required_userprofile(client):
    # userprofile is not complete
    client.app.settings.org.require_complete_userprofile = True
    client.app.settings.org.is_complete_userprofile = lambda r, u: False

    page = client.get('/auth/login?to=/settings')
    page.form['username'] = 'admin@example.org'
    page.form['password'] = 'wrong-password'
    page = page.form.submit()

    assert 'falsches Passwort' in page

    page.form['password'] = 'hunter2'
    page = page.form.submit().follow()

    assert 'userprofile' in page.request.url
    assert "Ihr Benutzerprofil ist unvollständig" in page
    page = page.form.submit().follow()

    assert 'settings' in page.request.url

    # userprofile is complete
    client.app.settings.org.require_complete_userprofile = True
    client.app.settings.org.is_complete_userprofile = lambda r, u: True

    page = client.get('/auth/login?to=/settings')
    page.form['username'] = 'admin@example.org'
    page.form['password'] = 'hunter2'
    page = page.form.submit()

    assert 'settings' in page.request.url

    # completeness not required
    client.app.settings.org.require_complete_userprofile = False
    client.app.settings.org.is_complete_userprofile = lambda r, u: True

    page = client.get('/auth/login?to=/settings')
    page.form['username'] = 'admin@example.org'
    page.form['password'] = 'hunter2'
    page = page.form.submit()

    assert 'settings' in page.request.url


def test_manual_form_payment(client):
    collection = FormCollection(client.app.session())
    collection.definitions.add('Govikon Poster', definition=textwrap.dedent("""
        E-Mail *= @@@

        Posters *=
            [ ] Local Businesses (0 CHF)
            [ ] Executive Committee (10 CHF)
            [ ] Town Square (20 CHF)

        Delivery *=
            ( ) Pickup (0 CHF)
            ( ) Delivery (5 CHF)
    """), type='custom')

    transaction.commit()

    page = client.get('/form/govikon-poster')
    assert '10.00 CHF' in page
    assert '20.00 CHF' in page
    assert '5.00 CHF' in page

    page.form['e_mail'] = 'info@example.org'
    page.select_checkbox('posters', "Executive Committee")
    page.select_checkbox('posters', "Town Square")
    page.form['delivery'] = 'Delivery'

    page = page.form.submit().follow()
    assert "Totalbetrag" in page
    assert "35.00 CHF" in page

    page = page.form.submit().follow()
    assert "Ticket Status" in page

    client.login_editor()
    page = client.get('/tickets/ALL/open').click("Annehmen").follow()

    assert page.pyquery('.payment-state').text() == "Offen"

    client.post(page.pyquery('.mark-as-paid').attr('ic-post-to'))
    page = client.get(page.request.url)

    assert page.pyquery('.payment-state').text() == "Bezahlt"

    client.post(page.pyquery('.mark-as-unpaid').attr('ic-post-to'))
    page = client.get(page.request.url)

    assert page.pyquery('.payment-state').text() == "Offen"

    payments = client.get('/payments')
    assert "FRM-" in payments
    assert "Manuell" in payments
    assert "info@example.org" in payments
    assert "35.00" in payments
    assert "Offen" in payments


def test_manual_reservation_payment_with_extra(client):

    # prepate the required data
    resources = ResourceCollection(client.app.libres_context)
    resource = resources.by_name('tageskarte')
    resource.pricing_method = 'per_item'
    resource.price_per_item = 15.00
    resource.payment_method = 'manual'
    resource.definition = textwrap.dedent("""
        Donation =
            (x) Yes (10 CHF)
            ( ) No
    """)

    scheduler = resource.get_scheduler(client.app.libres_context)
    allocations = scheduler.allocate(
        dates=(
            datetime(2017, 7, 9),
            datetime(2017, 7, 9)
        ),
        whole_day=True,
        quota=4
    )

    reserve = client.bound_reserve(allocations[0])
    transaction.commit()

    # create a reservation
    reserve(quota=2, whole_day=True)

    page = client.get('/resource/tageskarte/form')
    page.form['email'] = 'info@example.org'

    page.form['donation'] = 'No'
    assert '30.00' in page.form.submit().follow()

    page.form['donation'] = 'Yes'
    assert '40.00' in page.form.submit().follow()

    ticket = page.form.submit().follow().form.submit().follow()
    assert 'RSV-' in ticket.text

    # mark it as paid
    client.login_editor()
    page = client.get('/tickets/ALL/open').click("Annehmen").follow()

    assert page.pyquery('.payment-state').text() == "Offen"

    client.post(page.pyquery('.mark-as-paid').attr('ic-post-to'))
    page = client.get(page.request.url)

    assert page.pyquery('.payment-state').text() == "Bezahlt"

    client.post(page.pyquery('.mark-as-unpaid').attr('ic-post-to'))
    page = client.get(page.request.url)

    assert page.pyquery('.payment-state').text() == "Offen"

    payments = client.get('/payments')
    assert "RSV-" in payments
    assert "Manuell" in payments
    assert "info@example.org" in payments
    assert "40.00" in payments
    assert "Offen" in payments


def test_manual_reservation_payment_without_extra(client):

    # prepate the required data
    resources = ResourceCollection(client.app.libres_context)
    resource = resources.by_name('tageskarte')
    resource.pricing_method = 'per_hour'
    resource.price_per_hour = 10.00
    resource.payment_method = 'manual'

    scheduler = resource.get_scheduler(client.app.libres_context)
    allocations = scheduler.allocate(
        dates=(
            datetime(2017, 7, 9, 10),
            datetime(2017, 7, 9, 12)
        )
    )

    reserve = client.bound_reserve(allocations[0])
    transaction.commit()

    # create a reservation
    reserve()

    page = client.get('/resource/tageskarte/form')
    page.form['email'] = 'info@example.org'
    assert '20.00' in page.form.submit().follow()

    ticket = page.form.submit().follow().form.submit().follow()
    assert 'RSV-' in ticket.text

    # mark it as paid
    client.login_editor()
    page = client.get('/tickets/ALL/open').click("Annehmen").follow()

    assert page.pyquery('.payment-state').text() == "Offen"

    client.post(page.pyquery('.mark-as-paid').attr('ic-post-to'))
    page = client.get(page.request.url)

    assert page.pyquery('.payment-state').text() == "Bezahlt"

    client.post(page.pyquery('.mark-as-unpaid').attr('ic-post-to'))
    page = client.get(page.request.url)

    assert page.pyquery('.payment-state').text() == "Offen"

    payments = client.get('/payments')
    assert "RSV-" in payments
    assert "Manuell" in payments
    assert "info@example.org" in payments
    assert "20.00" in payments
    assert "Offen" in payments


def test_setup_stripe(client):
    client.login_admin()

    assert client.app.default_payment_provider is None

    with requests_mock.Mocker() as m:
        m.post('https://oauth.example.org/register/foo', json={
            'token': '0xdeadbeef'
        })

        client.get('/payment-provider').click("Stripe Connect")

        url = URL(m.request_history[0].json()['url'])
        url = url.query_param('oauth_redirect_secret', 'bar')
        url = url.query_param('code', 'api_key')

        m.post('https://connect.stripe.com/oauth/token', json={
            'scope': 'read_write',
            'stripe_publishable_key': 'stripe_publishable_key',
            'stripe_user_id': 'stripe_user_id',
            'refresh_token': 'refresh_token',
            'access_token': 'access_token',
        })

        client.get(url.as_string())

    provider = client.app.default_payment_provider
    assert provider.title == 'Stripe Connect'
    assert provider.publishable_key == 'stripe_publishable_key'
    assert provider.user_id == 'stripe_user_id'
    assert provider.refresh_token == 'refresh_token'
    assert provider.access_token == 'access_token'


def test_stripe_form_payment(client):
    collection = FormCollection(client.app.session())
    collection.definitions.add('Donate', definition=textwrap.dedent("""
        E-Mail *= @@@

        Donation *=
            (x) Small (10 CHF)
            ( ) Medium (100 CHF)
    """), type='custom', payment_method='free')

    providers = PaymentProviderCollection(client.app.session())
    providers.add(type='stripe_connect', default=True, meta={
        'publishable_key': '0xdeadbeef',
        'access_token': 'foobar'
    })

    transaction.commit()

    page = client.get('/form/donate')
    page.form['e_mail'] = 'info@example.org'
    page = page.form.submit().follow()

    assert "Totalbetrag" in page
    assert "10.00 CHF" in page
    assert "+ 0.59" not in page
    assert "Online zahlen und abschliessen" in page

    button = page.pyquery('.checkout-button')
    assert button.attr('data-stripe-amount') == '1000'
    assert button.attr('data-stripe-currency') == 'CHF'
    assert button.attr('data-stripe-email') == 'info@example.org'
    assert button.attr('data-stripe-description') == 'Donate'
    assert button.attr('data-action') == 'submit'
    assert button.attr('data-stripe-allowrememberme') == 'false'
    assert button.attr('data-stripe-key') == '0xdeadbeef'

    with requests_mock.Mocker() as m:
        charge = {
            'id': '123456'
        }

        m.post('https://api.stripe.com/v1/charges', json=charge)
        m.get('https://api.stripe.com/v1/charges/123456', json=charge)
        m.post('https://api.stripe.com/v1/charges/123456/capture', json=charge)

        page.form['payment_token'] = 'foobar'
        page.form.submit().follow()

    with requests_mock.Mocker() as m:
        m.get('https://api.stripe.com/v1/charges/123456', json={
            'id': '123456',
            'captured': True,
            'refunded': False,
            'paid': True,
            'status': 'foobar'
        })

        client.login_admin()
        ticket = client.get('/tickets/ALL/open').click('Annehmen').follow()
        assert "Bezahlt" in ticket

    payments = client.get('/payments')
    assert "FRM-" in payments
    assert "Stripe Connect" in payments
    assert "info@example.org" in payments
    assert "9.41 CHF" in payments
    assert "0.59" in payments


def test_stripe_charge_fee_to_customer(client):
    collection = FormCollection(client.app.session())
    collection.definitions.add('Donate', definition=textwrap.dedent("""
        E-Mail *= @@@

        Donation *=
            (x) Small (10 CHF)
            ( ) Medium (100 CHF)
    """), type='custom', payment_method='free')

    providers = PaymentProviderCollection(client.app.session())
    providers.add(type='stripe_connect', default=True, meta={
        'publishable_key': '0xdeadbeef',
        'access_token': 'foobar',
        'user_id': 'foobar'
    })

    transaction.commit()

    client.login_admin()

    with requests_mock.Mocker() as m:
        m.get('https://api.stripe.com/v1/accounts/foobar', json={
            'business_name': 'Govikon',
            'email': 'info@example.org'
        })

        page = client.get('/payment-provider').click("Einstellungen", index=1)

    assert 'Govikon / info@example.org' in page
    page.form['charge_fee_to_customer'] = True
    page.form.submit()

    page = client.get('/form/donate')
    page.form['e_mail'] = 'info@example.org'
    page = page.form.submit().follow()

    assert "Totalbetrag" in page
    assert "10.00 CHF" in page
    assert "+ 0.61 CHF Kreditkarten-Gebühr" in page
    assert "Online zahlen und abschliessen" in page

    button = page.pyquery('.checkout-button')
    assert button.attr('data-stripe-amount') == '1061'

    with requests_mock.Mocker() as m:
        charge = {
            'id': '123456'
        }

        m.post('https://api.stripe.com/v1/charges', json=charge)
        m.get('https://api.stripe.com/v1/charges/123456', json=charge)
        m.post('https://api.stripe.com/v1/charges/123456/capture', json=charge)

        page.form['payment_token'] = 'foobar'
        page.form.submit().follow()

    with requests_mock.Mocker() as m:
        m.get('https://api.stripe.com/v1/charges/123456', json={
            'id': '123456',
            'captured': True,
            'refunded': False,
            'paid': True,
            'status': 'foobar'
        })

        client.login_admin()
        ticket = client.get('/tickets/ALL/open').click('Annehmen').follow()
        assert "Bezahlt" in ticket

    payments = client.get('/payments')
    assert "FRM-" in payments
    assert "Stripe Connect" in payments
    assert "info@example.org" in payments
    assert "10.00" in payments
    assert "0.61" in payments


def test_switch_languages(client):

    client.login_admin()

    page = client.get('/settings')
    assert 'Deutsch' in page
    assert 'Allemand' not in page

    page.form['locales'] = 'fr_CH'
    page = page.form.submit().follow()

    assert 'Allemand' in page
    assert 'Deutsch' not in page


def test_directory_visibility(client):

    client.login_admin()

    page = client.get('/directories')
    assert 'Noch keine Verzeichnisse' in page

    page = page.click('Verzeichnis')
    page.form['title'] = "Clubs"
    page.form['structure'] = """
        Name *= ___
    """
    page.form['title_format'] = '[Name]'
    page.form.submit()

    page = client.get('/directories/clubs')
    page = page.click('Eintrag', index=0)
    page.form['name'] = 'Soccer Club'
    page.form.submit()

    anon = client.spawn()
    assert "Clubs" in anon.get('/directories')
    assert "Soccer" in anon.get('/directories/clubs')
    assert "Soccer" in anon.get('/directories/clubs/soccer-club')

    page = client.get('/directories/clubs/soccer-club').click("Bearbeiten")
    page.form['is_hidden_from_public'] = True
    page.form.submit()

    assert "Clubs" in anon.get('/directories')
    assert "Soccer" not in anon.get('/directories/clubs')
    assert anon.get('/directories/clubs/soccer-club', status=403)

    page = client.get('/directories/clubs/soccer-club').click("Bearbeiten")
    page.form['is_hidden_from_public'] = False
    page.form.submit()

    page = client.get('/directories/clubs').click("Konfigurieren")
    page.form['is_hidden_from_public'] = True
    page.form.submit()

    assert "Clubs" not in anon.get('/directories')
    assert anon.get('/directories/clubs', status=403)
    assert anon.get('/directories/clubs/soccer-club')


def test_directory_submissions(client, postgres):

    client.login_admin()

    # create a directory does not accept submissions
    page = client.get('/directories').click('Verzeichnis')
    page.form['title'] = "Points of Interest"
    page.form['structure'] = """
        Name *= ___
        Description = ...
    """
    page.form['enable_submissions'] = False
    page.form['title_format'] = '[Name]'
    page.form['price'] = 'paid'
    page.form['price_per_submission'] = 100
    page.form['payment_method'] = 'manual'
    page = page.form.submit().follow()

    assert "Eintrag vorschlagen" not in page

    # change it to accept submissions
    page = page.click("Konfigurieren")
    page.form['enable_submissions'] = True
    page = page.form.submit().follow()

    assert "Eintrag vorschlagen" in page

    # create a submission with a missing field
    page = page.click("Eintrag vorschlagen")
    page.form['description'] = '\n'.join((
        "The Washington Monument is an obelisk on the National Mall in",
        "Washington, D.C., built to commemorate George Washington, once",
        "commander-in-chief of the Continental Army and the first President",
        "of the United States",
    ))
    page.form['submitter'] = 'info@example.org'
    page = page.form.submit()

    assert "error" in page

    # add the missing field
    page.form['name'] = 'Washingtom Monument'
    page = page.form.submit().follow()

    # check the result
    assert "error" not in page
    assert "100.00" in page
    assert "Washingtom Monument" in page
    assert "George Washington" in page

    # fix the result
    page = page.click("Bearbeiten", index=1)
    page.form['name'] = "Washington Monument"
    page = page.form.submit()

    assert "Washingtom Monument" not in page
    page = page.form.submit().follow()

    assert "DIR-" in page

    # the submission has not yet resulted in an entry
    assert 'Washington' not in client.get('/directories/points-of-interest')

    # adopt the submission through the ticket
    page = client.get('/tickets/ALL/open').click("Annehmen").follow()
    assert "Offen" in page
    assert "100.00" in page
    assert "Übernehmen" in page
    assert "info@example.org" in page
    assert "Washington" in page
    assert "National Mall" in page

    # if we adopt it it'll show up
    postgres.save()
    ticket_url = page.request.url
    accept_url = page.pyquery('.accept-link').attr('ic-post-to')
    client.post(accept_url)
    assert 'Washington' in client.get('/directories/points-of-interest')

    # the description here is a multiline field
    desc = client.app.session().query(DirectoryEntry)\
        .one().values['description']

    assert '\n' in desc
    transaction.abort()

    # if we don't, it won't
    postgres.undo(pop=False)
    client.post(page.pyquery('.delete-link').attr('ic-post-to'))
    assert 'Washington' not in client.get('/directories/points-of-interest')

    # if the structure changes we might not be able to accept the submission
    postgres.undo(pop=False)
    page = client.get('/directories/points-of-interest').click('Konfigurieren')
    page.form['structure'] = """
        Name *= ___
        Description = ...
        Category *=
            [ ] Monument
            [ ] Vista
    """
    page.form.submit()

    client.post(accept_url)

    page = client.get(ticket_url)
    assert "Der Eintrag ist nicht gültig" in page

    # in which case we can edit the submission to get it up to snuff
    page = page.click("Details bearbeiten")
    page.select_checkbox('category', "Monument")
    page.form.submit().follow()

    client.post(accept_url)

    page = client.get(ticket_url)
    assert 'Washington' in client.get('/directories/points-of-interest')

    # another way this can fail is with duplicate entries of the same name
    postgres.undo(pop=False)
    page = client.get('/directories/points-of-interest').click(
        'Eintrag', index=0)

    page.form['name'] = 'Washington Monument'
    page.form.submit()

    client.post(accept_url)

    page = client.get(ticket_url)
    assert "Ein Eintrag mit diesem Namen existiert bereits" in page

    # less severe structural changes are automatically applied
    postgres.undo(pop=False)
    page = client.get('/directories/points-of-interest').click('Konfigurieren')
    page.form['structure'] = """
        Name *= ___
        Description = ___
    """
    page.form.submit()

    client.post(accept_url)

    # the description here is no longer a multiline field
    desc = client.app.session().query(DirectoryEntry)\
        .one().values['description']

    assert '\n' not in desc
    transaction.abort()


def test_dependent_number_form(client):
    collection = FormCollection(client.app.session())
    collection.definitions.add('Profile', definition=textwrap.dedent("""
        E-Mail *= @@@
        Country =
            ( ) Switzerland
                Email *= @@@
            (x) Other
    """), type='custom')

    transaction.commit()

    page = client.get('/form/profile')
    page.form['e_mail'] = 'info@example.org'
    page = page.form.submit().follow()

    assert "Bitte überprüfen Sie Ihre Angaben" in page


def test_registration_form_hints(client):
    collection = FormCollection(client.app.session())
    collection.definitions.add('Meetup', "E-Mail *= @@@", 'custom')
    transaction.commit()

    client.login_editor()

    page = client.get('/form/meetup')
    page = page.click("Hinzufügen")

    page.form['start'] = '2018-01-01'
    page.form['end'] = '2018-01-31'
    page.form['limit_attendees'] = 'yes'
    page.form['limit'] = 2
    page.form['waitinglist'] = 'yes'
    page.form['stop'] = False
    page = page.form.submit().follow()

    assert "Der Anmeldezeitraum wurde erfolgreich hinzugefügt" in page

    # the time here is in UTC, offset is +1 hour
    with freeze_time('2017-12-31 22:59:59'):
        page = client.get('/form/meetup')
        assert "Die Anmeldung beginnt am Montag, 01. Januar 2018" in page

    with freeze_time('2017-12-31 23:00:00'):
        page = client.get('/form/meetup')
        assert "Die Anmeldung endet am Mittwoch, 31. Januar 2018" in page

    with freeze_time('2018-01-31 22:59:59'):
        page = client.get('/form/meetup')
        assert "Die Anmeldung endet am Mittwoch, 31. Januar 2018" in page

    with freeze_time('2018-01-31 23:00:00'):
        page = client.get('/form/meetup')
        assert "Die Anmeldung ist nicht mehr möglich" in page

    edit = page.click('01.01.2018 - 31.01.2018').click('Bearbeiten')
    edit.form['stop'] = True
    edit.form.submit()

    with freeze_time('2018-01-01'):
        page = client.get('/form/meetup')
        assert "Zur Zeit keine Anmeldung möglich" in page

        edit.form['stop'] = False
        edit.form.submit()

        page = client.get('/form/meetup')
        assert "Die Anmeldung endet am Mittwoch, 31. Januar 2018" in page
        assert "Die Anmeldung ist auf 2 Teilnehmer begrenzt" in page

        edit.form['waitinglist'] = 'no'
        edit.form.submit()

        page = client.get('/form/meetup')
        assert "Es sind noch 2 Plätze verfügbar" in page

        edit.form['limit'] = 1
        edit.form.submit()

        page = client.get('/form/meetup')
        assert "Es ist noch ein Platz verfügbar" in page

        page.form['e_mail'] = 'info@example.org'
        page.form.submit().follow().form.submit()

        page = client.get('/form/meetup')
        assert "Keine Plätze mehr verfügbar" in page


def test_registration_complete_after_deadline(client):
    collection = FormCollection(client.app.session())

    form = collection.definitions.add('Meetup', "E-Mail *= @@@", 'custom')
    form.add_registration_window(
        start=date(2018, 1, 1),
        end=date(2018, 1, 31),
    )

    transaction.commit()

    # the registration is started before the end of the deadline
    with freeze_time('2018-01-31 22:59:59'):
        page = client.get('/form/meetup')
        page.form['e_mail'] = 'info@example.org'
        page = page.form.submit().follow()

    # but it is completed after the deadline (no longer possible)
    with freeze_time('2018-01-31 23:00:00'):
        page = page.form.submit().follow()
        assert "Anmeldungen sind nicht mehr möglich" in page
        assert TicketCollection(client.app.session()).query().count() == 0


def test_registration_race_condition(client):
    collection = FormCollection(client.app.session())

    form = collection.definitions.add('Meetup', "E-Mail *= @@@", 'custom')
    form.add_registration_window(
        start=date(2018, 1, 1),
        end=date(2018, 1, 31),
        limit=1,
        overflow=False
    )

    transaction.commit()

    foo = client.spawn()
    bar = client.spawn()

    def fill_out_form(client):
        page = client.get('/form/meetup')
        page.form['e_mail'] = 'info@example.org'

        return page.form.submit().follow()

    def complete_form(page):
        return page.form.submit().follow()

    with freeze_time('2018-01-01'):
        foo = fill_out_form(foo)
        bar = fill_out_form(bar)

        assert "Vielen Dank für Ihre Eingabe" in complete_form(foo)
        assert "Anmeldungen sind nicht mehr möglich" in complete_form(bar)


def test_registration_change_limit_after_submissions(client):
    collection = FormCollection(client.app.session())

    form = collection.definitions.add('Meetup', "E-Mail *= @@@", 'custom')
    form.add_registration_window(
        start=date(2018, 1, 1),
        end=date(2018, 1, 31),
        limit=10,
        overflow=False
    )

    transaction.commit()

    client.login_editor()

    with freeze_time('2018-01-01'):
        for i in range(0, 3):
            page = client.get('/form/meetup')
            page.form['e_mail'] = 'info@example.org'
            page.form.submit().follow().form.submit().follow()

    page = client.get('/form/meetup').click('01.01.2018 - 31.01.2018')
    page = page.click('Bearbeiten')

    page.form['limit'] = 1
    assert "nicht tiefer sein als die Summe" in page.form.submit()

    submissions = collection.submissions.query().all()
    submissions[0].claim()
    submissions[1].claim()
    transaction.commit()

    page.form['waitinglist'] = 'yes'
    assert "nicht tiefer sein als die Anzahl" in page.form.submit()

    page.form['waitinglist'] = 'no'
    page.form['limit'] = 2
    assert "nicht tiefer sein als die Summe" in page.form.submit()

    submissions = collection.submissions.query().all()
    submissions[2].disclaim()
    transaction.commit()

    page = page.form.submit().follow()
    assert "Ihre Änderungen wurden gespeichert" in page

    submissions = collection.submissions.query().all()
    submissions[1].disclaim()
    transaction.commit()

    page = page.click('01.01.2018 - 31.01.2018').click('Bearbeiten')
    page.form['limit'] = 1
    page = page.form.submit().follow()

    assert "Ihre Änderungen wurden gespeichert" in page


def test_registration_ticket_workflow(client):
    collection = FormCollection(client.app.session())

    form = collection.definitions.add('Meetup', textwrap.dedent("""
        E-Mail *= @@@
        Name *= ___
    """), 'custom')

    form.add_registration_window(
        start=date(2018, 1, 1),
        end=date(2018, 1, 31),
        limit=10,
        overflow=False
    )

    transaction.commit()

    client.login_editor()

    def register(e_mail, name, include_data_in_email):

        with freeze_time('2018-01-01'):
            page = client.get('/form/meetup')
            page.form['e_mail'] = 'info@example.org'
            page.form['name'] = 'Foobar'
            page = page.form.submit().follow()

            page.form['send_by_email'] = include_data_in_email
            page.form.submit().follow()

        return client.get('/tickets/ALL/open').click("Annehmen").follow()

    page = register('info@example.org', 'Foobar', include_data_in_email=True)

    assert "bestätigen" in page
    assert "ablehnen" in page

    msg = client.app.smtp.sent[-1]
    assert "Ein neues Ticket wurde für Sie eröffnet" in msg
    assert "Foobar" in msg

    page = page.click("Anmeldung bestätigen").follow()

    msg = client.app.smtp.sent[-1]
    assert 'Ihre Anmeldung für "Meetup" wurde bestätigt' in msg
    assert "01.01.2018 - 31.01.2018" in msg
    assert "Foobar" in msg

    page = page.click("Anmeldung stornieren").follow()

    msg = client.app.smtp.sent[-1]
    assert 'Ihre Anmeldung für "Meetup" wurde storniert' in msg
    assert "01.01.2018 - 31.01.2018" in msg
    assert "Foobar" in msg

    page = register('info@example.org', 'Foobar', include_data_in_email=False)

    msg = client.app.smtp.sent[-1]
    assert "Ein neues Ticket wurde für Sie eröffnet" in msg
    assert "Foobar" not in msg

    page.click("Anmeldung ablehnen")

    msg = client.app.smtp.sent[-1]
    assert 'Ihre Anmeldung für "Meetup" wurde abgelehnt' in msg
    assert "01.01.2018 - 31.01.2018" in msg
    assert "Foobar" not in msg


def test_registration_not_in_front_of_queue(client):
    collection = FormCollection(client.app.session())

    form = collection.definitions.add('Meetup', "E-Mail *= @@@", 'custom')
    form.add_registration_window(
        start=date(2018, 1, 1),
        end=date(2018, 1, 31),
        limit=10,
        overflow=False
    )

    transaction.commit()

    client.login_editor()

    with freeze_time('2018-01-01'):
        for i in range(0, 2):
            page = client.get('/form/meetup')
            page.form['e_mail'] = 'info@example.org'
            page.form.submit().follow().form.submit().follow()

    page = client.get('/tickets/ALL/open').click("Annehmen", index=1).follow()
    assert "Dies ist nicht die älteste offene Eingabe" in page

    page = client.get('/tickets/ALL/open').click("Annehmen").follow()
    assert "Dies ist nicht die älteste offene Eingabe" not in page


def test_markdown_in_forms(client):
    collection = FormCollection(client.app.session())
    collection.definitions.add('Content', definition=textwrap.dedent("""
        E-Mail *= @@@
        Content = <markdown>
    """), type='custom')

    transaction.commit()

    page = client.get('/forms').click('Content')
    page.form['e_mail'] = 'info@example.org'
    page.form['content'] = '* foo\n* bar'
    page = page.form.submit().follow()

    assert '<li>foo</li>' in page
    assert '<li>bar</li>' in page


def test_exploit_markdown_in_forms(client):
    collection = FormCollection(client.app.session())
    collection.definitions.add('Content', definition=textwrap.dedent("""
        E-Mail *= @@@
        Content = <markdown>
    """), type='custom')

    transaction.commit()

    page = client.get('/forms').click('Content')
    page.form['e_mail'] = 'info@example.org'
    page.form['content'] = '<script>alert();</script>'
    page = page.form.submit().follow()

    assert '<script>alert' not in page
    assert '&lt;script&gt;alert' in page


def test_markdown_in_directories(client):
    client.login_admin()

    page = client.get('/directories').click('Verzeichnis')
    page.form['title'] = "Clubs"
    page.form['structure'] = """
        Name *= ___
        Notes = <markdown>
    """
    page.form['title_format'] = '[Name]'
    page.form['content_fields'] = 'Notes'
    page.form.submit()

    page = client.get('/directories/clubs')
    page = page.click('Eintrag', index=0)
    page.form['name'] = 'Soccer Club'
    page.form['notes'] = '* Soccer rules!'
    page.form.submit()

    assert "<li>Soccer rules" in client.get('/directories/clubs/soccer-club')


def test_search_signed_files(client_with_es):
    client = client_with_es
    client.login_admin()

    path = module_path('onegov.org', 'tests/fixtures/sample.pdf')
    with open(path, 'rb') as f:
        page = client.get('/files')
        page.form['file'] = Upload('Sample.pdf', f.read(), 'application/pdf')
        page.form.submit()

    client.app.es_indexer.process()
    client.app.es_client.indices.refresh(index='_all')

    assert 'Sample' in client.get('/search?q=Adobe')
    assert 'Sample' not in client.spawn().get('/search?q=Adobe')

    transaction.begin()
    pdf = FileCollection(client.app.session()).query().one()
    pdf.signed = True
    transaction.commit()

    client.app.es_indexer.process()
    client.app.es_client.indices.refresh(index='_all')

    assert 'Sample' in client.get('/search?q=Adobe')
    assert 'Sample' in client.spawn().get('/search?q=Adobe')


def test_sign_document(client):
    client.login_admin()

    path = module_path('onegov.org', 'tests/fixtures/sample.pdf')
    with open(path, 'rb') as f:
        page = client.get('/files')
        page.form['file'] = Upload('Sample.pdf', f.read(), 'application/pdf')
        page.form.submit()

    pdf = FileCollection(client.app.session()).query().one()

    # signatures are only used if yubikeys are used
    page = client.get(f'/storage/{pdf.id}/details')
    assert 'signature' not in page

    client.app.enable_yubikey = True

    page = client.get(f'/storage/{pdf.id}/details')
    assert 'signature' in page

    # signing only works if the given user has a yubikey setup
    def sign(client, page, token):
        rex = r"'(http://\w+/\w+/\w+/sign?[^']+)'"
        url = re.search(rex, str(page)).group(1)
        return client.post(url, {'token': token})

    assert "Bitte geben Sie Ihren Yubikey ein" in sign(client, page, '')
    assert "nicht mit einem Yubikey verknüpft" in sign(client, page, 'foobar')

    # not just any yubikey either, it has to be the one linked to the account
    transaction.begin()

    user = UserCollection(client.app.session())\
        .by_username('admin@example.org')

    user.second_factor = {
        'type': 'yubikey',
        'data': 'ccccccbcgujh'
    }

    transaction.commit()

    assert "nicht mit Ihrem Konto verknüpft" in sign(client, page, 'foobar')

    # if the key doesn't work, the signature is not applied
    with patch.object(Yubico, 'verify') as verify:
        verify.return_value = False

        assert "konnte nicht validiert werden" in sign(
            client, page, 'ccccccbcgujhingjrdejhgfnuetrgigvejhhgbkugded')

    assert not FileCollection(client.app.session()).query().one().signed

    # once the signature has been applied, it can't be repeated
    tape = module_path('onegov.org', 'tests/cassettes/ais-success.json')

    with patch.object(Yubico, 'verify') as verify:
        verify.return_value = True

        with vcr.use_cassette(tape, record_mode='none'):

            assert "signiert von admin@example.org" in sign(
                client, page, 'ccccccbcgujhingjrdejhgfnuetrgigvejhhgbkugded')

        with vcr.use_cassette(tape, record_mode='none'):

            assert "Datei hat bereits eine digital Signatur" in sign(
                client, page, 'ccccccbcgujhingjrdejhgfnuetrgigvejhhgbkugded')

    # we should at this point see some useful metadata on the file
    metadata = FileCollection(client.app.session())\
        .query().one().signature_metadata

    assert metadata['token'] == 'ccccccbcgujhingjrdejhgfnuetrgigvejhhgbkugded'
    assert metadata['signee'] == 'admin@example.org'

    # and we should see a message in the activity log
    assert 'Datei signiert' in client.get('/timeline')

    # deleting the signed file at this point should yield another message
    pdf = FileCollection(client.app.session()).query().one()
    client.get(f'/storage/{pdf.id}/details').click("Löschen")
    assert b'Signierte Datei gel\u00f6scht' in client.get('/timeline').body
