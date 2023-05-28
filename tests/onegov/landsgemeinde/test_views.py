from dateutil import parser
from freezegun import freeze_time


def test_views(client_with_es):
    last_modified = []

    def assert_last_modified():
        response = client_with_es.head('/landsgemeinde/2023-05-07/ticker')
        last_modified.append(parser.parse(response.headers['Last-Modified']))
        assert sorted(last_modified) == last_modified
        assert len(set(last_modified)) == len(last_modified)

    client_with_es.login('admin@example.org', 'hunter2')

    page = client_with_es.get('/').click('Archiv')
    assert 'Noch keine Landsgemeinden erfasst.' in page

    # add assembly
    with freeze_time('2023-05-07 9:30'):
        page = page.click('Landsgemeinde')
        page.form['date'] = '2023-05-07'
        page.form['state'] = 'completed'
        page.form['overview'] = '<p>Lorem ipsum</p>'
        page = page.form.submit().follow()
    assert 'Landsgemeinde vom 07. Mai 2023' in page
    assert_last_modified()

    page.click('Archiv', index=0)
    assert 'Landsgemeinde vom 07. Mai 2023' in page
    page.click('Landsgemeinde vom 07. Mai 2023')

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
    assert (
        'Traktandum 5<br>'
        '<small>A. consectetur adipiscing<br>B. tempor incididunt</small>'
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
        page = page.form.submit().follow()
    assert 'Traktandum 6' in page
    assert_last_modified()

    # add votum
    with freeze_time('2023-05-07 9:34'):
        page = page.click('Wortmeldung')
        page.form['number'] = 7
        page.form['state'] = 'completed'
        page.form['person_name'] = 'Quimby'
        page.form['person_function'] = 'Mayor'
        page.form['person_political_affiliation'] = 'Liberals'
        page.form['person_place'] = 'Springfield'
        page.form['text'] = '<p>Ullamco laboris.</p>'
        page.form['motion'] = '<p>Nisi ut aliquip.</p>'
        page.form['statement_of_reasons'] = '<p>Ex ea commodo consequat.</p>'
        page = page.form.submit().follow()
    assert 'Quimby' in page
    assert 'Mayor' in page
    assert 'Liberals' in page
    assert 'Springfield' in page
    assert '<p>Ullamco laboris.</p>' in page
    assert '<p>Nisi ut aliquip.</p>' in page
    assert '<p>Ex ea commodo consequat.</p>' in page
    assert_last_modified()

    # edit votum
    with freeze_time('2023-05-07 9:35'):
        page = page.click('Bearbeiten', href='votum')
        page.form['person_name'] = 'Joe Quimby'
        page = page.form.submit().follow()
    assert 'Joe Quimby' in page
    assert_last_modified()

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
    assert 'Landsgemeinde vom 07. Mai' in client.get('/search?q=liberals')
    assert 'Landsgemeinde vom 07. Mai' in client.get('/search?q=springfield')
    assert 'Landsgemeinde vom 07. Mai' in client.get('/search?q=laboris')
    assert 'Landsgemeinde vom 07. Mai' in client.get('/search?q=aliquip')
    assert 'Landsgemeinde vom 07. Mai' in client.get('/search?q=consequat')

    # delete votum
    with freeze_time('2023-05-07 9:36'):
        page.click('Löschen', href='votum')
        page = page.click('Traktandum')
    assert '<p>Dolore magna aliqua.</p>' in page
    assert 'Joe Quimby' not in page
    assert_last_modified()

    # delete agenda item
    with freeze_time('2023-05-07 9:37'):
        page.click('Löschen')
        page = page.click('Landsgemeinde')
    assert '<p>Lorem ipsum dolor sit amet</p>' in page
    assert 'Traktandum 6' not in page
    assert_last_modified()

    # delete landsgemeinde
    with freeze_time('2023-05-07 9:38'):
        page.click('Löschen')
        page = page.click('Archiv', index=0)
    assert 'Noch keine Landsgemeinden erfasst.' in page
