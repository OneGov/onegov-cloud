import onegov.core
import onegov.org
from pytest import mark
from tests.shared import utils


def test_view_permissions():
    utils.assert_explicit_permissions(onegov.org, onegov.org.OrgApp)


def test_notfound(client):
    notfound_page = client.get('/foobar', expect_errors=True)
    assert "Seite nicht gefunden" in notfound_page
    assert notfound_page.status_code == 404


def test_links(client):
    root_url = client.get('/').pyquery('.side-navigation a').attr('href')
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


def test_gobal_tools(client):
    links = client.get('/').pyquery('.globals a')
    assert links == []

    client.login_admin()
    links = client.get('/').pyquery('.globals a')
    assert links != []


def test_top_navigation(client):
    links = client.get('/').pyquery('.side-navigation a span')
    assert links.text() == 'Organisation Themen Kontakt Aktuelles'

    client.login_admin()

    # Set all pages to private
    page = client.get('/editor/edit/page/1')
    page.form['access'] = 'private'
    page = page.form.submit().follow()
    page = client.get('/editor/edit/page/2')
    page.form['access'] = 'private'
    page = page.form.submit().follow()
    page = client.get('/editor/edit/page/3')
    page.form['access'] = 'private'
    page = page.form.submit().follow()
    page = client.get('/editor/edit/news/4')
    page.form['access'] = 'private'
    page = page.form.submit().follow()

    # Make sure the admin still sees the navigation icon
    page = client.get('/')
    assert 'fas fa-bars' in page
    # And the visitor doesn't
    visitor = client.spawn()
    page = visitor.get('/')
    assert 'fas fa-bars' not in page


def test_announcement(client):
    client.login_admin()

    color = '#006fbb'
    bg_color = '#008263'
    text = 'This is an announcement which appears on top of the page'
    settings = client.get('/header-settings')

    # test default not giving the color
    assert settings.form['announcement_bg_color'].value == (
        '#FBBC05'
    )
    assert settings.form['announcement_font_color'].value == (
        '#000000'
    )

    settings.form['announcement'] = text
    settings.form['announcement_url'] = 'https://other-town.ch'
    settings.form['announcement_bg_color'] = bg_color
    settings.form['announcement_font_color'] = color
    page = settings.form.submit().follow()

    assert text in page
    assert (
        f'<div id="header_announcement" '
        f'style="background-color: {bg_color};">'
    ) in page
    assert (
        f'<a style="color: {color}" href="https://other-town.ch"'
    ) in page


@mark.skip('Passes locally, but not in CI, skip for now')
def test_search_in_header(client_with_es):
    page = client_with_es.get("/")
    client_with_es.app.es_client.indices.refresh(index='_all')
    assert "Suchbegriff" in page
    page.form['q'] = 'aktuell'
    page = page.form.submit()
    assert "search-result-news" in page


def test_create_external_link(client):
    client.login_admin()
    resources = client.get('/resources')
    forms = client.get('/forms')

    # Create new external resource
    resource = resources.click('Externer Reservationslink')
    resource.form['title'] = 'Room 12b'
    resource.form['lead'] = 'It is a very beautiful room.'
    resource.form['url'] = 'https://seantis.ch'
    resources = resource.form.submit().follow()

    # Create new external form
    form = forms.click('Externes Formular')
    form.form['title'] = 'Birth certificate request'
    form.form['lead'] = 'This is an important form.'
    form.form['url'] = 'https://seantis.ch'
    forms = form.form.submit().follow()

    # Check if the new external links are where they belong
    assert 'Room 12b' in resources
    assert 'Room 12b' not in forms

    assert 'Birth certificate request' in forms
    assert 'Birth certificate request' not in resources


def test_header_links(client):
    client.login_admin()

    page = client.get('/')
    assert 'id="header_links"' not in page

    settings = client.get('/header-settings')
    settings.form['header_links'] = '''
        {"labels":
            {"text": "Text",
             "link": "URL",
             "add": "Hinzuf\\u00fcgen",
             "remove": "Entfernen"},
         "values": []
        }
    '''
    page = settings.form.submit().follow()

    assert 'id="header_links"' not in page

    settings = client.get('/header-settings')
    settings.form['header_links'] = '''
        {"labels":
            {"text": "Text",
             "link": "URL",
             "add": "Hinzuf\\u00fcgen",
             "remove": "Entfernen"},
         "values": [
            {"text": "Govikon School",
             "link": "https://www.govikon-school.ch", "error": ""},
            {"text": "Castle Govikon",
             "link": "https://www.govikon-castle.ch", "error": ""}
         ]
        }
    '''
    page = settings.form.submit().follow()

    assert '<a href="https://www.govikon-castle.ch">Castle Govikon</a>' in page
    assert '<a href="https://www.govikon-school.ch">Govikon School</a>' in page


def test_header_image(client):
    client.login_admin()

    page = client.get('/topics/themen')
    assert 'class="header-image"' not in page

    settings = client.get('/general-settings')
    settings.form['standard_image'] = 'standard_image.png'
    settings.form['page_image_position'] = 'header'
    page = settings.form.submit().follow()

    assert 'class="header-image"' in page
