from xml.etree.ElementTree import tostring

from onegov.api.models import ApiKey


def test_gever_settings_only_https_allowed(client):

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


def test_api_keys_create_and_delete(client):

    client.login_admin()

    settings = client.get('/api-keys')
    settings.form['name'] = "My API key"
    page = settings.form.submit()
    assert 'My API key' in page

    key = client.app.session().query(ApiKey).first()
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


def test_all_settings_are_reachable(client):
    # The purpose is to identify any broken or unreachable settings links that
    # might happen if a view is missing

    client.login_admin()
    page = client.get('/settings')
    links = [
        e.attrib.get('href') for e in page.pyquery('.org-settings a[href]')
    ]

    assert all(client.get(link).status_code == 200 for link in links)


def test_general_settings(client):
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


def test_analytics_settings(client):
    # plausible
    client.login_admin()

    code = ('<script defer data-domain="govikon.ch" '
            'src="https://analytics.seantis.ch/js/script.js"></script>')
    settings = client.get('/analytics-settings')
    settings.form['analytics_code'] = code
    settings.form.submit()

    settings = client.get('/analytics-settings')
    assert 'https://analytics.seantis.ch/govikon.ch' in settings

    # matomo
    code = """
<!-- Matomo -->
<script>
  var _paq = window._paq = window._paq || [];
  _paq.push(['trackPageView']);
  _paq.push(['enableLinkTracking']);
  (function() {
    var u="//stats.seantis.ch/";
    _paq.push(['setTrackerUrl', u+'matomo.php']);
    _paq.push(['setSiteId', '28']);
    var d=document, g=d.createElement('script');
    var s=d.getElementsByTagName('script')[0];
    g.async=true; g.src=u+'matomo.js'; s.parentNode.insertBefore(g,s);
  })();
</script>
<!-- End Matomo Code -->
"""
    settings = client.get('/analytics-settings')
    settings.form['analytics_code'] = code
    settings.form.submit()

    settings = client.get('/analytics-settings')
    assert 'https://stats.seantis.ch' in settings



def test_firebase_settings(client):

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


def test_resource_settings(client):
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
