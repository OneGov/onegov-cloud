import transaction

from webtest import Upload
from onegov.core.utils import Bunch
from onegov.directory import DirectoryCollection, DirectoryConfiguration
from onegov.org.models import ExtendedDirectory
from onegov.org.upgrade import enable_directory_search
from tests.shared.utils import create_image


from typing import cast, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.upgrade import UpgradeContext
    from tests.shared.client import Client
    from .conftest import TestApp


def test_inline_event_search(client: Client[TestApp]) -> None:
    resp = client.get(
        '/events?search=inline' '&search_query={"term"%3A"natur"}'
    )
    assert resp.status_int == 200


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


def test_directory_search_toggle(client: Client[TestApp]) -> None:
    client.login_admin()

    def create_directory(title: str, enable_search: bool) -> None:
        page = client.get('/directories').click('^Verzeichnis$')
        page.form['title'] = title
        page.form['structure'] = 'Name *= ___'
        page.form['title_format'] = '[Name]'
        page.form['enable_search'] = enable_search
        page.form.submit().follow()

    create_directory('Clubs', enable_search=True)
    create_directory('Bars', enable_search=False)

    assert client.get('/directories/clubs').pyquery('#inline-search')
    assert not client.get('/directories/bars').pyquery('#inline-search')

    # the search box stays hidden even when search is forced into the url
    assert not client.get(
        '/directories/bars?search=inline').pyquery('#inline-search')


def test_directory_search_reset(client_with_fts: Client[TestApp]) -> None:
    client = client_with_fts
    client.login_admin()

    # Create directory with two entries
    page = client.get('/directories').click('^Verzeichnis$')
    page.form['title'] = 'Clubs'
    page.form['structure'] = 'Name *= ___'
    page.form['title_format'] = '[Name]'
    page.form.submit().follow()

    for name in ('Pilatus', 'Rigi'):
        page = client.get('/directories/clubs').click('Eintrag', index=0)
        page.form['name'] = name
        page.form.submit().follow()

    # a search filters down to the matching entry
    filtered = client.get(
        '/directories/clubs?search=inline&search_query={"term"%3A"Pilatus"}')
    assert 'Pilatus' in filtered
    assert 'Rigi' not in filtered

    # the reset button navigates to the unfiltered directory, showing all
    reset = client.get('/directories/clubs')
    assert 'Pilatus' in reset
    assert 'Rigi' in reset


def test_directory_search_enabled_by_migration(
    client: Client[TestApp],
) -> None:
    session = client.app.session()
    directories: DirectoryCollection[ExtendedDirectory]
    directories = DirectoryCollection(session, type='extended')
    directory = directories.add(
        title='Clubs',
        structure='Name *= ___',
        configuration=DirectoryConfiguration(title='[Name]'),
    )
    # a directory created before the feature has no enable_search flag
    assert directory.enable_search is None
    transaction.commit()

    # without the flag the search box is hidden
    assert not client.get('/directories/clubs').pyquery('#inline-search')

    # the migration enables search on all existing directories
    session = client.app.session()
    enable_directory_search(cast('UpgradeContext', Bunch(session=session)))
    transaction.commit()

    directories = DirectoryCollection(session, type='extended')
    migrated = directories.by_name('clubs')
    assert migrated is not None
    assert migrated.enable_search is True
    assert client.get('/directories/clubs').pyquery('#inline-search')
