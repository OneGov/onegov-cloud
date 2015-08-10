# -*- coding: utf-8 -*-
import onegov.core
import onegov.town
import textwrap

from datetime import datetime
from lxml.html import document_fromstring
from onegov.form import FormCollection
from onegov.libres import ResourceCollection
from onegov.testing import utils
from onegov.ticket import TicketCollection
from webtest import TestApp as Client
from webtest import Upload


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

    form_page = client.get('/formulare/neu')
    form_page.form['title'] = "My Form"
    form_page.form['lead'] = "This is a form"
    form_page.form['text'] = "There are many like it, but this one's mine"
    form_page.form['definition'] = "xxx = !!!"
    form_page = form_page.form.submit()

    assert u"Das Formular ist nicht gültig." in form_page

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

    assert client.get('/tickets', expect_errors=True).status_code == 403

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

    tickets_page = client.get('/tickets')

    assert '1 Offene Tickets' in tickets_page

    ticket_page = tickets_page.click('Annehmen').follow()

    assert '1 Tickets in Bearbeitung' in client.get('/tickets?state=pending')

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

    tickets_page = client.get('/tickets?state=closed')
    assert '1 Abgeschlossene Tickets' in tickets_page

    ticket_page = client.get(ticket_url)
    ticket_page = ticket_page.click('Ticket wieder öffnen').follow()

    assert '1 Tickets in Bearbeitung' in client.get('/tickets?state=pending')

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

    client = Client(town_app)

    url = '/reservation/foo/slots'
    assert client.get(url).json == []

    url = '/reservation/foo/slots?start=2015-08-04&end=2015-08-05'

    assert client.get(url).json == [
        {
            'start': '2015-08-04T00:00:00+02:00',
            'end': '2015-08-05T00:00:00+02:00'
        },
        {
            'start': '2015-08-05T00:00:00+02:00',
            'end': '2015-08-06T00:00:00+02:00'
        }
    ]


def test_resources(town_app):
    client = Client(town_app)

    login_page = client.get('/login')
    login_page.form.set('email', 'admin@example.org')
    login_page.form.set('password', 'hunter2')
    login_page.form.submit()

    resources = client.get('/reservationen')
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

    assert 'Besprechungsraum' in client.get('/reservationen')

    assert client.delete('/reservation/meeting-room').status_code == 200


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
