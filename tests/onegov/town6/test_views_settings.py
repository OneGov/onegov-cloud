
def test_settings(client):
    client.login_admin()

    # general settings
    settings = client.get('/general-settings')
    settings.form['reply_to'] = 'info@govikon.ch'
    settings.form['custom_css'] = 'h2 { text-decoration: underline; }'
    settings.form.submit()

    settings = client.get('/general-settings')
    assert '<style>h2 { text-decoration: underline; }</style>' in settings


def test_gever_settings(client):

    client.login_admin()
    settings = client.get('/settings').click('Gever API')
    settings.form['gever_username'] = 'foo'
    settings.form['gever_password'] = 'bar'
    settings.form['gever_endpoint'] = 'https://example.org/'
    settings.form.submit().follow()

    res = client.get('/settings').click('Gever API')
    assert res.status_code == 200
