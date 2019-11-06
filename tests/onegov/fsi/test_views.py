def test_view_homepage(client):
    homepage = client.get('/')

    assert "Informationen" in homepage
    assert "Kursverwaltung" in homepage


def test_view_courses(client):
    page = client.get('/events')
    assert 'No entries found' in page


# def test_view_courses_new(client):
#     page = client.get('/courses/new')
