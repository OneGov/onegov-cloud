import json
import onegov.core
import onegov.org
import pytest
import re
import textwrap
import transaction

from datetime import datetime, date, timedelta
from libres.db.models import Reservation
from libres.modules.errors import AffectedReservationError
from lxml.html import document_fromstring
from onegov.core.utils import Bunch
from onegov.form import FormCollection, FormSubmission
from onegov.libres import ResourceCollection
from onegov.newsletter import RecipientCollection
from onegov.org.testing import Client
from onegov.org.testing import decode_map_value
from onegov.org.testing import encode_map_value
from onegov.org.testing import extract_href
from onegov.org.testing import get_message
from onegov.org.testing import select_checkbox
from onegov.testing import utils
from onegov.ticket import TicketCollection
from onegov.user import UserCollection
from purl import URL
from webtest import Upload


def bound_reserve(client, allocation):

    default_start = '{:%H:%M}'.format(allocation.start)
    default_end = '{:%H:%M}'.format(allocation.end)
    default_whole_day = allocation.whole_day
    resource = allocation.resource
    allocation_id = allocation.id

    def reserve(
        start=default_start,
        end=default_end,
        quota=1,
        whole_day=default_whole_day
    ):

        baseurl = '/einteilung/{}/{}/reserve'.format(
            resource,
            allocation_id
        )
        query = '?start={start}&end={end}&quota={quota}&whole_day={whole_day}'

        return client.post(baseurl + query.format(
            start=start,
            end=end,
            quota=quota,
            whole_day=whole_day and '1' or '0')
        )

    return reserve


def test_view_permissions():
    utils.assert_explicit_permissions(onegov.org, onegov.org.OrgApp)


def test_view_form_alert(org_app):

    login = Client(org_app).get('/auth/login')
    login = login.form.submit()

    assert 'Das Formular enthält Fehler' in login


def test_view_login(org_app):

    client = Client(org_app)

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


def test_view_files(org_app):

    client = Client(org_app)

    assert client.get('/dateien', expect_errors=True).status_code == 403

    client.login_admin()

    files_page = client.get('/dateien')

    assert "Noch keine Dateien hochgeladen" in files_page

    files_page.form['file'] = Upload('Test.txt', b'File content.')
    files_page = files_page.form.submit().follow()

    assert "Noch keine Dateien hochgeladen" not in files_page
    assert 'Test.txt' in files_page


def test_view_images(org_app):

    client = Client(org_app)

    assert client.get('/bilder', expect_errors=True).status_code == 403

    client.login_admin()

    images_page = client.get('/bilder')

    assert "Noch keine Bilder hochgeladen" in images_page

    images_page.form['file'] = Upload('Test.txt', b'File content')
    assert images_page.form.submit(expect_errors=True).status_code == 415

    images_page.form['file'] = Upload('Test.jpg', utils.create_image().read())
    images_page = images_page.form.submit().follow()

    assert "Noch keine Bilder hochgeladen" not in images_page


def test_login(org_app):
    client = Client(org_app)

    links = client.get('/').pyquery('.bottom-links li:first-child a')
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

    links = index_page.pyquery('.bottom-links li:first-child a')
    assert links.text() == 'Logout'

    index_page = client.get(links.attr('href')).follow()
    assert "Sie wurden ausgeloggt" in index_page.text

    links = index_page.pyquery('.bottom-links li:first-child a')
    assert links.text() == 'Login'


def test_reset_password(org_app):
    client = Client(org_app)

    links = client.get('/').pyquery('.bottom-links li:first-child a')
    assert links.text() == 'Login'
    login_page = client.get(links.attr('href'))

    request_page = login_page.click('Passwort zurücksetzen')
    assert 'Passwort zurücksetzen' in request_page.text

    request_page.form['email'] = 'someone@example.org'
    assert 'someone@example.org' in request_page.form.submit().follow()
    assert len(org_app.smtp.outbox) == 0

    request_page.form['email'] = 'admin@example.org'
    assert 'admin@example.org' in request_page.form.submit().follow()
    assert len(org_app.smtp.outbox) == 1

    message = org_app.smtp.outbox[0]
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


def test_unauthorized(org_app):
    client = Client(org_app)

    unauth_page = client.get('/einstellungen', expect_errors=True)
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


def test_notfound(org_app):
    client = Client(org_app)

    notfound_page = client.get('/foobar', expect_errors=True)
    assert "Seite nicht gefunden" in notfound_page
    assert notfound_page.status_code == 404


def test_pages(org_app):
    client = Client(org_app)

    root_url = client.get('/').pyquery('.top-bar-section a').attr('href')
    assert len(client.get(root_url).pyquery('.edit-bar')) == 0

    root_page = client.login_admin(to=root_url).follow()

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

    client.get('/auth/logout')
    root_page = client.get(root_url)

    assert len(root_page.pyquery('.edit-bar')) == 0

    assert page.pyquery('.main-title').text() == "Living in Govikon is Awful"
    assert page.pyquery('h2').text() == "Living in Govikon Really Sucks"
    assert page.pyquery('i').text().startswith("Experts say hiring more")


def test_news(org_app):
    client = Client(org_app)
    client.login_admin().follow()

    page = client.get('/aktuelles')
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

    page = client.get('/aktuelles')

    assert "We have a new homepage" in page.text
    assert "It is very good" in page.text
    assert "It is lots of fun" not in page.text

    # do not show the year in the news list if there's only one
    assert str(datetime.utcnow().year) not in page.text

    page = client.get('/aktuelles/we-have-a-new-homepage')

    client.delete(page.pyquery('a[ic-delete-from]').attr('ic-delete-from'))
    page = client.get('/aktuelles')

    assert "We have a new homepage" not in page.text
    assert "It is very good" not in page.text
    assert "It is lots of fun" not in page.text


def test_delete_pages(org_app):
    client = Client(org_app)

    root_url = client.get('/').pyquery('.top-bar-section a').attr('href')
    root_page = client.login_admin(to=root_url).follow()
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


def test_links(org_app):
    client = Client(org_app)

    root_url = client.get('/').pyquery('.top-bar-section a').attr('href')
    root_page = client.login_admin(to=root_url).follow()

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


def test_submit_form(org_app):
    collection = FormCollection(org_app.session())
    collection.definitions.add('Profile', definition=textwrap.dedent("""
        # Your Details
        First name * = ___
        Last name * = ___
        E-Mail * = @@@
    """), type='custom')

    transaction.commit()

    client = Client(org_app)
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

    tickets = TicketCollection(org_app.session()).by_handler_code('FRM')
    assert len(tickets) == 1

    assert tickets[0].title == 'Kung, Fury, kung.fury@example.org'
    assert tickets[0].group == 'Profile'


def test_pending_submission_error_file_upload(org_app):
    collection = FormCollection(org_app.session())
    collection.definitions.add('Statistics', definition=textwrap.dedent("""
        Name * = ___
        Datei * = *.txt|*.csv
    """), type='custom')
    transaction.commit()

    client = Client(org_app)
    form_page = client.get('/formulare').click('Statistics')
    form_page.form['datei'] = Upload('test.jpg', utils.create_image().read())

    form_page = form_page.form.submit().follow()
    assert 'formular-eingabe' in form_page.request.url
    assert len(form_page.pyquery('small.error')) == 2


def test_pending_submission_successful_file_upload(org_app):
    collection = FormCollection(org_app.session())
    collection.definitions.add('Statistics', definition=textwrap.dedent("""
        Name * = ___
        Datei * = *.txt|*.csv
    """), type='custom')
    transaction.commit()

    client = Client(org_app)
    form_page = client.get('/formulare').click('Statistics')
    form_page.form['datei'] = Upload('README.txt', b'1;2;3')
    form_page = form_page.form.submit().follow()

    assert "README.txt" in form_page.text
    assert "Datei ersetzen" in form_page.text
    assert "Datei löschen" in form_page.text
    assert "Datei behalten" in form_page.text

    # unfortunately we can't test more here, as webtest doesn't support
    # multiple differing fields of the same name...


def test_add_custom_form(org_app):
    client = Client(org_app)
    client.login_editor()

    # this error is not strictly line based, so there's a general error
    form_page = client.get('/formulare/neu')
    form_page.form['title'] = "My Form"
    form_page.form['lead'] = "This is a form"
    form_page.form['text'] = "There are many like it, but this one's mine"
    form_page.form['definition'] = "abc ="
    form_page = form_page.form.submit()

    assert "Das Formular ist nicht gültig." in form_page

    # this error is line based
    form_page = client.get('/formulare/neu')
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

    form_page = client.get('/formular/my-form/bearbeiten')
    form_page.form['definition'] = "Nom * = ___\nMail * = @@@"
    form_page = form_page.form.submit().follow()

    form_page.form['nom'] = 'My name'
    form_page.form['mail'] = 'my@name.com'
    form_page.form.submit().follow()


def test_add_duplicate_form(org_app):
    client = Client(org_app)
    client.login_editor()

    form_page = client.get('/formulare/neu')
    form_page.form['title'] = "My Form"
    form_page.form['lead'] = "This is a form"
    form_page.form['text'] = "There are many like it, but this one's mine"
    form_page.form['definition'] = "email *= @@@"
    form_page = form_page.form.submit().follow()

    assert "Ein neues Formular wurd hinzugefügt" in form_page

    form_page = client.get('/formulare/neu')
    form_page.form['title'] = "My Form"
    form_page.form['lead'] = "This is a form"
    form_page.form['text'] = "There are many like it, but this one's mine"
    form_page.form['definition'] = "email *= @@@"
    form_page = form_page.form.submit()

    assert "Ein Formular mit diesem Namen existiert bereits" in form_page


def test_delete_builtin_form(org_app):
    client = Client(org_app)
    builtin_form = '/formular/anmeldung'

    response = client.delete(builtin_form, expect_errors=True)
    assert response.status_code == 403

    client.login_editor()

    response = client.delete(builtin_form, expect_errors=True)
    assert response.status_code == 403


def test_delete_custom_form(org_app):
    client = Client(org_app)
    client.login_editor()

    form_page = client.get('/formulare/neu')
    form_page.form['title'] = "My Form"
    form_page.form['definition'] = "e-mail * = @@@"
    form_page = form_page.form.submit().follow()

    client.delete(
        form_page.pyquery('a.delete-link')[0].attrib['ic-delete-from'])


def test_show_uploaded_file(org_app):
    collection = FormCollection(org_app.session())
    collection.definitions.add(
        'Text', definition="File * = *.txt\nE-Mail * = @@@", type='custom')
    transaction.commit()

    client = Client(org_app)
    client.login_editor()

    form_page = client.get('/formular/text')
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


def test_hide_page(org_app):
    client = Client(org_app)
    client.login_editor()

    new_page = client.get('/themen/organisation').click('Thema')

    new_page.form['title'] = "Test"
    new_page.form['is_hidden_from_public'] = True
    page = new_page.form.submit().follow()

    anonymous = Client(org_app)
    response = anonymous.get(page.request.url, expect_errors=True)
    assert response.status_code == 403

    edit_page = page.click("Bearbeiten")
    edit_page.form['is_hidden_from_public'] = False
    page = edit_page.form.submit().follow()

    response = anonymous.get(page.request.url)
    assert response.status_code == 200


def test_hide_news(org_app):
    client = Client(org_app)
    client.login_editor()

    new_page = client.get('/aktuelles').click('Nachricht')

    new_page.form['title'] = "Test"
    new_page.form['is_hidden_from_public'] = True
    page = new_page.form.submit().follow()

    anonymous = Client(org_app)
    response = anonymous.get(page.request.url, expect_errors=True)
    assert response.status_code == 403

    edit_page = page.click("Bearbeiten")
    edit_page.form['is_hidden_from_public'] = False
    page = edit_page.form.submit().follow()

    response = anonymous.get(page.request.url)
    assert response.status_code == 200


def test_hide_form(org_app):
    client = Client(org_app)
    client.login_editor()

    form_page = client.get('/formular/anmeldung/bearbeiten')
    form_page.form['is_hidden_from_public'] = True
    page = form_page.form.submit().follow()

    anonymous = Client(org_app)
    response = anonymous.get(
        '/formular/anmeldung', expect_errors=True)
    assert response.status_code == 403

    edit_page = page.click("Bearbeiten")
    edit_page.form['is_hidden_from_public'] = False
    page = edit_page.form.submit().follow()

    response = anonymous.get(page.request.url)
    assert response.status_code == 200


def test_people_view(org_app):
    client = Client(org_app)
    client.login_editor()

    people = client.get('/personen')
    assert 'noch keine Personen' in people

    new_person = people.click('Person')
    new_person.form['first_name'] = 'Flash'
    new_person.form['last_name'] = 'Gordon'
    person = new_person.form.submit().follow()

    assert 'Gordon Flash' in person

    people = client.get('/personen')

    assert 'Gordon Flash' in people

    edit_person = person.click('Bearbeiten')
    edit_person.form['first_name'] = 'Merciless'
    edit_person.form['last_name'] = 'Ming'
    person = edit_person.form.submit().follow()

    assert 'Ming Merciless' in person

    delete_link = person.pyquery('a.delete-link').attr('ic-delete-from')
    client.delete(delete_link)

    people = client.get('/personen')
    assert 'noch keine Personen' in people


def test_with_people(org_app):
    client = Client(org_app)
    client.login_editor()

    people = client.get('/personen')

    new_person = people.click('Person')
    new_person.form['first_name'] = 'Flash'
    new_person.form['last_name'] = 'Gordon'
    new_person.form.submit()

    new_person = people.click('Person')
    new_person.form['first_name'] = 'Merciless'
    new_person.form['last_name'] = 'Ming'
    new_person.form.submit()

    new_page = client.get('/themen/organisation').click('Thema')

    assert 'Gordon Flash' in new_page
    assert 'Ming Merciless' in new_page

    new_page.form['title'] = 'About Flash'
    new_page.form['people_gordon_flash'] = True
    new_page.form['people_gordon_flash_function'] = 'Astronaut'
    edit_page = new_page.form.submit().follow().click('Bearbeiten')

    assert edit_page.form['people_gordon_flash'].value == 'y'
    assert edit_page.form['people_gordon_flash_function'].value == 'Astronaut'

    assert edit_page.form['people_ming_merciless'].value is None
    assert edit_page.form['people_ming_merciless_function'].value == ''


def test_delete_linked_person_issue_149(org_app):
    client = Client(org_app)
    client.login_editor()

    people = client.get('/personen')

    new_person = people.click('Person')
    new_person.form['first_name'] = 'Flash'
    new_person.form['last_name'] = 'Gordon'
    new_person.form.submit()

    new_page = client.get('/themen/organisation').click('Thema')
    new_page.form['title'] = 'About Flash'
    new_page.form['people_gordon_flash'] = True
    new_page.form['people_gordon_flash_function'] = 'Astronaut'
    edit_page = new_page.form.submit().follow().click('Bearbeiten')

    person = client.get('/personen').click('Gordon Flash')
    delete_link = person.pyquery('a.delete-link').attr('ic-delete-from')
    client.delete(delete_link)

    # this used to throw an error before issue 149 was fixed
    edit_page.form.submit().follow()


def test_tickets(org_app):
    client = Client(org_app)

    assert client.get(
        '/tickets/ALL/open', expect_errors=True).status_code == 403

    assert len(client.get('/').pyquery('.ticket-count')) == 0

    client.login_editor()

    assert client.get('/').pyquery('.ticket-count div').text()\
        == '0 Offene Tickets 0 Tickets in Bearbeitung'

    form_page = client.get('/formulare/neu')
    form_page.form['title'] = "Newsletter"
    form_page.form['definition'] = "E-Mail *= @@@"
    form_page = form_page.form.submit()

    client.logout()

    form_page = client.get('/formular/newsletter')
    form_page.form['e_mail'] = 'info@seantis.ch'

    assert len(org_app.smtp.outbox) == 0

    status_page = form_page.form.submit().follow().form.submit().follow()

    assert len(org_app.smtp.outbox) == 1

    message = org_app.smtp.outbox[0]
    message = message.get_payload(0).get_payload(decode=True)
    message = message.decode('iso-8859-1')

    assert 'FRM-' in message
    assert '/status' in message

    assert 'FRM-' in status_page
    assert 'Offen' in status_page

    client.login_editor()

    assert client.get('/').pyquery('.ticket-count div').text()\
        == '1 Offenes Ticket 0 Tickets in Bearbeitung'

    tickets_page = client.get('/tickets/ALL/open')
    assert len(tickets_page.pyquery('tr.ticket')) == 1

    ticket_page = tickets_page.click('Annehmen').follow()
    assert len(tickets_page.pyquery('tr.ticket')) == 1

    tickets_page = client.get('/tickets/ALL/pending')
    assert len(tickets_page.pyquery('tr.ticket')) == 1

    assert client.get('/').pyquery('.ticket-count div').text()\
        == '0 Offene Tickets 1 Ticket in Bearbeitung'

    assert 'editor@example.org' in ticket_page
    assert 'Newsletter' in ticket_page
    assert 'info@seantis.ch' in ticket_page
    assert 'In Bearbeitung' in ticket_page
    assert 'FRM-' in ticket_page

    ticket_url = ticket_page.request.path
    ticket_page = ticket_page.click('Ticket abschliessen').follow()

    assert client.get('/').pyquery('.ticket-count div').text()\
        == '0 Offene Tickets 0 Tickets in Bearbeitung'

    assert len(org_app.smtp.outbox) == 2

    message = org_app.smtp.outbox[1]
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
        == '0 Offene Tickets 1 Ticket in Bearbeitung'

    message = org_app.smtp.outbox[2]
    message = message.get_payload(0).get_payload(decode=True)
    message = message.decode('iso-8859-1')

    assert 'FRM-' in message
    assert '/status' in message


def test_resource_slots(org_app):

    resources = ResourceCollection(org_app.libres_context)
    resource = resources.add("Foo", 'Europe/Zurich')

    scheduler = resource.get_scheduler(org_app.libres_context)
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

    client = Client(org_app)

    url = '/ressource/foo/slots'
    assert client.get(url).json == []

    url = '/ressource/foo/slots?start=2015-08-04&end=2015-08-05'
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

    url = '/ressource/foo/slots?start=2015-08-06&end=2015-08-06'
    result = client.get(url).json

    assert len(result) == 1
    assert result[0]['className'] == 'event-unavailable'
    assert result[0]['title'] == "12:00 - 16:00 \nBesetzt"


def test_resources(org_app):
    client = Client(org_app)
    client.login_admin()

    resources = client.get('/ressourcen')

    new = resources.click('Raum')
    new.form['title'] = 'Meeting Room'
    resource = new.form.submit().follow()

    assert 'calendar' in resource
    assert 'Meeting Room' in resource

    edit = resource.click('Bearbeiten')
    edit.form['title'] = 'Besprechungsraum'
    edit.form.submit()

    assert 'Besprechungsraum' in client.get('/ressourcen')

    resource = client.get('/ressource/meeting-room')
    delete_link = resource.pyquery('a.delete-link').attr('ic-delete-from')

    assert client.delete(delete_link, status=200)


def test_reserved_resources_fields(org_app):
    client = Client(org_app)
    client.login_admin()

    room = client.get('/ressourcen').click('Raum')
    room.form['title'] = 'Meeting Room'
    room.form['definition'] = "Email *= @@@"
    room = room.form.submit()

    assert "'Email' ist ein reservierter Name" in room

    # fieldsets act as a namespace for field names
    room.form['definition'] = "# Title\nEmail *= @@@"
    room = room.form.submit().follow()

    assert "calendar" in room
    assert "Meeting Room" in room


def test_clipboard(org_app):
    client = Client(org_app)
    client.login_admin()

    page = client.get('/themen/organisation')
    assert 'paste-link' not in page

    page = page.click(
        'Kopieren',
        extra_environ={'HTTP_REFERER': page.request.url}
    ).follow()

    assert 'paste-link' in page

    page = page.click('Einf').form.submit().follow()
    assert '/organisation/organisation' in page.request.url


def test_clipboard_separation(org_app):
    client = Client(org_app)
    client.login_admin()

    page = client.get('/themen/organisation')
    page = page.click('Kopieren')

    assert 'paste-link' in client.get('/themen/organisation')

    # new client (browser) -> new clipboard
    client = Client(org_app)
    client.login_admin()

    assert 'paste-link' not in client.get('/themen/organisation')


def test_copy_pages_to_news(org_app):
    client = Client(org_app)
    client.login_admin()

    page = client.get('/themen/organisation')
    edit = page.click('Bearbeiten')

    edit.form['lead'] = '0xdeadbeef'
    page = edit.form.submit().follow()

    page.click('Kopieren')

    edit = client.get('/aktuelles').click('Einf')

    assert '0xdeadbeef' in edit
    page = edit.form.submit().follow()

    assert '/aktuelles/organisation' in page.request.url


def test_sitecollection(org_app):
    client = Client(org_app)

    assert client.get('/sitecollection', expect_errors=True).status_code == 403

    client.login_admin()

    collection = client.get('/sitecollection').json

    assert collection[0] == {
        'name': 'Kontakt',
        'url': 'http://localhost/themen/kontakt',
        'group': 'Themen'
    }


def test_allocations(org_app):
    client = Client(org_app)
    client.login_admin()

    # create a new daypass allocation
    new = client.get((
        '/ressource/tageskarte/neue-einteilung'
        '?start=2015-08-04&end=2015-08-05'
    ))

    new.form['daypasses'] = 1
    new.form['daypasses_limit'] = 1
    new.form.submit()

    # view the daypasses
    slots = client.get((
        '/ressource/tageskarte/slots'
        '?start=2015-08-04&end=2015-08-05'
    ))

    assert len(slots.json) == 2
    assert slots.json[0]['title'] == "Ganztägig \nVerfügbar"

    # change the daypasses
    edit = client.get(extract_href(slots.json[0]['actions'][0]))
    edit.form['daypasses'] = 2
    edit.form.submit()

    slots = client.get((
        '/ressource/tageskarte/slots'
        '?start=2015-08-04&end=2015-08-04'
    ))

    assert len(slots.json) == 1
    assert slots.json[0]['title'] == "Ganztägig \n2/2 Verfügbar"

    # try to create a new allocation over an existing one
    new = client.get((
        '/ressource/tageskarte/neue-einteilung'
        '?start=2015-08-04&end=2015-08-04'
    ))

    new.form['daypasses'] = 1
    new.form['daypasses_limit'] = 1
    new = new.form.submit()

    assert "Es besteht bereits eine Einteilung im gewünschten Zeitraum" in new

    # move the existing allocations
    slots = client.get((
        '/ressource/tageskarte/slots'
        '?start=2015-08-04&end=2015-08-05'
    ))

    edit = client.get(extract_href(slots.json[0]['actions'][0]))
    edit.form['date'] = '2015-08-06'
    edit.form.submit()

    edit = client.get(extract_href(slots.json[1]['actions'][0]))
    edit.form['date'] = '2015-08-07'
    edit.form.submit()

    # get the new slots
    slots = client.get((
        '/ressource/tageskarte/slots'
        '?start=2015-08-06&end=2015-08-07'
    ))

    assert len(slots.json) == 2

    # delete an allocation
    client.delete(extract_href(slots.json[0]['actions'][2]))

    # get the new slots
    slots = client.get((
        '/ressource/tageskarte/slots'
        '?start=2015-08-06&end=2015-08-07'
    ))

    assert len(slots.json) == 1

    # delete an allocation
    client.delete(extract_href(slots.json[0]['actions'][2]))

    # get the new slots
    slots = client.get((
        '/ressource/tageskarte/slots'
        '?start=2015-08-06&end=2015-08-07'
    ))

    assert len(slots.json) == 0


def test_allocation_times(org_app):
    client = Client(org_app)
    client.login_admin()

    new = client.get('/ressourcen').click('Raum')
    new.form['title'] = 'Meeting Room'
    new.form.submit()

    # 12:00 - 00:00
    new = client.get('/ressource/meeting-room/neue-einteilung')
    new.form['start'] = '2015-08-20'
    new.form['end'] = '2015-08-20'
    new.form['start_time'] = '12:00'
    new.form['end_time'] = '00:00'
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

    # 12:00 - 00:00 over two days
    new = client.get('/ressource/meeting-room/neue-einteilung')
    new.form['start'] = '2015-08-24'
    new.form['end'] = '2015-08-25'
    new.form['start_time'] = '12:00'
    new.form['end_time'] = '00:00'
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


def test_reserve_allocation(org_app):

    client = Client(org_app)

    # prepate the required data
    resources = ResourceCollection(org_app.libres_context)
    resource = resources.by_name('tageskarte')
    resource.definition = 'Note = ___'
    scheduler = resource.get_scheduler(org_app.libres_context)

    allocations = scheduler.allocate(
        dates=(datetime(2015, 8, 28), datetime(2015, 8, 28)),
        whole_day=True,
        quota=4,
        quota_limit=4
    )

    reserve = bound_reserve(client, allocations[0])
    transaction.commit()

    # create a reservation
    result = reserve(quota=4, whole_day=True)
    assert result.json == {'success': True}
    assert result.headers['X-IC-Trigger'] == 'rc-reservations-changed'

    # and fill out the form
    formular = client.get('/ressource/tageskarte/formular')
    formular.form['email'] = 'info@example.org'
    formular.form['note'] = 'Foobar'

    ticket = formular.form.submit().follow().click('Abschliessen').follow()

    assert 'RSV-' in ticket.text
    assert len(org_app.smtp.outbox) == 1

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
        '/ressource/tageskarte/slots'
        '?start=2015-08-28&end=2015-08-28'
    ))

    assert len(slots.json) == 1

    with pytest.raises(AffectedReservationError):
        client.delete(extract_href(slots.json[0]['actions'][2]))

    # open the created ticket
    ticket = client.get('/tickets/ALL/open').click('Annehmen').follow()

    assert 'Foobar' in ticket
    assert '28. August 2015' in ticket
    assert '4' in ticket

    # accept it
    assert 'Alle Reservationen annehmen' in ticket
    ticket = ticket.click('Alle Reservationen annehmen').follow()

    assert 'Alle Reservationen annehmen' not in ticket
    assert len(org_app.smtp.outbox) == 2

    message = org_app.smtp.outbox[1]
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
    assert org_app.session().query(Reservation).count() == 1
    assert org_app.session().query(FormSubmission).count() == 1

    link = ticket.pyquery('a.delete-link')[0].attrib['ic-get-from']
    ticket = client.get(link).follow()

    assert org_app.session().query(Reservation).count() == 0
    assert org_app.session().query(FormSubmission).count() == 0

    assert "Der hinterlegte Datensatz wurde entfernt" in ticket
    assert '28. August 2015' in ticket
    assert '4' in ticket
    assert '0xdeadbeef' in ticket

    assert len(org_app.smtp.outbox) == 3

    message = org_app.smtp.outbox[2]
    message = message.get_payload(0).get_payload(decode=True)
    message = message.decode('iso-8859-1')

    assert 'Tageskarte' in message
    assert '28. August 2015' in message
    assert '4' in message

    # close the ticket
    ticket.click('Ticket abschliessen')

    assert len(org_app.smtp.outbox) == 4


def test_reserve_allocation_partially(org_app):

    client = Client(org_app)

    # prepate the required data
    resources = ResourceCollection(org_app.libres_context)
    resource = resources.by_name('tageskarte')
    scheduler = resource.get_scheduler(org_app.libres_context)

    allocations = scheduler.allocate(
        dates=(datetime(2015, 8, 28, 10), datetime(2015, 8, 28, 14)),
        whole_day=False,
        partly_available=True
    )

    reserve = bound_reserve(client, allocations[0])
    transaction.commit()

    # create a reservation
    assert reserve('10:00', '12:00').json == {'success': True}

    # fill out the form
    formular = client.get('/ressource/tageskarte/formular')
    formular.form['email'] = 'info@example.org'

    ticket = formular.form.submit().follow().click("Abschliessen").follow()

    assert 'RSV-' in ticket.text
    assert len(org_app.smtp.outbox) == 1

    # open the created ticket
    client.login_admin()

    ticket = client.get('/tickets/ALL/open').click('Annehmen').follow()

    assert "info@example.org" in ticket
    assert "10:00" in ticket
    assert "12:00" in ticket

    # accept it
    ticket = ticket.click('Alle Reservationen annehmen').follow()

    message = org_app.smtp.outbox[1]
    message = message.get_payload(0).get_payload(decode=True)
    message = message.decode('iso-8859-1')

    assert "Tageskarte" in message
    assert "28. August 2015" in message
    assert "10:00" in message
    assert "12:00" in message

    # see if the slots are partitioned correctly
    url = '/ressource/tageskarte/slots?start=2015-08-01&end=2015-08-30'
    slots = client.get(url).json
    assert slots[0]['partitions'] == [[50.0, True], [50.0, False]]


def test_reserve_no_definition(org_app):

    client = Client(org_app)

    # prepate the required data
    resources = ResourceCollection(org_app.libres_context)
    resource = resources.by_name('tageskarte')
    scheduler = resource.get_scheduler(org_app.libres_context)

    allocations = scheduler.allocate(
        dates=(datetime(2015, 8, 28), datetime(2015, 8, 28)),
        whole_day=True,
        quota=4,
        quota_limit=4
    )

    reserve = bound_reserve(client, allocations[0])
    transaction.commit()

    # create a reservation
    result = reserve(quota=4)
    assert result.json == {'success': True}

    # fill out the reservation form
    formular = client.get('/ressource/tageskarte/formular')
    formular.form['email'] = 'info@example.org'

    ticket = formular.form.submit().follow().click('Abschliessen').follow()

    assert 'RSV-' in ticket.text
    assert len(org_app.smtp.outbox) == 1


def test_reserve_confirmation_no_definition(org_app):

    client = Client(org_app)

    resources = ResourceCollection(org_app.libres_context)
    resource = resources.by_name('tageskarte')
    scheduler = resource.get_scheduler(org_app.libres_context)

    allocations = scheduler.allocate(
        dates=(datetime(2015, 8, 28), datetime(2015, 8, 28)),
        whole_day=True,
        quota=4,
        quota_limit=4
    )

    reserve = bound_reserve(client, allocations[0])
    transaction.commit()

    # create a reservation
    assert reserve(quota=4).json == {'success': True}

    formular = client.get('/ressource/tageskarte/formular')
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


def test_reserve_confirmation_with_definition(org_app):

    client = Client(org_app)

    resources = ResourceCollection(org_app.libres_context)
    resource = resources.by_name('tageskarte')
    resource.definition = "Vorname *= ___\nNachname *= ___"

    scheduler = resource.get_scheduler(org_app.libres_context)

    allocations = scheduler.allocate(
        dates=(datetime(2015, 8, 28, 10), datetime(2015, 8, 28, 12)),
        whole_day=False,
        partly_available=True
    )
    reserve = bound_reserve(client, allocations[0])

    transaction.commit()

    # create a reservation
    assert reserve("10:30", "12:00").json == {'success': True}

    formular = client.get('/ressource/tageskarte/formular')
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


def test_reserve_session_bound(org_app):

    client = Client(org_app)

    # prepate the required data
    resources = ResourceCollection(org_app.libres_context)
    resource = resources.by_name('tageskarte')
    scheduler = resource.get_scheduler(org_app.libres_context)

    allocations = scheduler.allocate(
        dates=(datetime(2015, 8, 28), datetime(2015, 8, 28)),
        whole_day=True,
        quota=4,
        quota_limit=4
    )

    reserve = bound_reserve(client, allocations[0])
    transaction.commit()

    # create a reservation
    assert reserve(quota=4).json == {'success': True}

    formular = client.get('/ressource/tageskarte/formular')
    formular.form['email'] = 'info@example.org'

    confirm = formular.form.submit().follow()
    finalize_url = confirm.pyquery('a.button:first').attr('href')

    # make sure the finalize step can only be called by the original client
    c2 = Client(org_app)

    assert c2.get(finalize_url, expect_errors=True).status_code == 403
    assert client.get(finalize_url).follow().status_code == 200


def test_reserve_in_parallel(org_app):

    # prepate the required data
    resources = ResourceCollection(org_app.libres_context)
    resource = resources.by_name('tageskarte')
    scheduler = resource.get_scheduler(org_app.libres_context)

    allocations = scheduler.allocate(
        dates=(datetime(2015, 8, 28), datetime(2015, 8, 28)),
        whole_day=True
    )

    c1 = Client(org_app)
    c2 = Client(org_app)

    c1_reserve = bound_reserve(c1, allocations[0])
    c2_reserve = bound_reserve(c2, allocations[0])
    transaction.commit()

    # create a reservation
    assert c1_reserve().json == {'success': True}
    formular = c1.get('/ressource/tageskarte/formular')
    formular.form['email'] = 'info@example.org'
    f1 = formular.form.submit().follow()

    # create a parallel reservation
    assert c2_reserve().json == {'success': True}
    formular = c2.get('/ressource/tageskarte/formular')
    formular.form['email'] = 'info@example.org'
    f2 = formular.form.submit().follow()

    # one will win, one will lose
    assert f1.click('Abschliessen').status_code == 302
    assert "Der gewünschte Zeitraum ist nicht mehr verfügbar." in f2.click(
        'Abschliessen'
    ).follow()


def test_occupancy_view(org_app):

    # prepate the required data
    resources = ResourceCollection(org_app.libres_context)
    resource = resources.by_name('tageskarte')
    scheduler = resource.get_scheduler(org_app.libres_context)

    allocations = scheduler.allocate(
        dates=(datetime(2015, 8, 28), datetime(2015, 8, 28)),
        whole_day=True
    )

    client = Client(org_app)
    reserve = bound_reserve(client, allocations[0])
    transaction.commit()

    client.login_admin()

    # create a reservation
    assert reserve().json == {'success': True}
    formular = client.get('/ressource/tageskarte/formular')
    formular.form['email'] = 'info@example.org'
    formular.form.submit().follow().click('Abschliessen')

    ticket = client.get('/tickets/ALL/open').click('Annehmen').follow()

    # at this point, the reservation won't show up in the occupancy view
    occupancy = client.get('/ressource/tageskarte/belegung?date=20150828')
    assert len(occupancy.pyquery('.occupancy-block')) == 0

    # ..until we accept it
    ticket.click('Alle Reservationen annehmen')
    occupancy = client.get('/ressource/tageskarte/belegung?date=20150828')
    assert len(occupancy.pyquery('.occupancy-block')) == 1


def test_reservation_export_view(org_app):

    # prepate the required data
    resources = ResourceCollection(org_app.libres_context)
    resource = resources.by_name('tageskarte')
    resource.definition = "Vorname *= ___\nNachname *= ___"

    scheduler = resource.get_scheduler(org_app.libres_context)

    allocations = scheduler.allocate(
        dates=(datetime(2015, 8, 28), datetime(2015, 8, 28)),
        whole_day=True
    )

    client = Client(org_app)
    reserve = bound_reserve(client, allocations[0])
    transaction.commit()

    client.login_admin()

    # create a reservation
    assert reserve().json == {'success': True}
    formular = client.get('/ressource/tageskarte/formular')
    formular.form['email'] = 'info@example.org'
    formular.form['vorname'] = 'Charlie'
    formular.form['nachname'] = 'Carson'
    formular.form.submit().follow().click('Abschliessen')

    ticket = client.get('/tickets/ALL/open').click('Annehmen').follow()

    # at this point, the reservation won't show up in the export
    export = client.get('/ressource/tageskarte/export')
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


def test_reserve_session_separation(org_app):
    c1 = Client(org_app)
    c1.login_admin()

    c2 = Client(org_app)
    c2.login_admin()

    reserve = []

    # check both for separation by resource and by client
    for room in ('meeting-room', 'gym'):
        new = c1.get('/ressourcen').click('Raum')
        new.form['title'] = room
        new.form.submit()

        resource = org_app.libres_resources.by_name(room)
        allocations = resource.scheduler.allocate(
            dates=(datetime(2016, 4, 28, 12, 0), datetime(2016, 4, 28, 13, 0)),
            whole_day=False
        )

        reserve.append(bound_reserve(c1, allocations[0]))
        reserve.append(bound_reserve(c2, allocations[0]))
        transaction.commit()

    c1_reserve_room, c2_reserve_room, c1_reserve_gym, c2_reserve_gym = reserve

    assert c1_reserve_room().json == {'success': True}
    assert c1_reserve_gym().json == {'success': True}
    assert c2_reserve_room().json == {'success': True}
    assert c2_reserve_gym().json == {'success': True}

    for room in ('meeting-room', 'gym'):
        result = c1.get('/ressource/{}/reservations'.format(room)).json
        assert len(result) == 1

        result = c2.get('/ressource/{}/reservations'.format(room)).json
        assert len(result) == 1

    formular = c1.get('/ressource/meeting-room/formular')
    formular.form['email'] = 'info@example.org'
    formular.form.submit()

    # make sure if we confirm one reservation, only one will be written
    formular.form.submit().follow().click("Abschliessen").follow()

    resource = org_app.libres_resources.by_name('meeting-room')
    assert resource.scheduler.managed_reserved_slots().count() == 1

    result = c1.get('/ressource/meeting-room/reservations'.format(room)).json
    assert len(result) == 0

    result = c1.get('/ressource/gym/reservations'.format(room)).json
    assert len(result) == 1

    result = c2.get('/ressource/meeting-room/reservations'.format(room)).json
    assert len(result) == 1

    result = c2.get('/ressource/gym/reservations'.format(room)).json
    assert len(result) == 1


def test_reserve_multiple_allocations(org_app):
    client = Client(org_app)
    client.login_admin()

    resource = org_app.libres_resources.by_name('tageskarte')
    thursday = resource.scheduler.allocate(
        dates=(datetime(2016, 4, 28), datetime(2016, 4, 28)),
        whole_day=True
    )[0]
    friday = resource.scheduler.allocate(
        dates=(datetime(2016, 4, 29), datetime(2016, 4, 29)),
        whole_day=True
    )[0]

    reserve_thursday = bound_reserve(client, thursday)
    reserve_friday = bound_reserve(client, friday)

    transaction.commit()

    assert reserve_thursday().json == {'success': True}
    assert reserve_friday().json == {'success': True}

    formular = client.get('/ressource/tageskarte/formular')
    assert "28. April 2016" in formular
    assert "29. April 2016" in formular
    formular.form['email'] = "info@example.org"

    confirmation = formular.form.submit().follow()
    assert "28. April 2016" in confirmation
    assert "29. April 2016" in confirmation

    ticket = confirmation.click("Abschliessen").follow()
    assert 'RSV-' in ticket.text
    assert len(org_app.smtp.outbox) == 1

    ticket = client.get('/tickets/ALL/open').click('Annehmen').follow()
    assert "info@example.org" in ticket
    assert "28. April 2016" in ticket
    assert "29. April 2016" in ticket

    # accept it
    ticket.click('Alle Reservationen annehmen')

    message = org_app.smtp.outbox[1]
    message = message.get_payload(0).get_payload(decode=True)
    message = message.decode('iso-8859-1')

    assert "Tageskarte" in message
    assert "28. April 2016" in message
    assert "29. April 2016" in message

    # make sure the reservations are no longer pending
    resource = org_app.libres_resources.by_name('tageskarte')

    reservations = resource.scheduler.managed_reservations()
    assert reservations.filter(Reservation.status == 'approved').count() == 2
    assert reservations.filter(Reservation.status == 'pending').count() == 0
    assert resource.scheduler.managed_reserved_slots().count() == 2

    # now deny them
    client.get(ticket.pyquery('a.delete-link')[0].attrib['ic-get-from'])

    message = org_app.smtp.outbox[2]
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


def test_reserve_and_deny_multiple_dates(org_app):
    client = Client(org_app)
    client.login_admin()

    resource = org_app.libres_resources.by_name('tageskarte')
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

    reserve_wednesday = bound_reserve(client, wednesday)
    reserve_thursday = bound_reserve(client, thursday)
    reserve_friday = bound_reserve(client, friday)

    transaction.commit()

    assert reserve_wednesday().json == {'success': True}
    assert reserve_thursday().json == {'success': True}
    assert reserve_friday().json == {'success': True}

    formular = client.get('/ressource/tageskarte/formular')
    formular.form['email'] = "info@example.org"

    confirmation = formular.form.submit().follow()
    ticket = confirmation.click("Abschliessen").follow()
    ticket = client.get('/tickets/ALL/open').click('Annehmen').follow()

    # the resource needs to be refetched after the commit
    resource = org_app.libres_resources.by_name('tageskarte')
    assert resource.scheduler.managed_reserved_slots().count() == 3

    # deny the last reservation
    client.get(ticket.pyquery('a.delete-link')[-1].attrib['ic-get-from'])
    assert resource.scheduler.managed_reserved_slots().count() == 2

    message = get_message(org_app, 1)
    assert "abgesagt" in message
    assert "29. April 2016" in message

    # accept the others
    ticket = ticket.click('Alle Reservationen annehmen').follow()
    assert resource.scheduler.managed_reserved_slots().count() == 2

    message = get_message(org_app, 2)
    assert "angenommen" in message
    assert "27. April 2016" in message
    assert "28. April 2016" in message

    # deny the reservations that were accepted one by one
    client.get(ticket.pyquery('a.delete-link')[-1].attrib['ic-get-from'])
    assert resource.scheduler.managed_reserved_slots().count() == 1

    message = get_message(org_app, 3)
    assert "abgesagt" in message
    assert "27. April 2016" not in message
    assert "28. April 2016" in message

    ticket = client.get(ticket.request.url)
    client.get(ticket.pyquery('a.delete-link')[-1].attrib['ic-get-from'])
    assert resource.scheduler.managed_reserved_slots().count() == 0

    message = get_message(org_app, 4)
    assert "abgesagt" in message
    assert "27. April 2016" in message
    assert "28. April 2016" not in message

    ticket = client.get(ticket.request.url)
    assert "Der hinterlegte Datensatz wurde entfernt" in ticket
    assert "27. April 2016" in message
    assert "28. April 2016" not in message
    assert "29. April 2016" not in message


def test_reserve_failing_multiple(org_app):
    c1 = Client(org_app)
    c1.login_admin()

    c2 = Client(org_app)
    c2.login_admin()

    resource = org_app.libres_resources.by_name('tageskarte')
    thursday = resource.scheduler.allocate(
        dates=(datetime(2016, 4, 28), datetime(2016, 4, 28)),
        whole_day=True
    )[0]
    friday = resource.scheduler.allocate(
        dates=(datetime(2016, 4, 29), datetime(2016, 4, 29)),
        whole_day=True
    )[0]

    c1_reserve_thursday = bound_reserve(c1, thursday)
    c1_reserve_friday = bound_reserve(c1, friday)
    c2_reserve_thursday = bound_reserve(c2, thursday)
    c2_reserve_friday = bound_reserve(c2, friday)

    transaction.commit()

    assert c1_reserve_thursday().json == {'success': True}
    assert c1_reserve_friday().json == {'success': True}
    assert c2_reserve_thursday().json == {'success': True}
    assert c2_reserve_friday().json == {'success': True}

    # accept the first reservation session
    formular = c1.get('/ressource/tageskarte/formular')
    formular.form['email'] = "info@example.org"
    formular.form.submit().follow().click("Abschliessen").follow()

    ticket = c1.get('/tickets/ALL/open').click('Annehmen').follow()
    ticket.click('Alle Reservationen annehmen')

    # then try to accept the second one
    formular = c2.get('/ressource/tageskarte/formular')
    formular.form['email'] = "info@example.org"
    confirmation = formular.form.submit().follow()
    confirmation = confirmation.click("Abschliessen").follow()

    assert 'failed_reservations' in confirmation.request.url
    assert 'class="reservation failed"' in confirmation


def test_cleanup_allocations(org_app):

    # prepate the required data
    resources = ResourceCollection(org_app.libres_context)
    resource = resources.by_name('tageskarte')
    scheduler = resource.get_scheduler(org_app.libres_context)

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
    client = Client(org_app)
    client.login_admin()

    cleanup = client.get('/ressource/tageskarte').click("Aufräumen")
    cleanup.form['start'] = date(2015, 8, 31)
    cleanup.form['end'] = date(2015, 8, 1)
    cleanup = cleanup.form.submit()

    assert "Das End-Datum muss nach dem Start-Datum liegen" in cleanup

    cleanup.form['start'] = date(2015, 8, 1)
    cleanup.form['end'] = date(2015, 8, 31)
    resource = cleanup.form.submit().follow()

    assert "1 Einteilungen wurden erfolgreich entfernt" in resource


def test_view_occurrences(org_app):
    client = Client(org_app)

    def events(query=''):
        page = client.get('/veranstaltungen/?{}'.format(query))
        return [event.text for event in page.pyquery('h3 a')]

    def total_events(query=''):
        page = client.get('/veranstaltungen/?{}'.format(query))
        return int(page.pyquery('.date-range-selector-result span')[0].text)

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
    assert events(query) == ["Generalversammlung"]

    query = 'tags=Sports'
    assert tags(query) == ["Sport"]
    assert total_events(query) == 10
    assert set(events(query)) == set(["Gemeinsames Turnen", "Grümpelturnier"])

    query = 'tags=Politics&tags=Party'
    assert sorted(tags(query)) == ["Party", "Politik"]
    assert total_events(query) == 2
    assert set(events(query)) == set(["150 Jahre Govikon",
                                      "Generalversammlung"])

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


def test_view_occurrence(org_app):
    client = Client(org_app)
    events = client.get('/veranstaltungen')

    event = events.click("Generalversammlung")
    assert event.pyquery('h1.main-title').text() == "Generalversammlung"
    assert "Gemeindesaal" in event
    assert "Politik" in event
    assert "Alle Jahre wieder" in event
    assert len(event.pyquery('.occurrence-occurrences li')) == 1
    assert len(event.pyquery('.occurrence-exports h2')) == 1
    assert event.click('Diesen Termin exportieren').text.startswith(
        'BEGIN:VCALENDAR'
    )

    event = events.click("Gemeinsames Turnen", index=0)
    assert event.pyquery('h1.main-title').text() == "Gemeinsames Turnen"
    assert "Turnhalle" in event
    assert "Sport" in event
    assert "fit werden" in event
    assert len(event.pyquery('.occurrence-occurrences li')) == 9
    assert len(event.pyquery('.occurrence-exports h2')) == 2

    event.click('Diesen Termin exportieren').text.startswith('BEGIN:VCALENDAR')
    event.click('Alle Termine exportieren').text.startswith('BEGIN:VCALENDAR')


def test_submit_event(org_app):
    client = Client(org_app)
    form_page = client.get('/veranstaltungen').click("Veranstaltung melden")

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

    assert len(org_app.smtp.outbox) == 1
    message = org_app.smtp.outbox[0]
    assert message.get('to') == "test@example.org"
    message = message.get_payload(0).get_payload(decode=True)
    message = message.decode('utf-8')
    assert ticket_nr in message

    assert "Zugriff verweigert" in preview_page.form.submit(expect_errors=True)

    # Accept ticket
    client.login_editor()

    assert client.get('/').pyquery('.ticket-count div').text()\
        == "1 Offenes Ticket 0 Tickets in Bearbeitung"

    ticket_page = client.get('/tickets/ALL/open').click("Annehmen").follow()
    assert ticket_nr in ticket_page
    assert "test@example.org" in ticket_page
    assert "My Event" in ticket_page
    assert "My event is an event." in ticket_page
    assert "Location" in ticket_page
    assert "The Organizer" in ticket_page
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

    assert len(org_app.smtp.outbox) == 2
    message = org_app.smtp.outbox[1]
    assert message.get('to') == "test@example.org"
    message = message.get_payload(0).get_payload(decode=True)
    message = message.decode('utf-8')
    assert "My Event" in message
    assert "My event is an event." in message
    assert "Location" in message
    assert "Ausstellung" in message
    assert "Gastronomie" in message
    assert "The Organizer" in message
    assert "{} 18:00-22:00".format(start_date.strftime('%d.%m.%Y')) in message
    for days in range(5):
        assert (start_date + timedelta(days=days)).strftime('%d.%m.%Y') in \
            message
    assert "Ihre Veranstaltung wurde angenommen" in message
    assert ticket_nr in message

    # Close ticket
    ticket_page.click("Ticket abschliessen").follow()

    assert len(org_app.smtp.outbox) == 3
    message = org_app.smtp.outbox[2]
    assert message.get('to') == "test@example.org"
    message = message.get_payload(0).get_payload(decode=True)
    message = message.decode('utf-8')
    assert ticket_nr in message


def test_edit_event(org_app):
    client = Client(org_app)

    # Submit and publish an event
    form_page = client.get('/veranstaltungen').click("Veranstaltung melden")
    event_date = date.today() + timedelta(days=1)
    form_page.form['email'] = "test@example.org"
    form_page.form['title'] = "My Ewent"
    form_page.form['location'] = "Lokation"
    form_page.form['organizer'] = "Organixator"
    form_page.form['start_date'] = event_date.isoformat()
    form_page.form['start_time'] = "18:00"
    form_page.form['end_time'] = "22:00"
    form_page.form.submit().follow().form.submit().follow()

    client.login_editor()

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


def test_delete_event(org_app):
    client = Client(org_app)

    # Submit and publish an event
    form_page = client.get('/veranstaltungen').click("Veranstaltung melden")
    event_date = date.today() + timedelta(days=1)
    form_page.form['email'] = "test@example.org"
    form_page.form['title'] = "My Event"
    form_page.form['organizer'] = "Organizer"
    form_page.form['location'] = "Location"
    form_page.form['start_date'] = event_date.isoformat()
    form_page.form['start_time'] = "18:00"
    form_page.form['end_time'] = "22:00"
    form_page.form.submit().follow().form.submit().follow()

    client.login_editor()

    ticket_page = client.get('/tickets/ALL/open').click("Annehmen").follow()
    ticket_page = ticket_page.click("Veranstaltung annehmen").follow()
    ticket_nr = ticket_page.pyquery('.ticket-number').text()

    assert "My Event" in client.get('/veranstaltungen')

    # Try to delete a submitted event directly
    event_page = client.get('/veranstaltungen').click("My Event")

    assert "Diese Veranstaltung kann nicht gelöscht werden." in \
        event_page.pyquery('a.delete-link')[0].values()

    # Delete the event via the ticket
    delete_link = ticket_page.pyquery('a.delete-link').attr('ic-delete-from')
    client.delete(delete_link)

    assert len(org_app.smtp.outbox) == 3
    message = org_app.smtp.outbox[2]
    assert message.get('to') == "test@example.org"
    message = message.get_payload(0).get_payload(decode=True)
    message = message.decode('utf-8')
    assert "My Event" in message
    assert "Ihre Veranstaltung musste leider abgelehnt werden" in message
    assert ticket_nr in message

    assert "My Event" not in client.get('/veranstaltungen')

    # Delete a non-submitted event
    event_page = client.get('/veranstaltungen').click("Generalversammlung")
    assert "Möchten Sie die Veranstaltung wirklich löschen?" in \
        event_page.pyquery('a.delete-link')[0].values()

    delete_link = event_page.pyquery('a.delete-link').attr('ic-delete-from')
    client.delete(delete_link)

    assert "Generalversammlung" not in client.get('/veranstaltungen')


def test_basic_search(es_org_app):
    client = Client(es_org_app)
    client.login_admin()

    add_news = client.get('/aktuelles').click('Nachricht')
    add_news.form['title'] = "Now supporting fulltext search"
    add_news.form['lead'] = "It is pretty awesome"
    add_news.form['text'] = "Much <em>wow</em>"
    news = add_news.form.submit().follow()

    es_org_app.es_client.indices.refresh(index='_all')

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
    assert "fulltext" in Client(es_org_app).get('/suche?q=fulltext')
    edit_news = news.click("Bearbeiten")
    edit_news.form['is_hidden_from_public'] = True
    edit_news.form.submit()

    es_org_app.es_client.indices.refresh(index='_all')

    assert "Now supporting" not in Client(es_org_app).get('/suche?q=fulltext')
    assert "Now supporting" in client.get('/suche?q=fulltext')


def test_view_search_is_limiting(es_org_app):
    # ensures that the search doesn't just return all results
    # a regression that occured for anonymous uses only

    client = Client(es_org_app)
    client.login_admin()

    add_news = client.get('/aktuelles').click('Nachricht')
    add_news.form['title'] = "Foobar"
    add_news.form['lead'] = "Foobar"
    add_news.form.submit()

    add_news = client.get('/aktuelles').click('Nachricht')
    add_news.form['title'] = "Deadbeef"
    add_news.form['lead'] = "Deadbeef"
    add_news.form.submit()

    es_org_app.es_client.indices.refresh(index='_all')

    root_page = client.get('/')
    root_page.form['q'] = "Foobar"
    search_page = root_page.form.submit()

    assert "1 Resultat" in search_page

    client.logout()

    root_page = client.get('/')
    root_page.form['q'] = "Foobar"
    search_page = root_page.form.submit()

    assert "1 Resultat" in search_page


def test_basic_autocomplete(es_org_app):
    client = Client(es_org_app)

    client.login_editor()

    people = client.get('/personen')

    new_person = people.click('Person')
    new_person.form['first_name'] = 'Flash'
    new_person.form['last_name'] = 'Gordon'
    new_person.form.submit()

    es_org_app.es_client.indices.refresh(index='_all')
    assert client.get('/suche/suggest?q=Go').json == ["Gordon Flash"]
    assert client.get('/suche/suggest?q=Fl').json == []


def test_unsubscribe_link(org_app):

    client = Client(org_app)

    user = UserCollection(org_app.session()).by_username('editor@example.org')
    assert user.data is None

    request = Bunch(identity_secret=org_app.identity_secret, app=org_app)

    token = org_app.request_class.new_url_safe_token(request, {
        'user': 'editor@example.org'
    }, salt='unsubscribe')

    client.get('/unsubscribe?token={}'.format(token))
    page = client.get('/')
    assert "abgemeldet" in page

    user = UserCollection(org_app.session()).by_username('editor@example.org')
    assert user.data['daily_ticket_statistics'] == False

    token = org_app.request_class.new_url_safe_token(request, {
        'user': 'unknown@example.org'
    }, salt='unsubscribe')

    page = client.get(
        '/unsubscribe?token={}'.format(token), expect_errors=True)
    assert page.status_code == 403

    token = org_app.request_class.new_url_safe_token(request, {
        'user': 'editor@example.org'
    }, salt='foobar')

    page = client.get(
        '/unsubscribe?token={}'.format(token), expect_errors=True)
    assert page.status_code == 403


def test_newsletters_crud(org_app):

    client = Client(org_app)
    client.login_editor()

    newsletter = client.get('/newsletters')
    assert 'Es wurden noch keine Newsletter versendet' in newsletter

    new = newsletter.click('Newsletter')
    new.form['title'] = "Our town is AWESOME"
    new.form['lead'] = "Like many of you, I just love our town..."

    select_checkbox(new, "occurrences", "150 Jahre Govikon")
    select_checkbox(new, "occurrences", "Gemeinsames Turnen")

    newsletter = new.form.submit().follow()

    assert newsletter.pyquery('h1').text() == "Our town is AWESOME"
    assert "Like many of you" in newsletter
    assert "Gemeinsames Turnen" in newsletter
    assert "Turnhalle" in newsletter
    assert "150 Jahre Govikon" in newsletter
    assert "Sportanlage" in newsletter

    edit = newsletter.click("Bearbeiten")
    edit.form['title'] = "I can't even"
    select_checkbox(edit, "occurrences", "150 Jahre Govikon", checked=False)

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
    assert "noch keine Newsletter" in Client(org_app).get('/newsletters')

    delete_link = newsletter.pyquery('a.delete-link').attr('ic-delete-from')
    client.delete(delete_link)

    newsletters = client.get('/newsletters')
    assert "noch keine Newsletter" in newsletters


def test_newsletter_signup(org_app):

    client = Client(org_app)

    page = client.get('/newsletters')
    page.form['address'] = 'asdf'
    page = page.form.submit()

    assert 'Ungültig' in page

    page.form['address'] = 'info@example.org'
    page.form.submit()

    assert len(org_app.smtp.outbox) == 1

    # make sure double submissions don't result in multiple e-mails
    page.form.submit()
    assert len(org_app.smtp.outbox) == 1

    message = org_app.smtp.outbox[0]
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
    assert len(org_app.smtp.outbox) == 1

    # unsubscribing does not result in an e-mail either
    assert "falsches Token" in client.get(
        illegal.replace('/confirm', '/unsubscribe')
    ).follow()
    assert "erfolgreich abgemeldet" in client.get(
        confirm.replace('/confirm', '/unsubscribe')
    ).follow()

    # no e-mail is sent when unsubscribing
    assert len(org_app.smtp.outbox) == 1

    # however, we can now signup again
    page.form.submit()
    assert len(org_app.smtp.outbox) == 2


def test_newsletter_subscribers_management(org_app):

    client = Client(org_app)

    page = client.get('/newsletters')
    page.form['address'] = 'info@example.org'
    page.form.submit()

    assert len(org_app.smtp.outbox) == 1

    message = org_app.smtp.outbox[0]
    message = message.get_payload(0).get_payload(decode=True)
    message = message.decode('utf-8')

    confirm = re.search(r'Anmeldung bestätigen\]\(([^\)]+)', message).group(1)
    assert "info@example.org wurde erfolgreich" in client.get(confirm).follow()

    client.login_editor()

    subscribers = client.get('/abonnenten')
    assert "info@example.org" in subscribers

    unsubscribe = subscribers.pyquery('a[ic-get-from]').attr('ic-get-from')
    result = client.get(unsubscribe).follow()
    assert "info@example.org wurde erfolgreich abgemeldet" in result


def test_newsletter_send(org_app):
    client = Client(org_app)
    anon = Client(org_app)

    client.login_editor()

    # add a newsletter
    new = client.get('/newsletters').click('Newsletter')
    new.form['title'] = "Our town is AWESOME"
    new.form['lead'] = "Like many of you, I just love our town..."

    select_checkbox(new, "news", "Willkommen bei OneGov")
    select_checkbox(new, "occurrences", "150 Jahre Govikon")
    select_checkbox(new, "occurrences", "Gemeinsames Turnen")

    newsletter = new.form.submit().follow()

    # add some recipients the quick wqy
    recipients = RecipientCollection(org_app.session())
    recipients.add('one@example.org', confirmed=True)
    recipients.add('two@example.org', confirmed=True)
    recipients.add('xxx@example.org', confirmed=False)

    transaction.commit()

    assert "2 Abonnenten registriert" in client.get('/newsletters')

    # send the newsletter to one recipient
    send = newsletter.click('Senden')
    assert "Dieser Newsletter wurde noch nicht gesendet." in send
    assert "one@example.org" in send
    assert "two@example.org" in send
    assert "xxx@example.org" not in send

    len(send.pyquery('input[name="recipients"]')) == 2

    select_checkbox(send, 'recipients', 'one@example.org', checked=True)
    select_checkbox(send, 'recipients', 'two@example.org', checked=False)

    newsletter = send.form.submit().follow()

    assert '"Our town is AWESOME" wurde an 1 Empfänger gesendet' in newsletter

    page = anon.get('/newsletters')
    assert "gerade eben" in page

    # the send form should now look different
    send = newsletter.click('Senden')

    assert "Zum ersten Mal gesendet gerade eben." in send
    assert "Dieser Newsletter wurde an 1 Abonnenten gesendet." in send
    assert "one@example.org" in send
    assert "two@example.org" in send
    assert "xxx@example.org" not in send

    assert len(send.pyquery('input[name="recipients"]')) == 1
    assert len(send.pyquery('.previous-recipients li')) == 1

    # send to the other mail adress
    send = send.form.submit().follow().click("Senden")
    assert "von allen Abonnenten empfangen" in send

    # make sure the mail was sent correctly
    assert len(org_app.smtp.outbox) == 2

    message = org_app.smtp.outbox[0]
    message = message.get_payload(0).get_payload(decode=True)
    message = message.decode('utf-8')

    assert "Our town is AWESOME" in message
    assert "Like many of you" in message

    web = re.search(r'Web-Version anzuzeigen.\]\(([^\)]+)', message).group(1)
    assert web.endswith('/newsletter/our-town-is-awesome')

    # make sure the unconfirm link is different for each mail
    unconfirm_1 = re.search(r'abzumelden.\]\(([^\)]+)', message).group(1)

    message = org_app.smtp.outbox[1]
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


def test_map_default_view(org_app):
    client = Client(org_app)
    client.login_admin()

    settings = client.get('/einstellungen')

    assert decode_map_value(settings.form['default_map_view'].value) == {
        'lat': None, 'lon': None, 'zoom': None
    }

    settings.form['default_map_view'] = encode_map_value({
        'lat': 47, 'lon': 8, 'zoom': 12
    })
    settings = settings.form.submit()

    assert decode_map_value(settings.form['default_map_view'].value) == {
        'lat': 47, 'lon': 8, 'zoom': 12
    }

    edit = client.get('/editor/edit/page/1')
    assert 'data-default-lat="47"' in edit
    assert 'data-default-lon="8"' in edit
    assert 'data-default-zoom="12"' in edit


def test_map_set_marker(org_app):
    client = Client(org_app)
    client.login_admin()

    edit = client.get('/editor/edit/page/1')
    assert decode_map_value(edit.form['coordinates'].value) == {
        'lat': None, 'lon': None, 'zoom': None
    }
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


def test_manage_album(org_app):
    client = Client(org_app)
    client.login_editor()

    albums = client.get('/fotoalben')
    assert "Noch keine Fotoalben" in albums

    new = albums.click('Fotoalbum')
    new.form['title'] = "Comicon 2016"
    new.form.submit()

    albums = client.get('/fotoalben')
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


def test_settings(org_app):
    client = Client(org_app)

    assert client.get('/einstellungen', expect_errors=True).status_code == 403

    client.login_admin()

    settings_page = client.get('/einstellungen')
    document = settings_page.pyquery

    assert document.find('input[name=name]').val() == 'Govikon'
    assert document.find('input[name=primary_color]').val() == '#006fba'

    settings_page.form['primary_color'] = '#xxx'
    settings_page.form['reply_to'] = 'info@govikon.ch'
    settings_page = settings_page.form.submit()

    assert "Ungültige Farbe." in settings_page.text

    settings_page.form['primary_color'] = '#ccddee'
    settings_page.form['reply_to'] = 'info@govikon.ch'
    settings_page = settings_page.form.submit()

    assert "Ungültige Farbe." not in settings_page.text

    settings_page.form['logo_url'] = 'https://seantis.ch/logo.img'
    settings_page.form['reply_to'] = 'info@govikon.ch'
    settings_page = settings_page.form.submit()

    assert '<img src="https://seantis.ch/logo.img"' in settings_page.text

    settings_page.form['homepage_image_1'] = "http://images/one"
    settings_page.form['homepage_image_2'] = "http://images/two"
    settings_page = settings_page.form.submit()

    assert 'http://images/one' in settings_page
    assert 'http://images/two' in settings_page

    settings_page.form['analytics_code'] = '<script>alert("Hi!");</script>'
    settings_page = settings_page.form.submit()
    assert '<script>alert("Hi!");</script>' in settings_page.text


def test_registration_honeypot(org_app):
    client = Client(org_app)

    register = client.get('/auth/register')
    register.form['username'] = 'spam@example.org'
    register.form['password'] = 'p@ssw0rd'
    register.form['confirm'] = 'p@ssw0rd'
    register.form['roboter_falle'] = 'buy pills now'

    assert "Das Feld ist nicht leer" in register.form.submit()


def test_registration(org_app):
    client = Client(org_app)

    register = client.get('/auth/register')
    register.form['username'] = 'user@example.org'
    register.form['password'] = 'p@ssw0rd'
    register.form['confirm'] = 'p@ssw0rd'

    assert "Vielen Dank" in register.form.submit().follow()

    message = get_message(org_app, 0, 1)
    assert "Anmeldung bestätigen" in message

    url = re.search(r'href="[^"]+">Anmeldung bestätigen</a>', message).group()
    url = extract_href(url)

    faulty = URL(url).query_param('token', 'asdf').as_string()

    assert "Ungültiger Aktivierungscode" in client.get(faulty).follow()
    assert "Konto wurde aktiviert" in client.get(url).follow()
    assert "Konto wurde bereits aktiviert" in client.get(url).follow()

    logged_in = client.login('user@example.org', 'p@ssw0rd').follow()
    assert "eingeloggt" in logged_in


def test_disabled_registration(org_app):
    client = Client(org_app)
    org_app.settings.org.enable_user_registration = False

    assert client.get('/auth/register', expect_errors=True).status_code == 404


def test_disabled_yubikey(org_app):
    client = Client(org_app)
    client.login_admin()

    org_app.settings.org.enable_yubikey = False
    assert 'YubiKey' not in client.get('/auth/login')
    assert 'YubiKey' not in client.get('/benutzerverwaltung')

    org_app.settings.org.enable_yubikey = True
    assert 'YubiKey' in client.get('/auth/login')
    assert 'YubiKey' in client.get('/benutzerverwaltung')


def test_disable_users(org_app):
    client = Client(org_app)
    client.login_admin()

    users = client.get('/benutzerverwaltung')
    assert 'admin@example.org' in users
    assert 'editor@example.org' in users

    editor = users.click('Bearbeiten', index=1)
    editor.form['active'] = False
    editor.form.submit()

    login = Client(org_app).login_editor()
    assert login.status_code == 200

    editor = users.click('Bearbeiten', index=1)
    editor.form['role'] = 'member'
    editor.form['active'] = True
    editor.form.submit()

    login = Client(org_app).login_editor()
    assert login.status_code == 302


def test_change_role(org_app):
    client = Client(org_app)
    client.login_admin()

    org_app.settings.org.enable_yubikey = True

    editor = client.get('/benutzerverwaltung').click('Bearbeiten', index=1)
    assert "müssen zwingend einen YubiKey" in editor.form.submit()

    editor.form['role'] = 'member'
    assert editor.form.submit().status_code == 302

    editor.form['role'] = 'admin'
    editor.form['active'] = False
    assert editor.form.submit().status_code == 302

    editor.form['role'] = 'admin'
    editor.form['active'] = True
    editor.form['yubikey'] = 'cccccccdefgh'
    assert editor.form.submit().status_code == 302

    org_app.settings.org.enable_yubikey = False
    editor.form['role'] = 'admin'
    editor.form['active'] = True
    editor.form['yubikey'] = ''
    assert editor.form.submit().status_code == 302


def test_unique_yubikey(org_app):
    client = Client(org_app)
    client.login_admin()

    org_app.settings.org.enable_yubikey = True

    users = client.get('/benutzerverwaltung')
    admin = users.click('Bearbeiten', index=0)
    editor = users.click('Bearbeiten', index=1)

    admin.form['yubikey'] = 'cccccccdefgh'
    assert admin.form.submit().status_code == 302

    editor.form['yubikey'] = 'cccccccdefgh'
    assert "bereits von admin@example.org verwendet" in editor.form.submit()

    # make sure the current owner can save its own yubikey
    admin = users.click('Bearbeiten', index=0)
    assert admin.form.submit().status_code == 302


def test_add_new_user(org_app):
    client = Client(org_app)
    client.login_admin()

    org_app.settings.org.enable_yubikey = True

    new = client.get('/benutzerverwaltung').click('Benutzer', index=0)
    new.form['username'] = 'admin@example.org'

    assert "existiert bereits" in new.form.submit()

    new.form['username'] = 'member@example.org'
    new.form['role'] = 'admin'

    assert "müssen zwingend einen YubiKey" in new.form.submit()

    new.form['role'] = 'member'
    added = new.form.submit()

    assert "Passwort" in added
    password = added.pyquery('.panel strong').text()

    login = Client(org_app).get('/auth/login')
    login.form['username'] = 'member@example.org'
    login.form['password'] = password
    assert login.form.submit().status_code == 302


def test_edit_user_settings(org_app):
    client = Client(org_app)
    client.login_admin()

    org_app.settings.org.enable_yubikey = False

    new = client.get('/benutzerverwaltung').click('Benutzer', index=0)
    new.form['username'] = 'new@example.org'
    new.form['role'] = 'member'
    new.form.submit()

    users = UserCollection(org_app.session())
    assert not users.by_username('new@example.org').data

    edit = client.get('/benutzerverwaltung').click('Bearbeiten', index=2)
    assert "new@example.org" in edit

    edit.form.get('daily_ticket_statistics').checked = False
    edit.form.submit()

    assert users.by_username('new@example.org').data == {
        'daily_ticket_statistics': False
    }


def test_homepage(org_app):
    with org_app.update_org() as org:
        org.meta['homepage_cover'] = "<b>0xdeadbeef</b>"
        org.meta['homepage_structure'] = """
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

    client = Client(org_app)
    homepage = client.get('/')

    assert '<b>0xdeadbeef</b>' in homepage
    assert '<h2>Veranstaltungen</h2>' in homepage
