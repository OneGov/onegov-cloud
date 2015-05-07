# -*- coding: utf-8 -*-
import onegov.core
import onegov.town

from mock import patch
from morepath import setup
from onegov.testing import utils
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
    assert u"E-Mail Adresse" in response
    assert u"Passwort" in response

    assert 'userid' not in client.cookies
    assert 'role' not in client.cookies
    assert 'application_id' not in client.cookies
    assert client.get('/logout', expect_errors=True).status_code == 403

    response.form.set('email', 'admin@example.org')
    response = response.form.submit()
    assert response.status_code == 200
    assert u"E-Mail Adresse" in response
    assert u"Passwort" in response
    assert u"Dieses Feld wird benötigt." in response

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

    images_page.form['file'] = Upload('Test.txt', utils.create_image().read())
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
    settings_page = settings_page.form.submit()

    assert u"Ungültige Farbe." in settings_page.text

    settings_page.form['primary_color'] = '#ccddee'
    settings_page = settings_page.form.submit()

    assert u"Ungültige Farbe." not in settings_page.text

    settings_page.form['logo_url'] = 'https://seantis.ch/logo.img'
    settings_page = settings_page.form.submit()

    assert '<img src="https://seantis.ch/logo.img"' in settings_page.text

    settings_page.form['homepage_images'] = """
        http://images/one
        http://images/two
    """
    settings_page = settings_page.form.submit()

    assert 'http://images/one' in settings_page
    assert 'http://images/two' in settings_page


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
