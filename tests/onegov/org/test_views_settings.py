from __future__ import annotations

from onegov.api.models import ApiKey
from onegov.org.theme.org_theme import HELVETICA
from xml.etree.ElementTree import tostring


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .conftest import Client


def test_settings(client: Client) -> None:
    assert client.get(
        '/general-settings', expect_errors=True
    ).status_code == 403

    client.login_admin()

    # general settings
    settings = client.get('/general-settings')
    assert client.app.font_family is None
    document = settings.pyquery

    assert document.find('input[name=name]').val() == 'Govikon'
    assert document.find('input[name=primary_color]').val() == '#006fba'
    # is not defined in org/content, but on the form as default and in the UI
    assert document.find(
        'select[name=font_family_sans_serif]').val() == HELVETICA

    settings.form['primary_color'] = '#xxx'
    settings.form['reply_to'] = 'info@govikon.ch'
    settings = settings.form.submit()

    assert "Ungültige Farbe." in settings.text

    settings.form['primary_color'] = '#ccddee'
    settings.form['reply_to'] = 'info@govikon.ch'
    settings.form.submit()

    settings = client.get('/general-settings')
    assert "Ungültige Farbe." not in settings.text
    # Form was populated with user_options default before submitting
    assert client.app.font_family == HELVETICA

    settings.form['logo_url'] = 'https://seantis.ch/logo.img'
    settings.form['reply_to'] = 'info@govikon.ch'
    settings.form['custom_css'] = 'h1 { text-decoration: underline; }'
    settings.form.submit()

    settings = client.get('/general-settings')
    assert '<img src="https://seantis.ch/logo.img"' in settings.text
    assert '<style>h1 { text-decoration: underline; }</style>' in settings.text

    # analytics settings
    settings = client.get('/analytics-settings')
    settings.form['analytics_provider_name'] = 'plausible'
    settings.form.submit()

    settings = client.get('/analytics-settings')
    assert 'src="https://dummy-plausible.test/script.js"' in settings.text

    # header settings
    color = '#006fbb'
    bg_color = '#008263'
    text = 'This is an announcement which appears on top of the page'
    settings = client.get('/header-settings')

    # test default not giving the color
    assert settings.form['left_header_color'].value == '#000000'
    assert settings.form['announcement_bg_color'].value == (
        '#FBBC05'
    )
    assert settings.form['announcement_font_color'].value == (
        '#000000'
    )

    settings.form['left_header_name'] = 'Homepage of Govikon'
    settings.form['left_header_url'] = 'https://govikon.ch'
    settings.form['left_header_rem'] = 2.5
    settings.form['left_header_color'] = color
    settings.form['announcement'] = text
    settings.form['announcement_url'] = 'https://other-town.ch'
    settings.form['announcement_bg_color'] = bg_color
    settings.form['announcement_font_color'] = color
    page = settings.form.submit().follow()
    assert (
               f'<a href="https://govikon.ch" '
               f'style="color:{color}; font-size: 2.5rem">'
           ) in page
    assert text in page
    assert '' in page
    assert (
               f'<div id="header_announcement" '
               f'style="background-color: {bg_color};">'
           ) in page
    assert (
               f'<a style="color: {color}" href="https://other-town.ch"'
           ) in page

    # module settings
    settings = client.get('/event-settings')
    assert client.app.org.event_filter_type == 'tags'
    assert settings.form['event_filter_type'].value == 'tags'
    settings.form['event_locations'] = 'loc A, loc B'
    page = settings.form.submit().follow()


def test_settings_tags(client: Client) -> None:
    client.login_admin()

    settings = client.get('/event-settings')
    settings.form.submit()
    assert client.app.org.event_locations == []

    settings = client.get('/event-settings')
    settings.form['event_locations'] = ''
    settings.form.submit()
    assert client.app.org.event_locations == []

    settings = client.get('/event-settings')
    settings.form['event_locations'] = '[]'
    settings.form.submit()
    assert client.app.org.event_locations == ['[]']
    settings = client.get('/event-settings')
    assert settings.form['event_locations'].value == '[]'  # not visible on UI

    settings = client.get('/event-settings')
    settings.form['event_locations'] = '()'
    settings.form.submit()
    assert client.app.org.event_locations == ['()']
    settings = client.get('/event-settings')
    assert settings.form['event_locations'].value == '()'  # not visible on UI

    settings.form['event_locations'] = 'Tag A, BBBB'
    settings.form.submit()
    assert client.app.org.event_locations == ['Tag A', 'BBBB']
    settings = client.get('/event-settings')
    assert settings.form['event_locations'].value == 'Tag A,BBBB'

    settings.form['event_locations'] = ['take, this', 'ignore that']
    settings.form.submit()
    assert client.app.org.event_locations == ['take', 'this']
    settings = client.get('/event-settings')
    assert settings.form['event_locations'].value == 'take,this'


def test_api_keys_create_and_delete(client: Client) -> None:
    client.login_admin()

    settings = client.get('/api-keys')
    settings.form['name'] = "My API key"
    page = settings.form.submit()
    assert 'My API key' in page

    key = client.app.session().query(ApiKey).first()
    assert key is not None
    assert key.name == "My API key"
    assert key.read_only == True

    # manually extract the link
    delete_link = tostring(page.pyquery('a.confirm')[0]).decode('utf-8')
    url = client.extract_href(delete_link)
    remove_chars = len("http://localhost")
    link = url[remove_chars:]

    client.delete(link)
    # should be gone
    assert client.app.session().query(ApiKey).first() is None


def test_switch_languages(client: Client) -> None:

    client.login_admin()

    page = client.get('/general-settings')
    assert 'Deutsch' in page
    assert 'Allemand' not in page

    page.form['locales'] = 'fr_CH'
    page.form.submit().follow()

    page = client.get('/general-settings')
    assert 'Allemand' in page
    assert 'Deutsch' not in page

    page.form['locales'] = 'it_CH'
    page.form.submit().follow()

    page = client.get('/general-settings')
    assert 'Tedesco' in page
    assert 'Allemand' not in page
    assert 'Deutsch' not in page
