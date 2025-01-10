from io import BytesIO
from webtest import Upload
from xlsxwriter import Workbook

from onegov.api.models import ApiKey
from onegov.page import Page
from onegov.org.theme.org_theme import HELVETICA
from xml.etree.ElementTree import tostring
from onegov.org.models import SiteCollection


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
    settings.form['custom_css'] = 'h1 { text-decoration: underline; }'
    settings.form.submit()

    settings = client.get('/general-settings')
    assert '<img src="https://seantis.ch/logo.img"' in settings.text
    assert '<style>h1 { text-decoration: underline; }</style>' in settings.text

    # analytics settings
    settings = client.get('/analytics-settings')
    settings.form['analytics_code'] = '<script>alert("Hi!");</script>'
    settings.form.submit()

    settings = client.get('/analytics-settings')
    assert '<script>alert("Hi!");</script>' in settings.text

    # header settings
    color = '#006fbb'
    bg_color = '#008263'
    text = 'This is an announcement which appears on top of the page'
    settings = client.get('/header-settings')

    # test default not giving the color
    assert settings.form['left_header_color'].value == '#000000'
    assert settings.form['announcement_bg_color'].value == (
        '#FBBC05'
    )
    assert settings.form['announcement_font_color'].value == (
        '#000000'
    )

    settings.form['left_header_name'] = 'Homepage of Govikon'
    settings.form['left_header_url'] = 'https://govikon.ch'
    settings.form['left_header_rem'] = 2.5
    settings.form['left_header_color'] = color
    settings.form['announcement'] = text
    settings.form['announcement_url'] = 'https://other-town.ch'
    settings.form['announcement_bg_color'] = bg_color
    settings.form['announcement_font_color'] = color
    page = settings.form.submit().follow()
    assert (
        f'<a href="https://govikon.ch" '
        f'style="color:{color}; font-size: 2.5rem">'
    ) in page
    assert text in page
    assert '' in page
    assert (
        f'<div id="header_announcement" '
        f'style="background-color: {bg_color};">'
    ) in page
    assert (
        f'<a style="color: {color}" href="https://other-town.ch"'
    ) in page

    # module settings
    settings = client.get('/event-settings')
    assert client.app.org.event_filter_type == 'tags'
    assert settings.form['event_filter_type'].value == 'tags'


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

    page.form['locales'] = 'it_CH'
    page.form.submit().follow()

    page = client.get('/general-settings')
    assert 'Tedesco' in page
    assert 'Allemand' not in page
    assert 'Deutsch' not in page


def create_test_replacement_xlsx(
    replacement_pairs: list[tuple[str, str]]
) -> BytesIO:
    file = BytesIO()
    workbook = Workbook(file)
    worksheet = workbook.add_worksheet('Replacements')
    for row, (original, replacement) in enumerate(replacement_pairs, start=1):
        worksheet.write_string(row, 0, original)
        worksheet.write_string(row, 1, replacement)

    workbook.close()
    file.seek(0)
    return file


def test_migrate_links(client):
    session = client.app.session()

    sitecollection = SiteCollection(session)
    objects = sitecollection.get()
    old_domain = 'localhost'

    # Create test objects with content containing the old domain
    page = Page(
        name='page',
        title='Page',
        content={'text': f'A link to http://{old_domain}/page'},
    )
    # form = Form(meta={'url': f'http://{old_domain}/form'})
    # event = Event(content={'description': f'Visit us at {old_domain}'})
    # resource = Resource(meta={'link': f'https://{old_domain}/resource'})
    # person = Person(picture_url=f'http://{old_domain}/person.jpg')
    # org = Organisation(logo_url=f'http://{old_domain}/logo.png')
    # directory = Directory(content={'entries': [f'http://{old_domain}/entry1',
    # f'http://{old_domain}/entry2']})
    # ticket = Ticket(snapshot={'url': f'http://{old_domain}/ticket'})

    # external_link = ExternalLink(url=f'http://{old_domain}/external')

    # Testing the 'domain' change is hard to test, because current domain
    # will always be localhost here, which fails in form validation
    # 'Die Domain muss einen Punkt enthalten'
    # One would probably need to monkey patch the validate_domain function
    # We don't bother with that here
    session.add_all([page])
    session.flush()
    client.login_admin()
    page = client.get('/migrate-links')

    assert (
        'Migriert Links von der angegebenen Domain zur aktuellen Domain '
        '"localhost"' in page
    )
    page.form['migration_type'] = 'text'
    replacement_pairs = [
        ('www.abes.foo.ch', 'https://www.foo.ch/wsu/amt-fuer-beistand'),
        ('www.umgezogen.ch', 'https://www.foo.ch/umgezogen'),
    ]

    # todo: first test the dry-run 'test' mode
    file = create_test_replacement_xlsx(replacement_pairs)
    page.form['url_mappings'] = Upload(
        'redirects.xlsx', file.read(), 'application/vnd.ms-excel'
    )
    page.form['test'] = True
    page = page.form.submit().maybe_follow()
    assert 'Das Formular enthält Fehler' not in page
    page.showbrowser()


    # then test the other mode:
