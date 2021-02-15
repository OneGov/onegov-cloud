from onegov.org.theme.org_theme import HELVETICA


def test_settings(client):

    assert client.get('/general-settings', expect_errors=True)\
        .status_code == 403

    client.login_admin()

    # general settings
    settings = client.get('/general-settings')
    assert client.app.font_family is None
    document = settings.pyquery

    assert document.find('input[name=name]').val() == 'Govikon'
    assert document.find('input[name=primary_color]').val() == '#006fba'
    # is not defined in org/content, but on the form as default and in the UI
    assert document.find(
        'select[name=font_family_sans_serif]').val() == HELVETICA

    settings.form['primary_color'] = '#xxx'
    settings.form['reply_to'] = 'info@govikon.ch'
    settings = settings.form.submit()

    assert "Ungültige Farbe." in settings.text

    settings.form['primary_color'] = '#ccddee'
    settings.form['reply_to'] = 'info@govikon.ch'
    settings.form.submit()

    settings = client.get('/general-settings')
    assert "Ungültige Farbe." not in settings.text
    # Form was populated with user_options default before submitting
    assert client.app.font_family == HELVETICA

    settings.form['logo_url'] = 'https://seantis.ch/logo.img'
    settings.form['reply_to'] = 'info@govikon.ch'
    settings.form.submit()

    settings = client.get('/general-settings')
    assert '<img src="https://seantis.ch/logo.img"' in settings.text

    # homepage settings
    settings = client.get('/homepage-settings')
    settings.form['homepage_image_1'] = "http://images/one"
    settings.form['homepage_image_2'] = "http://images/two"
    settings.form.submit()

    settings = client.get('/homepage-settings')
    assert 'http://images/one' in settings
    assert 'http://images/two' in settings

    # analytics settings
    settings = client.get('/analytics-settings')
    settings.form['analytics_code'] = '<script>alert("Hi!");</script>'
    settings.form.submit()

    settings = client.get('/analytics-settings')
    assert '<script>alert("Hi!");</script>' in settings.text

    color = '#006fbb'
    settings = client.get('/header-settings')
    settings.form['left_header_name'] = 'Homepage of Govikon'
    settings.form['left_header_url'] = 'https://govikon.ch'
    settings.form['left_header_rem'] = 2.5
    settings.form['left_header_color'] = color
    page = settings.form.submit().follow()

    assert f'<a href="https://govikon.ch" ' \
           f'style="color:{color}; font-size: 2.5rem">' in page


def test_switch_languages(client):

    client.login_admin()

    page = client.get('/general-settings')
    assert 'Deutsch' in page
    assert 'Allemand' not in page

    page.form['locales'] = 'fr_CH'
    page.form.submit().follow()

    page = client.get('/general-settings')
    assert 'Allemand' in page
    assert 'Deutsch' not in page
