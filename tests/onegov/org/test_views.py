import onegov.org
from tests.shared import utils


def test_view_permissions():
    utils.assert_explicit_permissions(onegov.org, onegov.org.OrgApp)


def test_notfound(client):
    notfound_page = client.get('/foobar', expect_errors=True)
    assert "Seite nicht gefunden" in notfound_page
    assert notfound_page.status_code == 404


def test_header_links(client):
    client.login_admin()

    page = client.get('/')
    assert 'id="header_links"' not in page

    settings = client.get('/header-settings')
    settings.form['header_links'] = '''
        {"labels":
            {"text": "Text",
             "link": "URL",
             "add": "Hinzuf\\u00fcgen",
             "remove": "Entfernen"},
         "values": []
        }
    '''
    page = settings.form.submit().follow()

    assert 'id="header_links"' not in page

    settings = client.get('/header-settings')
    settings.form['header_links'] = '''
        {"labels":
            {"text": "Text",
             "link": "URL",
             "add": "Hinzuf\\u00fcgen",
             "remove": "Entfernen"},
         "values": [
            {"text": "Govikon School",
             "link": "https://www.govikon-school.ch", "error": ""},
            {"text": "Castle Govikon",
             "link": "https://www.govikon-castle.ch", "error": ""}
         ]
        }
    '''
    page = settings.form.submit().follow()

    assert '<a href="https://www.govikon-castle.ch">Castle Govikon</a>' in page
    assert '<a href="https://www.govikon-school.ch">Govikon School</a>' in page


def test_publications_year(client):

    page = client.get('/publications?year=20263', status=400)
    assert 'Cannot decode URL parameter' in page

    page = client.get('/publications?year=0', status=400)
    assert 'Cannot decode URL parameter' in page

    page = client.get('/publications?year=2020')
    assert 'Publikationen' in page

    page = client.get('/publications')
    assert 'Publikationen' in page
