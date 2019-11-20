def test_view_homepage(client):
    homepage = client.get('/')

    assert "Informationen" in homepage
    assert "Kursverwaltung" in homepage


def test_view_courses(client):
    page = client.get('/events')
    # assert 'No entries found' in page
    assert 'Keine Einträge gefunden' in page


def test_view_courses_new(client):
    page = client.get('/events/add')
    assert page
    # page.form['domain'] = 'federation'
    # page.form.submit()
