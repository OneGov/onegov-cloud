from __future__ import annotations

from onegov.api.models import ApiKey
from xml.etree.ElementTree import tostring


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .conftest import Client


def test_gever_settings_only_https_allowed(client: Client) -> None:

    client.login_admin()
    settings = client.get('/settings').click('Gever API')
    settings.form['gever_username'] = 'foo'
    settings.form['gever_password'] = 'bar'
    settings.form['gever_endpoint'] = 'http://example.org/'

    settings = settings.form.submit().maybe_follow()

    assert "Link muss mit 'https' beginnen" in settings

    settings.form['gever_username'] = 'foo'
    settings.form['gever_password'] = 'bar'
    settings.form['gever_endpoint'] = 'https://example.org/'

    res = client.get('/settings').click('Gever API')
    assert res.status_code == 200


def test_api_keys_create_and_delete(client: Client) -> None:

    client.login_admin()

    settings = client.get('/api-keys')
    settings.form['name'] = "My API key"
    page = settings.form.submit()
    assert 'My API key' in page

    key = client.app.session().query(ApiKey).first()
    assert key is not None
    assert key.name == "My API key"
    assert key.read_only == True

    # manually extract the link
    delete_link = tostring(page.pyquery('a.confirm')[0]).decode('utf-8')
    url = client.extract_href(delete_link)
    remove_chars = len("http://localhost")
    link = url[remove_chars:]

    client.delete(link)
    # should be gone
    assert client.app.session().query(ApiKey).first() is None


def test_all_settings_are_reachable(client: Client) -> None:
    # The purpose is to identify any broken or unreachable settings links that
    # might happen if a view is missing

    client.login_admin()
    page = client.get('/settings')
    links = [
        e.attrib.get('href') for e in page.pyquery('.org-settings a[href]')
    ]

    assert all(client.get(link).status_code == 200 for link in links)


def test_general_settings(client: Client) -> None:
    client.login_admin()

    page = client.get('/topics/themen')
    assert 'class="header-image"' not in page

    settings = client.get('/general-settings')
    settings.form['standard_image'] = 'standard_image.png'
    settings.form['page_image_position'] = 'header'
    settings.form['reply_to'] = 'info@govikon.ch'
    settings.form['custom_css'] = 'h2 { text-decoration: underline; }'
    page = settings.form.submit().follow()

    assert '<style>h2 { text-decoration: underline; }</style>' in page

    assert 'class="header-image"' in page


def test_analytics_settings(client: Client) -> None:
    # plausible
    client.login_admin()

    settings = client.get('/analytics-settings')
    settings.form['analytics_provider_name'] = 'plausible'
    settings.form['plausible_domain'] = 'govikon.ch'
    settings.form.submit()

    settings = client.get('/analytics-settings')
    assert 'src="https://dummy-plausible.test/script.js"' in settings
    assert 'href="https://dummy-plausible.test/govikon.ch"' in settings

    # matomo
    settings = client.get('/analytics-settings')
    settings.form['analytics_provider_name'] = 'matomo'
    settings.form['matomo_site_id'] = '28'
    settings.form.submit()

    settings = client.get('/analytics-settings')
    assert 'var u="https://dummy-matomo.test/";' in settings
    assert 'href="https://dummy-matomo.test/"' in settings

    # siteimprove
    settings = client.get('/analytics-settings')
    settings.form['analytics_provider_name'] = 'siteimprove'
    settings.form['siteimprove_site_id'] = '5775'
    settings.form.submit()

    settings = client.get('/analytics-settings')
    assert 'href="https://www.siteimprove.com/"' in settings
    assert (
        'src="https://siteimproveanalytics.com/js/siteanalyze_5775.js"'
    ) in settings



def test_firebase_settings(client: Client) -> None:

    client.login_admin()

    # Pretend this is real data (it's completely random)
    code = """
    {
  "type": "service_account",
  "project_id": "test-project-54321",
  "private_key_id": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0",
  "private_key": "private key",
  "client_email": "firebase-admin@test-project-54321.iam.gserviceaccount.com",
  "client_id": "123456789012345678901",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "foobar.com",
  "universe_domain": "googleapis.com"
    }
    """

    settings = client.get('/firebase')
    assert 'Übersicht Push-Benachrichtigungen' in settings

    settings.form['firebase_adminsdk_credential'] = code

    settings = settings.form.submit().maybe_follow()
    assert 'Ihre Änderungen wurden gespeichert' in settings


def test_resource_settings(client: Client) -> None:
    client.login_admin()

    settings = client.get('/settings').click('Reservationen')
    settings.form['resource_header_html'] = '<h1>foo</h1>'
    settings.form['resource_footer_html'] = '<p>bar</p>'
    assert ('Ihre Änderungen wurden gespeichert' in
            settings.form.submit().maybe_follow())

    page = client.get('/resources')
    assert 'Allgemeine Informationen zu Reservationen' in page
    assert '<h1>foo</h1>' in page
    assert '<p>bar</p>' in page
