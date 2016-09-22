import onegov.core
import onegov.town

from onegov.org.testing import Client
from onegov.testing import utils


def test_view_permissions():
    utils.assert_explicit_permissions(onegov.town, onegov.town.TownApp)


def test_startpage(town_app):
    client = Client(town_app)

    links = client.get('/').pyquery('.top-bar-section a')

    assert links[0].text == 'Bildung & Gesellschaft'
    assert links[0].attrib.get('href').endswith('/themen/bildung-gesellschaft')

    assert links[1].text == 'Gewerbe & Tourismus'
    assert links[1].attrib.get('href').endswith('/themen/gewerbe-tourismus')

    assert links[2].text == 'Kultur & Freizeit'
    assert links[2].attrib.get('href').endswith('/themen/kultur-freizeit')

    assert links[3].text == 'Leben & Wohnen'
    assert links[3].attrib.get('href').endswith('/themen/leben-wohnen')

    assert links[4].text == 'Politik & Verwaltung'
    assert links[4].attrib.get('href').endswith('/themen/politik-verwaltung')

    links = client.get('/').pyquery('.homepage-tiles a')

    assert links[0].find('h3').text == 'Bildung & Gesellschaft'
    assert links[0].attrib.get('href').endswith('/themen/bildung-gesellschaft')

    assert links[1].find('h3').text == 'Gewerbe & Tourismus'
    assert links[1].attrib.get('href').endswith('/themen/gewerbe-tourismus')

    assert links[2].find('h3').text == 'Kultur & Freizeit'
    assert links[2].attrib.get('href').endswith('/themen/kultur-freizeit')

    assert links[3].find('h3').text == 'Leben & Wohnen'
    assert links[3].attrib.get('href').endswith('/themen/leben-wohnen')

    assert links[4].find('h3').text == 'Politik & Verwaltung'
    assert links[4].attrib.get('href').endswith('/themen/politik-verwaltung')

    assert links[5].find('h3').text == 'Aktuelles'
    assert links[5].attrib.get('href').endswith('/aktuelles')


def test_view_occurrences_on_startpage(town_app):
    client = Client(town_app)
    links = [
        a.text for a in client.get('/').pyquery('.homepage-panel li a')
    ]
    events = (
        '150 Jahre Govikon',
        'Alle Veranstaltungen',
        'Gemeindeversammlung',
        'MuKi Turnen',
    )
    assert set(events) <= set(links)


def test_pages_on_homepage(es_town_app):
    client = Client(es_town_app)

    client.login_editor()

    new_page = client.get('/themen/bildung-gesellschaft').click('Thema')
    new_page.form['title'] = "0xdeadbeef"
    new_page = new_page.form.submit().follow()

    assert '0xdeadbeef' not in client.get('/')

    edit_page = new_page.click('Bearbeiten')
    edit_page.form['is_visible_on_homepage'] = True
    edit_page.form.submit()

    assert '0xdeadbeef' in client.get('/')

    edit_page = new_page.click('Bearbeiten')
    edit_page.form['is_hidden_from_public'] = True
    edit_page.form.submit()

    assert '0xdeadbeef' in client.get('/')
    assert '0xdeadbeef' not in Client(es_town_app).get('/')

    client.delete(
        new_page.pyquery('a[ic-delete-from]')[0].attrib['ic-delete-from']
    )

    assert '0xdeadbeef' not in client.get('/')
