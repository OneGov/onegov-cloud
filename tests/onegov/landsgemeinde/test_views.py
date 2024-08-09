from dateutil import parser
from freezegun import freeze_time
from lxml import etree
from onegov.landsgemeinde.models import Assembly
from tests.onegov.town6.conftest import Client
from transaction import begin
from transaction import commit


def test_views(client_with_es):
    last_modified = []

    def assert_last_modified():
        response = client_with_es.head('/landsgemeinde/2023-05-07/ticker')
        last_modified.append(parser.parse(response.headers['Last-Modified']))
        assert sorted(last_modified) == last_modified
        assert len(set(last_modified)) == len(last_modified)

    client_with_es.login('admin@example.org', 'hunter2')

    page = client_with_es.get('/').click('Landsgemeinden')
    assert 'Noch keine Landsgemeinden erfasst.' in page
    assert 'Zum Liveticker' not in page

    # add assembly
    with freeze_time('2023-05-07 9:30'):
        page = page.click('Landsgemeinde', index=1)
        page.form['date'] = '2023-05-07'
        page.form['state'] = 'ongoing'
        page.form['overview'] = '<p>Lorem ipsum</p>'
        page.form['video_url'] = 'https://www.youtube.com/embed/1234'
        page.form['start_time'] = '09:30:12 AM'
        page = page.form.submit().follow()
    assert 'Landsgemeinde vom 07. Mai 2023' in page
    assert 'Zum Liveticker' in page
    assert 'https://www.youtube.com/embed/1234' in page
    assert_last_modified()

    page = client_with_es.get('/').follow()
    assert 'Landsgemeinde vom 07. Mai 2023' in page
    assert 'Zum Liveticker' not in page

    page = client_with_es.get('/landsgemeinden')
    assert 'Landsgemeinde vom 07. Mai 2023' in page
    page = page.click('Landsgemeinde vom 07. Mai 2023')

    # edit assembly
    with freeze_time('2023-05-07 9:31'):
        page = page.click('Bearbeiten')
        page.form['overview'] = '<p>Lorem ipsum dolor sit amet</p>'
        page = page.form.submit().follow()
    assert '<p>Lorem ipsum dolor sit amet</p>' in page
    assert_last_modified()

    # add agenda item
    with freeze_time('2023-05-07 9:32'):
        page = page.click('Traktandum')
        page.form['number'] = 5
        page.form['state'] = 'completed'
        page.form['title'] = 'A. consectetur adipiscing\nB. tempor incididunt'
        page.form['overview'] = '<p>Dolore magna aliqua.</p>'
        page.form['text'] = '<p>Ad minim veniam.</p>'
        page.form['resolution'] = '<p>Nostrud exercitation.</p>'
        page = page.form.submit().follow()
    assert 'Traktandum 5<br>' in page
    assert (
        '<span class="agenda-item-title">A. consectetur adipiscing<br>'
        'B. tempor incididunt</span>'
    ) in page
    assert 'A. consectetur adipiscing\nB. tempor incididunt' in page
    assert '<p>Dolore magna aliqua.</p>' in page
    assert '<p>Ad minim veniam.</p>' in page
    assert '<p>Nostrud exercitation.</p>' in page
    assert_last_modified()

    # edit agenda item
    with freeze_time('2023-05-07 9:33'):
        page = page.click('Bearbeiten')
        page.form['number'] = 6
        page.form['start_time'] = '10:42:13 AM'
        page = page.form.submit().follow()
    assert 'Traktandum 6' in page
    assert 'https://www.youtube.com/embed/1234?start=4321' in page
    assert_last_modified()

    # edit start time of assembly
    page = page.click('Landsgemeinde vom 07. Mai 2023')
    page = page.click('Bearbeiten')
    page.form['start_time'] = '09:30:14 AM'
    page = page.form.submit().follow()
    page = page.click('Traktandum 6')
    assert 'https://www.youtube.com/embed/1234?start=4319' in page

    # add custom timestamp
    page = page.click('Bearbeiten')
    page.form['number'] = 6
    page.form['video_timestamp'] = '1h2m3s'
    page = page.form.submit().follow()
    assert 'Traktandum 6' in page
    assert 'https://www.youtube.com/embed/1234?start=3723' in page

    # add votum
    with freeze_time('2023-05-07 9:34'):
        page = page.click('Wortmeldung')
        page.form['number'] = 7
        page.form['state'] = 'completed'
        page.form['person_name'] = 'Quimby'
        page.form['person_function'] = 'Mayor'
        page.form['text'] = '<p>Ullamco laboris.</p>'
        page.form['motion'] = '<p>Nisi ut aliquip.</p>'
        page.form['statement_of_reasons'] = '<p>Ex ea commodo consequat.</p>'
        page.form['video_timestamp'] = '2m3s'
        page = page.form.submit().follow()
    assert 'Quimby' in page
    assert 'Mayor' in page
    assert '<p>Ullamco laboris.</p>' in page
    assert '<p>Nisi ut aliquip.</p>' in page
    assert '<p>Ex ea commodo consequat.</p>' in page
    assert '2m3s' in page
    assert 'start=123' in page
    assert_last_modified()

    # edit votum
    with freeze_time('2023-05-07 9:35'):
        page = page.click('Bearbeiten', href='votum')
        page.form['person_name'] = 'Joe Quimby'
        page.form['video_timestamp'] = '1h2m5s'
        page = page.form.submit().follow()
    assert 'Joe Quimby' in page
    assert '1h2m5s' in page
    assert 'start=3725' in page
    assert_last_modified()

    # open data
    assert client_with_es.get('/landsgemeinde/2023-05-07/json').json
    assert client_with_es.get('/catalog.rdf', status=501)
    setting = client_with_es.get('/open-data-settings')
    setting.form['ogd_publisher_mail'] = 'staatskanzlei@govikon.ch'
    setting.form['ogd_publisher_id'] = 'staatskanzlei-govikon'
    setting.form['ogd_publisher_name'] = 'Staatskanzlei Govikon'
    setting.form.submit()
    assert len(etree.XML(client_with_es.get('/catalog.rdf').body)) == 1

    # search
    client_with_es.app.es_client.indices.refresh(index='_all')
    client = client_with_es.spawn()
    assert 'Landsgemeinde vom 07. Mai' in client.get('/search?q=ipsum')
    assert 'Landsgemeinde vom 07. Mai' in client.get('/search?q=adipiscing')
    assert 'Landsgemeinde vom 07. Mai' in client.get('/search?q=aliqua')
    assert 'Landsgemeinde vom 07. Mai' in client.get('/search?q=magna')
    assert 'Landsgemeinde vom 07. Mai' in client.get('/search?q=veniam')
    assert 'Landsgemeinde vom 07. Mai' in client.get('/search?q=nostrud')
    assert 'Landsgemeinde vom 07. Mai' in client.get('/search?q=quimby')
    assert 'Landsgemeinde vom 07. Mai' in client.get('/search?q=mayor')
    assert 'Landsgemeinde vom 07. Mai' in client.get('/search?q=laboris')
    assert 'Landsgemeinde vom 07. Mai' in client.get('/search?q=aliquip')
    assert 'Landsgemeinde vom 07. Mai' in client.get('/search?q=consequat')

    # delete votum
    with freeze_time('2023-05-07 9:36'):
        page.click('Löschen', href='votum')
        page = page.click('Traktandum 6', index=0)
    assert '<p>Dolore magna aliqua.</p>' in page
    assert 'Joe Quimby' not in page
    assert_last_modified()

    # delete agenda item
    with freeze_time('2023-05-07 9:37'):
        page.click('Löschen')
        page = page.click('Landsgemeinde', index=2)
    assert '<p>Lorem ipsum dolor sit amet</p>' in page
    assert 'Traktandum 6' not in page
    assert_last_modified()

    # delete landsgemeinde
    with freeze_time('2023-05-07 9:38'):
        page.click('Löschen')
        page = page.click('Landsgemeinden', index=0)
    assert 'Noch keine Landsgemeinden erfasst.' in page


def test_view_pages_cache(landsgemeinde_app):
    client = Client(landsgemeinde_app)

    # make sure codes != 200 are not cached
    anonymous = Client(landsgemeinde_app)
    anonymous.get('/landsgemeinde/2023-05-07/ticker', status=404)
    assert len(landsgemeinde_app.pages_cache.keys()) == 0

    # add assembly
    client.login('admin@example.org', 'hunter2')
    page = client.get('/').click('Landsgemeinden')
    page = page.click('Landsgemeinde', index=1)
    page.form['date'] = '2023-05-07'
    page.form['state'] = 'completed'
    page.form['overview'] = 'Lorem'
    page = page.form.submit()

    # make sure set-cookies are not cached
    anonymous = Client(landsgemeinde_app)
    response = anonymous.get('/landsgemeinde/2023-05-07/ticker')
    assert 'Set-Cookie' in response.headers  # session_id
    assert len(landsgemeinde_app.pages_cache.keys()) == 0

    # make sure HEAD request are cached without qs
    anonymous.head('/landsgemeinde/2023-05-07/ticker')
    assert len(landsgemeinde_app.pages_cache.keys()) == 1

    anonymous.head('/landsgemeinde/2023-05-07/ticker?now')
    assert len(landsgemeinde_app.pages_cache.keys()) == 1

    # Create cache entries
    assert 'Lorem' in anonymous.get('/landsgemeinde/2023-05-07/ticker')
    assert len(landsgemeinde_app.pages_cache.keys()) == 2

    anonymous.get('/landsgemeinde/2023-05-07/ticker?now')
    assert len(landsgemeinde_app.pages_cache.keys()) == 3

    # Modify without invalidating the cache
    begin()
    landsgemeinde_app.session().query(Assembly).one().overview = 'Ipsum'
    commit()

    assert 'Ipsum' not in anonymous.get('/landsgemeinde/2023-05-07/ticker')
    assert 'Ipsum' in client.get('/landsgemeinde/2023-05-07/ticker')

    # Modify with invalidating the cache
    edit = client.get('/landsgemeinde/2023-05-07/edit')
    edit.form['overview'] = 'Adipiscing'
    edit.form.submit()

    assert 'Adipiscing' in anonymous.get('/landsgemeinde/2023-05-07/ticker')
    assert 'Adipiscing' in client.get('/landsgemeinde/2023-05-07/ticker')


def test_view_suggestions(landsgemeinde_app):
    client = Client(landsgemeinde_app)

    client.login('admin@example.org', 'hunter2')

    page = client.get('/').click('Personen')
    page = page.click('Person', index=1)
    page.form['first_name'] = 'Hans'
    page.form['last_name'] = 'Müller'
    page.form['function'] = 'Landrat'
    page.form['profession'] = 'Landwirt'
    page.form['location_code_city'] = 'Oberurnen'
    page.form['parliamentary_group'] = 'SVP'
    page.form['political_party'] = 'jSVP'
    page = page.form.submit().follow()
    assert 'Eine neue Person wurde hinzugefügt' in page

    assert client.get('/suggestion/person/name').json == []
    assert client.get('/suggestion/person/name?term').json == []
    assert client.get('/suggestion/person/name?term=h').json == ['Hans Müller']

    assert client.get('/suggestion/person/function').json == []
    assert client.get('/suggestion/person/function?term').json == []
    assert client.get('/suggestion/person/function?term=l').json == [
        'Landrat', 'Landwirt'
    ]

    assert client.get('/suggestion/person/place').json == []
    assert client.get('/suggestion/person/place?term').json == []
    assert client.get('/suggestion/person/place?term=r').json == ['Oberurnen']

    assert client.get('/suggestion/person/political-affiliation').json == []
    assert client.get(
        '/suggestion/person/political-affiliation?term'
    ).json == []
    assert client.get(
        '/suggestion/person/political-affiliation?term=s'
    ).json == ['SVP', 'jSVP']
