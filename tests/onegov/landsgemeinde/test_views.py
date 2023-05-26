def test_views(client_with_es):
    client_with_es.login('admin@example.org', 'hunter2')

    page = client_with_es.get('/').click('Archiv')
    assert 'Noch keine Landsgemeinden erfasst.' in page

    # add assembly
    page = page.click('Landsgemeinde')
    page.form['date'] = '2023-05-07'
    page.form['state'] = 'completed'
    page.form['overview'] = '<p>Lorem ipsum</p>'
    page = page.form.submit().follow()
    assert 'Landsgemeinde vom 07. Mai 2023' in page

    page.click('Archiv', index=0)
    assert 'Landsgemeinde vom 07. Mai 2023' in page
    page.click('Landsgemeinde vom 07. Mai 2023')

    # edit assembly
    page = page.click('Bearbeiten')
    page.form['overview'] = '<p>Lorem ipsum dolor sit amet</p>'
    page = page.form.submit().follow()
    assert '<p>Lorem ipsum dolor sit amet</p>' in page

    # add agenda item
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

    # edit agenda item
    page = page.click('Bearbeiten')
    page.form['number'] = 6
    page = page.form.submit().follow()
    assert 'Traktandum 6' in page

    # add votum
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

    # edit votum
    page = page.click('Bearbeiten', href='votum')
    page.form['person_name'] = 'Joe Quimby'
    page = page.form.submit().follow()
    assert 'Joe Quimby' in page

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
    page.click('Löschen', href='votum')
    page = page.click('Traktandum')
    assert '<p>Dolore magna aliqua.</p>' in page
    assert 'Joe Quimby' not in page

    # delete agenda item
    page.click('Löschen')
    page = page.click('Landsgemeinde')
    assert '<p>Lorem ipsum dolor sit amet</p>' in page
    assert 'Traktandum 6' not in page

    # delete landsgemeinde
    page.click('Löschen')
    page = page.click('Archiv', index=0)
    assert 'Noch keine Landsgemeinden erfasst.' in page
