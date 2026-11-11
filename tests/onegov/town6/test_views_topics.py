import pytest


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from webtest.forms import Select
    from .conftest import Client
    from tests.shared.client import ExtendedResponse


@pytest.mark.parametrize(('parent_url', 'add_label'), [
    ('/topics/themen', 'Thema'),
    ('/news', 'Nachricht'),
])
def test_collapsible_page_sections(
    client: Client,
    parent_url: str,
    add_label: str
) -> None:
    client.login_admin()
    new_page = client.get(parent_url).click(add_label)

    fields = list(new_page.form.fields)
    assert fields[fields.index('text') + 1] == 'collapse_sections'
    assert not new_page.form['collapse_sections'].checked
    assert new_page.pyquery('#collapse_sections').closest('label').find(
        '.label-text').text() == 'Ausklappen von Abschnitten'

    text = (
        '<p>Einleitung</p>'
        '<h2>Erster <em>Abschnitt</em></h2>'
        '<p>Erster Inhalt</p>'
        '<h3>Untertitel</h3><ul><li>Weiterer Inhalt</li></ul>'
        '<h2>Zweiter Abschnitt</h2><p>Zweiter Inhalt</p>'
    )
    new_page.form['title'] = 'Ausklappbare Abschnitte'
    new_page.form['text'] = text
    page = new_page.form.submit().follow()
    assert not page.pyquery('.page-text details')
    assert len(page.pyquery('.page-text > h2')) == 2

    edit_page = page.click('Bearbeiten')
    assert not edit_page.form['collapse_sections'].checked
    assert edit_page.form['text'].value == text
    edit_page.form['collapse_sections'] = True
    page = edit_page.form.submit().follow()

    # Public rendering groups each editor title into a closed section.
    public_page = client.spawn().get(page.request.url)
    sections = public_page.pyquery('.page-text details.page-section')
    assert len(sections) == 2
    assert not sections.filter('[open]')
    assert public_page.pyquery('.page-text > p').text() == 'Einleitung'
    assert sections.eq(0).find('summary > h2').text() == 'Erster Abschnitt'
    assert sections.eq(0).find('summary em').text() == 'Abschnitt'
    assert sections.eq(0).find('p').text() == 'Erster Inhalt'
    assert sections.eq(0).find('h3').text() == 'Untertitel'
    assert sections.eq(0).find('li').text() == 'Weiterer Inhalt'
    assert sections.eq(1).find('summary > h2').text() == 'Zweiter Abschnitt'
    assert sections.eq(1).find('p').text() == 'Zweiter Inhalt'

    # Editing retains the complete HTML and the saved checkbox state.
    edit_page = page.click('Bearbeiten')
    assert edit_page.form['collapse_sections'].checked
    assert edit_page.form['text'].value == text
    assert not edit_page.pyquery('details.page-section')

    edit_page.form['collapse_sections'] = False
    page = edit_page.form.submit().follow()
    assert not page.pyquery('.page-text details')
    assert len(page.pyquery('.page-text > h2')) == 2
    assert page.pyquery('.page-text > h3').text() == 'Untertitel'
    edit_page = page.click('Bearbeiten')
    assert not edit_page.form['collapse_sections'].checked
    assert edit_page.form['text'].value == text


def test_sort_topics(client: Client) -> None:
    client.login_admin().follow()

    page = client.get('/topics/themen')
    page = page.click('Thema')
    page.form['title'] = "Topic 1"
    page = page.form.submit().follow()

    page = client.get('/topics/themen')
    page = page.click('Thema')
    page.form['title'] = "Topic 2"
    page = page.form.submit().follow()

    page = page.click('Sortieren')
    page = page.follow()

    # Ensure no edit mode links
    assert "Speichern" not in page
    assert "Abbrechen" not in page
    assert "Topic 1" in page
    assert "Topic 2" in page
    assert "Zurück zur Seite" in page


def test_sort_root_topics(client: Client) -> None:
    client.login_admin().follow()

    page = client.get('/')
    page = page.click('Sortieren')
    url = page.pyquery('ul[data-sortable]').attr('data-sortable-url')
    items = {
        item.text_content().strip(): item.attrib['data-sortable-id']
        for item in page.pyquery('ul[data-sortable] li')
    }
    url = url.replace('%7Bsubject_id%7D', items['Kontakt'])
    url = url.replace('%7Bdirection%7D', 'above')
    url = url.replace('%7Btarget_id%7D', items['Organisation'])
    client.put(url)

    links = client.get('/').pyquery('.side-navigation > li > a span')
    assert links.text() == 'Kontakt Organisation Themen Aktuelles'


def get_select_option_id_by_text(
    select_form: Select,
    search_text: str
) -> str | None:
    found = []
    for option in select_form.options:
        # each option is a tuple (id, bool, select text)
        if search_text in option[2]:
            found.append(option[0])  # append page id

    if len(found) == 1:
        return found[0]
    else:
        print(f'Found multiple ids with {search_text}: {found}')
        return None


def test_move_topics(client: Client) -> None:
    client.login_admin().follow()

    page = client.get('/topics/themen')
    page = page.click('Thema')
    page.form['title'] = "Topic 1"
    page = page.form.submit().follow()
    assert page.status_code == 200

    page = client.get('/topics/themen')
    page = page.click('Thema')
    page.form['title'] = "Topic 2"
    page = page.form.submit().follow()
    assert page.status_code == 200

    news = client.get('/news')
    news = news.click('Nachricht')
    news.form['title'] = "News 1"
    news = news.form.submit().follow()
    assert news.status_code == 200

    page = page.click('Verschieben')  # move topic 2 under topic 1
    parent_id = get_select_option_id_by_text(page.form['parent_id'], 'Topic 1')
    page.form['parent_id'].select(parent_id)
    # ensure that news is not a valid destination
    assert not any('News' in o[2] for o in page.form['parent_id'].options)
    page = page.form.submit().follow()
    assert page.status_code == 200
    assert client.get('/topics/themen/topic-1/topic-2')

    # move page topic-1 to root (option '0') including subpage
    page = client.get('/topics/themen/topic-1')
    page = page.click('Verschieben')
    page.form['parent_id'].select('0')
    assert not any('News' in o[2] for o in page.form['parent_id'].options)
    page = page.form.submit().follow()
    print(page.request.url)
    assert client.get('/topics/topic-1')
    assert client.get('/topics/topic-1/topic-2')

    # test moving topic to itself (which is invalid)
    page = client.get('/topics/topic-1/topic-2')
    page = page.click('Verschieben')
    parent_id = get_select_option_id_by_text(page.form['parent_id'], 'Topic 2')
    page.form['parent_id'].select(parent_id)
    assert not any('News' in o[2] for o in page.form['parent_id'].options)
    page = page.form.submit()
    assert page.pyquery('.alert')
    assert page.pyquery('.error')
    assert 'Ungültiger Zielort gewählt' in page

    # test moving topic to a child (which is invalid)
    page = client.get('/topics/topic-1')
    page = page.click('Verschieben')
    parent_id = get_select_option_id_by_text(page.form['parent_id'], 'Topic 2')
    page.form['parent_id'].select(parent_id)
    assert not any('News' in o[2] for o in page.form['parent_id'].options)
    page = page.form.submit()
    assert page.pyquery('.alert')
    assert page.pyquery('.error')
    assert 'Ungültiger Zielort gewählt' in page


def test_topic_keywords(client: Client) -> None:
    client.login_admin()

    page = client.get('/topics/themen')
    new_page = page.click('Thema')
    new_page.form['title'] = "Einwohnerdienste"
    new_page.form['keywords'] = "Einwohnerkontrolle,Einwohneramt"
    page = new_page.form.submit().follow()
    assert 'Einwohnerdienste' in page

    edit_page = page.click('Bearbeiten')
    assert 'Einwohnerkontrolle' in edit_page
    assert 'Einwohneramt' in edit_page

    # keywords meta tag is rendered in the HTML head
    keywords_meta = edit_page.pyquery(
        "meta[name='keywords']"
    )
    assert not keywords_meta  # edit page has no model meta tags

    page = client.get('/topics/themen/einwohnerdienste')
    keywords_meta = page.pyquery("meta[name='keywords']")
    assert keywords_meta
    assert 'Einwohnerkontrolle' in keywords_meta.attr('content')
    assert 'Einwohneramt' in keywords_meta.attr('content')
    assert [
        keyword.text
        for keyword in page.pyquery('.sidebar .page-keywords .blank-label')
    ] == ['Einwohnerkontrolle', 'Einwohneramt']
    assert page.pyquery('.page-keywords h3').text() == 'Schlagworte'

    editor = client.spawn()
    editor.login_editor()
    editor_page = editor.get('/topics/themen/einwohnerdienste')
    assert editor_page.pyquery('.sidebar .page-keywords')

    anonymous = client.spawn()
    anonymous_page = anonymous.get('/topics/themen/einwohnerdienste')
    assert not anonymous_page.pyquery('.page-keywords')

    # keywords field is absent when editing news
    news = client.get('/news').click('Nachricht')
    assert 'keywords' not in news.form.fields


def test_contact_info_visible(client: Client) -> None:
    client.login_admin().follow()

    page = client.get('/topics/themen')
    page = page.click('Bearbeiten')
    page.form['contact'] = "Test contact info"
    page = page.form.submit().follow()

    assert "Test contact info" in page

    page = page.click('Bearbeiten')
    page.form['hide_contact'] = True
    page = page.form.submit().follow()

    assert "Test contact info" not in page

    page = page.click('Bearbeiten')
    page.form['hide_contact'] = False
    page = page.form.submit().follow()

    assert "Test contact info" in page


def test_contact_opening_hours_link(client: Client) -> None:
    client.login_admin()

    page = client.get('/topics/themen').click('Bearbeiten')
    page.form['contact'] = 'Test contact info'
    page.form.submit().follow()

    selector = '.contact-panel h3 a'
    assert not client.get('/topics/themen').pyquery(selector)

    settings = client.get('/footer-settings')
    settings.form['opening_hours_url'] = 'https://example.org/topics/kontakt'
    settings.form.submit().follow()

    anonymous = client.spawn()
    page = anonymous.get('/topics/themen')
    link = page.pyquery(selector)
    assert link.text() == 'Öffnungszeiten'
    assert link.attr('href') == 'https://example.org/topics/kontakt'
    target = page.click('Öffnungszeiten', href='/topics/kontakt')
    assert target.status_code == 200

    settings = client.get('/footer-settings')
    settings.form['opening_hours_url'] = (
        'https://example.org/topics/organisation'
    )
    settings.form.submit().follow()

    page = anonymous.get('/topics/themen')
    assert page.pyquery(selector).attr('href') == (
        'https://example.org/topics/organisation'
    )

    page = client.get('/topics/themen').click('Bearbeiten')
    page.form['hide_contact'] = True
    page.form.submit().follow()
    assert not anonymous.get('/topics/themen').pyquery(selector)

    page = client.get('/topics/themen').click('Bearbeiten')
    page.form['hide_contact'] = False
    page.form.submit().follow()

    settings = client.get('/footer-settings')
    settings.form['opening_hours_url'] = ''
    settings.form.submit().follow()
    assert not anonymous.get('/topics/themen').pyquery(selector)


def test_view_page_as_member(client: Client) -> None:
    admin = client
    client.login_admin()

    new_page = admin.get('/topics/organisation').click('Thema')
    new_page.form['title'] = "Test"
    new_page.form['access'] = 'member'
    page = new_page.form.submit().follow()
    page_url = '/topics/organisation/test'

    # Test if admin can see page
    admin.get(page_url)
    page = admin.get('/topics/organisation')
    assert 'Test' in page

    # Test if a member can see the page
    member = client.spawn()
    member.login_member()
    member.get(page_url)
    page = member.get('/topics/organisation')
    assert 'Test' in page

    # Test if a visitor can not see the page
    anon = client.spawn()
    anon.get(page_url, status=403)
    page = anon.get('/topics/organisation')
    assert 'Test' not in page


def test_page_templates(client: Client) -> None:
    from webtest.forms import Checkbox

    def mark_as_template(page: ExtendedResponse) -> None:
        # WebTest doesn't parse the fields at the end of the page form,
        # so we add the checkbox ourselves (see test_views_pages.py)
        field = Checkbox(page.form, 'input', 'is_page_template', 0, 'y')
        page.form.fields['is_page_template'] = [field]
        page.form.field_order.append(('is_page_template', field))
        field.checked = True

    client.login_admin()

    # without templates, there's nothing to select
    new_page = client.get('/topics/themen').click('Thema')
    assert 'page-templates' not in new_page

    # create a template
    new_page.form['title'] = "Vorlage Dienstleistung"
    new_page.form['lead'] = "Kurze Beschreibung der Dienstleistung"
    new_page.form['text'] = (
        '<h2>Voraussetzungen</h2><p>…</p>'
        '<h2>Kosten</h2><p>…</p>'
        '<p><a href="/forms" class="button cta">Online beantragen</a></p>'
    )
    mark_as_template(new_page)
    new_page.form['access'] = 'private'
    template = new_page.form.submit().follow()
    assert 'Diese Seite ist eine Vorlage' in template

    # the template can be selected when adding a page
    new_page = client.get('/topics/themen').click('Thema')
    assert 'Seite aus einer Vorlage erstellen' in new_page
    new_page = new_page.click(href='template=')
    assert new_page.form['title'].value == ''
    assert new_page.form['lead'].value == (
        'Kurze Beschreibung der Dienstleistung')
    assert '<h2>Kosten</h2>' in new_page.form['text'].value
    assert new_page.pyquery('#is_page_template').attr('checked') is None
    assert 'Ohne Vorlage' in new_page

    new_page.form['title'] = "Parkkarte"
    page = new_page.form.submit().follow()
    assert 'Kurze Beschreibung der Dienstleistung' in page
    assert 'Online beantragen' in page
    assert page.pyquery('.page-text a.cta').attr('href') == '/forms'
    assert 'Diese Seite ist eine Vorlage' not in page

    # also for pages on the top level
    root_page = client.get('/topics/themen').click('Thema')
    root_url = root_page.request.url.replace(
        '/editor/new/', '/editor/new-root/')
    root_url = root_url.rsplit('/', 1)[0] + '/1'
    root_page = client.get(root_url)
    assert 'Seite aus einer Vorlage erstellen' in root_page
    root_page = root_page.click(href='template=')
    assert '<h2>Kosten</h2>' in root_page.form['text'].value

    # a page which is no template anymore isn't offered
    # (the checkbox isn't submitted, since WebTest doesn't know it)
    edit = template.click('Bearbeiten')
    assert edit.pyquery('#is_page_template').attr('checked') is not None
    edit.form.submit()
    new_page = client.get('/topics/themen').click('Thema')
    assert 'page-templates' not in new_page

    # templates are not filled in by url manipulation either
    url = new_page.request.url + '?template=999999'
    assert 'Kurze Beschreibung' not in client.get(url)


def test_report_change_prefills_email(client: Client) -> None:
    client.login_admin()
    topic = client.get('/topics/themen')
    report_url = topic.pyquery('a[href$="report-change"]').attr('href')
    assert report_url

    # the e-mail address of the logged in user is filled in
    form = client.get(report_url).form
    assert form['submitter_email'].value == 'admin@example.org'

    # but can be changed
    form['submitter_email'] = 'someone@example.org'
    form['submitter_message'] = 'Bitte aktualisieren'
    ticket = form.submit().follow()
    assert 'someone@example.org' in client.get(
        ticket.request.url.replace('/status', ''))

    # anonymous users have to enter their address
    anonymous = client.spawn()
    form = anonymous.get(report_url).form
    assert form['submitter_email'].value == ''
