from __future__ import annotations

from webtest import Upload
from tests.shared.utils import create_image


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from tests.shared.client import Client
    from .conftest import TestApp


def test_search_excluding_image(client_with_fts: Client[TestApp]) -> None:

    client = client_with_fts
    client.login_admin()

    # Create directory
    page = client.get('/directories').click('^Verzeichnis$')
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

    search_page = client.get(
        '/directories/clubs?search=inline&search_query={"term"%3A"201-B"}')
    assert "Pilatus" in search_page

    search_page = client.get(
        '/directories/clubs?search=inline&search_query={"term"%3A"pretty"}')
    assert "Keine Einträge gefunden." in search_page


def test_search_malicious_term(client_with_fts: Client[TestApp]) -> None:

    client = client_with_fts
    client.login_admin()

    # Create directory
    page = client.get('/directories').click('^Verzeichnis$')
    page.form['title'] = 'Clubs'
    page.form['structure'] = """
                    Name *= ___
                """
    page.form['content_fields'] = 'Name'
    page.form['title_format'] = '[Name]'
    page.form['enable_map'] = 'entry'
    clubs = page.form.submit().follow()

    # Create club
    page = clubs.click('Eintrag', index=0)
    page.form['name'] = 'Pilatus'
    clubs = page.form.submit().follow()

    search_page = client.get(
        '/directories/clubs?search=inline&search_query='
        '{"term"%3A"----------------------------------Pilatus"}'
    )
    assert "Keine Einträge gefunden." in search_page
