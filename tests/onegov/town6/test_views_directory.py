def test_directory_prev_next(client):
    client.login_admin()

    page = client.get('/directories').click('Verzeichnis')
    page.form['title'] = "Trainers"
    page.form['structure'] = """
        Name *= ___
    """
    page.form['title_format'] = '[Name]'
    page.form.submit()

    page = client.get('/directories/trainers').click("^Eintrag$")
    page.form['name'] = 'Emily Larlham'
    page.form.submit()

    page = client.get('/directories/trainers').click("^Eintrag$")
    page.form['name'] = 'Susan Light'
    page.form['access'] = 'private'
    page.form.submit()

    page = client.get('/directories/trainers').click("^Eintrag$")
    page.form['name'] = 'Zak George'
    page.form.submit()

    # Admins see all entries
    emily_page = client.get('/directories/trainers/emily-larlham')
    susan_page = client.get('/directories/trainers/susan-light')
    zak_page = client.get('/directories/trainers/zak-george')

    assert 'Susan Light' in emily_page
    assert 'Zak George' not in emily_page

    assert 'Emily Larlham' in susan_page
    assert 'Zak George' in susan_page

    assert 'Emily Larlham' not in zak_page
    assert 'Susan Light' in zak_page

    # Anonymous users only see public entries
    client = client.spawn()
    emily_page = client.get('/directories/trainers/emily-larlham')
    zak_page = client.get('/directories/trainers/zak-george')

    assert 'Susan Light' not in emily_page
    assert 'Zak George' in emily_page

    assert 'Emily Larlham' in zak_page
    assert 'Susan Light' not in zak_page