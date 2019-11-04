def test_view_homepage(client):
    homepage = client.get('/')

    assert "Informationen" in homepage
    assert "Kursverwaltung" in homepage


def test_view_courses(client):
    page = client.get('/courses')
    assert 'No entries found' in page