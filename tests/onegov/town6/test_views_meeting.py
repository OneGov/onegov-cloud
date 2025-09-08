def test_meetings(client):
    client.login_admin().follow()

    # enable ris
    settings = client.get('/ris-enable')
    settings.form['ris_enabled'] = True
    settings.form.submit()

    page = client.get('/meetings')
    assert 'Sitzungen' in page
    assert 'Noch keine Sitzungen definiert' in page
    assert 'Nächste Sitzung' not in page

    # filters
    assert 'Vergangene Sitzungen' in page
    assert 'Künftige Sitzungen' in page

    # add meeting
    new = page.click('Sitzung')
    new.form['title'] = 'Test Meeting'
    new.form['address'] = 'Town Hall'
    new.form.submit()

    page = client.get('/meetings')


    # edit meeting


    # delete meeting
