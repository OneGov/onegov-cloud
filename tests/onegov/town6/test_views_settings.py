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
