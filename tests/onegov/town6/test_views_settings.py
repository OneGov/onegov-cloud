
def test_settings(client):
    client.login_admin()

    # general settings
    settings = client.get('/general-settings')
    settings.form['reply_to'] = 'info@govikon.ch'
    settings.form['custom_css'] = 'h2 { text-decoration: underline; }'
    settings.form.submit()

    settings = client.get('/general-settings')
    assert '<style>h2 { text-decoration: underline; }</style>' in settings
