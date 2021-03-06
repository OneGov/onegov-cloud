import onegov.core
import onegov.town

from tests.shared import Client, utils


def test_view_permissions():
    utils.assert_explicit_permissions(onegov.town, onegov.town.TownApp)


def test_startpage(town_app):
    client = Client(town_app)

    links = client.get('/').pyquery('.top-bar-section a')

    assert links[0].text.strip('\n ') == 'Leben & Wohnen'
    assert links[0].attrib.get('href').endswith('/topics/leben-wohnen')

    assert links[1].text.strip('\n ') == 'Bildung & Gesellschaft'
    assert links[1].attrib.get('href').endswith('/topics/bildung-gesellschaft')

    assert links[2].text.strip('\n ') == 'Politik & Verwaltung'
    assert links[2].attrib.get('href').endswith('/topics/politik-verwaltung')

    assert links[3].text.strip('\n ') == 'Freizeit & Tourismus'
    assert links[3].attrib.get('href').endswith('/topics/freizeit-tourismus')

    assert links[4].text.strip('\n ') == 'Porträt & Wirtschaft'
    assert links[4].attrib.get('href').endswith('/topics/portraet-wirtschaft')

    links = client.get('/').pyquery('.homepage-tiles a')

    assert links[0].find('h3').text.strip('\n ') == 'Leben & Wohnen'
    assert links[0].attrib.get('href').endswith('/topics/leben-wohnen')

    assert links[1].find('h3').text.strip('\n ') == 'Bildung & Gesellschaft'
    assert links[1].attrib.get('href').endswith('/topics/bildung-gesellschaft')

    assert links[2].find('h3').text.strip('\n ') == 'Politik & Verwaltung'
    assert links[2].attrib.get('href').endswith('/topics/politik-verwaltung')

    assert links[3].find('h3').text.strip('\n ') == 'Freizeit & Tourismus'
    assert links[3].attrib.get('href').endswith('/topics/freizeit-tourismus')

    assert links[4].find('h3').text.strip('\n ') == 'Porträt & Wirtschaft'
    assert links[4].attrib.get('href').endswith('/topics/portraet-wirtschaft')


def test_view_occurrences_on_startpage(town_app):
    client = Client(town_app)
    links = [
        a.text for a in client.get('/').pyquery('.panel-links:first li a')
    ]
    events = (
        '150 Jahre Govikon',
        'Alle Veranstaltungen',
        'Gemeinsames Turnen',
        'Generalversammlung'
    )
    assert set(events) <= set(links)


def test_pages_on_homepage(es_town_app):
    client = Client(es_town_app)
    client.skip_first_form = True
    client.login_editor()

    new_page = client.get('/topics/bildung-gesellschaft').click('Thema')
    new_page.form['title'] = "0xdeadbeef"
    new_page = new_page.form.submit().follow()

    assert '0xdeadbeef' not in client.get('/')

    edit_page = new_page.click('Bearbeiten')
    edit_page.form['is_visible_on_homepage'] = True
    edit_page.form.submit()

    assert '0xdeadbeef' in client.get('/')

    edit_page = new_page.click('Bearbeiten')
    edit_page.form['access'] = 'private'
    edit_page.form.submit()

    assert '0xdeadbeef' in client.get('/')
    assert '0xdeadbeef' not in Client(es_town_app).get('/')

    client.delete(
        new_page.pyquery('a[ic-delete-from]')[0].attrib['ic-delete-from']
    )

    assert '0xdeadbeef' not in client.get('/')
