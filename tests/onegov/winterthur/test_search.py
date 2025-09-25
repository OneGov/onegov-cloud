import pytest

from webtest import Upload
from tests.shared.utils import create_image


@pytest.mark.skip('Passes locally, but not in CI, skip for now')
def test_search_excluding_image(client_with_es):

    client = client_with_es
    client.login_admin()

    # Create directory
    page = client.get('/directories').click('Verzeichnis')
    page.form['title'] = 'Clubs'
    page.form['structure'] = """
                    Name *= ___
                    Location *= ___
                    Pic *= *.jpg|*.png|*.gif
                """
    page.form['content_fields'] = 'Name\nLocation\nPic'
    page.form['content_hide_labels'] = 'Pic'
    page.form['title_format'] = '[Name]'
    page.form['enable_map'] = 'entry'
    page.form['thumbnail'] = 'Pic'
    clubs = page.form.submit().follow()

    # Create club
    page = clubs.click('Eintrag', index=0)
    page.form['name'] = 'Pilatus'
    page.form['location'] = '201-B'
    page.form['pic'] = Upload('pretty-room.jpg', create_image().read())
    clubs = page.form.submit().follow()

    client.app.es_client.indices.refresh(index='_all')

    # elasticsearch
    search_page = client.get(
        '/directories/clubs?search=inline&search_query={"term"%3A"201-B"}')
    assert "Pilatus" in search_page

    search_page = client.get(
        '/directories/clubs?search=inline&search_query={"term"%3A"pretty"}')
    assert "Keine Eintr\xc3\xa4ge gefunden." not in search_page

    # postgres
    search_page = client.get(
        '/directories/clubs?search-postgres=inline'
        '&search_query={"term"%3A"201-B"}')
    assert "Pilatus" in search_page

    search_page = client.get(
        '/directories/clubs?search-postgres=inline'
        '&search_query={"term"%3A"pretty"}')
    assert "Keine Eintr\xc3\xa4ge gefunden." not in search_page
