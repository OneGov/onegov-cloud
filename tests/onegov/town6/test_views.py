from __future__ import annotations

import onegov.org
import transaction

from onegov.chat.collections import ChatCollection
from tests.shared import utils

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .conftest import Client


def test_view_permissions() -> None:
    utils.assert_explicit_permissions(onegov.org, onegov.org.OrgApp)


def test_notfound(client: Client) -> None:
    notfound_page = client.get('/foobar', expect_errors=True)
    assert "Seite nicht gefunden" in notfound_page
    assert notfound_page.status_code == 404


def test_links(client: Client) -> None:
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

    edit_page = link.click('Bearbeiten')
    assert edit_page.pyquery('.delete-link').text() == 'Löschen'

    client.get('/auth/logout')

    root_page = client.get(root_url)
    assert "Google" in root_page
    google = root_page.click("Google", index=0)

    assert google.status_code == 302
    assert google.location == 'https://www.google.ch'


def test_clipboard(client: Client) -> None:
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


def test_clipboard_separation(client: Client) -> None:
    client.login_admin()

    page = client.get('/topics/organisation')
    page = page.click('Kopieren')

    assert 'paste-link' in client.get('/topics/organisation')

    # new client (browser) -> new clipboard
    client = client.spawn()
    client.login_admin()

    assert 'paste-link' not in client.get('/topics/organisation')


def test_gobal_tools(client: Client) -> None:
    links = client.get('/').pyquery('.globals a')
    assert links == []

    client.login_admin()
    links = client.get('/').pyquery('.globals a')
    assert links != []


def test_top_navigation(client: Client) -> None:
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


def test_announcement(client: Client) -> None:
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


def test_search_in_header(client_with_fts: Client) -> None:
    page = client_with_fts.get("/")
    assert "Suchbegriff" in page
    page.form['q'] = 'aktuell'
    page = page.form.submit()
    assert "search-result-pages" in page


def test_create_external_link(client: Client) -> None:
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


def test_header_links(client: Client) -> None:
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


def test_chat_archive(client: Client) -> None:
    client.login_admin()

    settings = client.get('/chat-settings')
    settings.form['enable_chat'] = 'people_chat'
    settings.form.submit()

    page = client.get('/chats/+initiate')
    page.form['name'] = 'Andrew Lieu'
    page.form['email'] = 'andrew@lieu.org'
    page.form['confirmation'] = True
    page.form.submit()

    transaction.begin()
    chat = ChatCollection(client.app.session()).query().one()

    chat.chat_history = [
        {"text": "Heyhey", "time": "18:22",
         "user": "Chantal Trutmann", "userId": "customer"},
        {"text": "Guten Tag, wie kann ich Ihnen helfen?", "time": "18:25",
         "user": "admin@example.org", "userId":
             "7f9f7fb2a56f4c0eb1e63f667e0e64dc"},
        {"text": "Ich habe eine Frage zu Thema XYZ. ", "time": "18:26", "user":
            "Chantal Trutmann", "userId": "customer"}]
    chat.active = False
    transaction.commit()

    page = client.get('/chats/archive?state=archived')

    assert 'Andrew' in page


def test_chat_topics(client: Client) -> None:
    client.login_admin()

    settings = client.get('/chat-settings')
    settings.form['enable_chat'] = 'people_chat'
    settings.form['chat_topics'] = 'Steuern, Bau'
    settings.form.submit()

    page = client.get('/chats/+initiate')
    page.form['name'] = 'Andrew Lieu'
    page.form['email'] = 'andrew@lieu.org'
    page.form['topic'] = 'Steuern'
    page.form['confirmation'] = True
    page.form.submit()

    assert 'Kundenchat' in page

    anon = client.spawn()

    settings = client.get('/chat-settings')
    settings.form['chat_topics'] = ''
    settings.form.submit()

    page = anon.get('/chats/+initiate')
    assert 'Thema' not in page


def test_view_iframe_button_on_page(client: Client) -> None:
    client.login_admin().follow()

    page = client.get('/news')
    assert ('&lt;iframe src="http://localhost/news" width="100%" height="800" '
            'frameborder="0"&gt;&lt;/iframe&gt;') in page


def test_footer_settings_custom_links(client: Client) -> None:
    client.login_admin()

    # footer settings custom links
    settings = client.get('/footer-settings')
    impressum_url = 'https://my.impressum.io'
    custom_url = 'https://custom.com/1'
    custom_name = 'Custom1'

    settings.form['impressum_url'] = impressum_url
    settings.form['custom_link_1_name'] = custom_name
    settings.form['custom_link_1_url'] = custom_url
    settings.form['custom_link_2_name'] = 'Custom2'
    settings.form['custom_link_2_url'] = None

    page = settings.form.submit().follow()
    assert (f'<a class="footer-link" '
            f'href="{impressum_url}">Impressum</a>') in page
    assert (f'<a class="footer-link" '
            f'href="{custom_url}">{custom_name}</a>') in page
    assert 'Custom2' not in page


def test_footer_settings_contact_url_label(client: Client) -> None:
    client.login_admin()

    url = 'https://www.happy.coding.ch'

    # initial, no contact url set, no link
    page = client.get('/')
    assert 'mehr' not in page
    assert url not in page

    # footer settings custom contact link label
    settings = client.get('/footer-settings')
    settings.form['contact_url_label'] = 'Contact Form'
    settings.form['contact_url'] = url
    page = settings.form.submit().follow()
    assert 'Contact Form' in page
    assert url in page

    # footer settings default contact link label
    settings = client.get('/footer-settings')
    settings.form['contact_url_label'] = ''
    settings.form['contact_url'] = url
    page = settings.form.submit().follow()
    assert 'mehr' in page
    assert url in page


def test_footer_settings_opening_hours_url_label(client: Client) -> None:
    client.login_admin()

    url = 'https://www.abc.ch'

    # initial, no opening hours url set, no link
    page = client.get('/')
    assert 'mehr' not in page
    assert url not in page

    # footer settings custom opening our link label
    settings = client.get('/footer-settings')
    settings.form['opening_hours_url_label'] = 'Special abc'
    settings.form['opening_hours_url'] = url
    page = settings.form.submit().follow()
    assert 'Special abc' in page
    assert url in page

    # footer settings default opening hour link label
    settings = client.get('/footer-settings')
    settings.form['opening_hours_url_label'] = ''
    settings.form['opening_hours_url'] = url
    page = settings.form.submit().follow()
    assert 'mehr' in page
    assert url in page
