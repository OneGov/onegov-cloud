import onegov.core
import onegov.org
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


def test_announcement(client):
    client.login_admin()

    color = '#006fbb'
    bg_color = '#008263'
    text = 'This is an announcement which appears on top of the page'
    settings = client.get('/header-settings')

    # test default not giving the color
    assert settings.form['left_header_announcement_bg_color'].value == (
        '#FBBC05'
    )
    assert settings.form['left_header_announcement_font_color'].value == (
        '#000000'
    )

    settings.form['left_header_announcement'] = text
    settings.form['left_header_announcement_bg_color'] = bg_color
    settings.form['left_header_announcement_font_color'] = color
    page = settings.form.submit().follow()

    assert text in page
    assert (
        f'<div id="announcement" style="color: {color}; '
        f'background-color: {bg_color};">'
    ) in page
