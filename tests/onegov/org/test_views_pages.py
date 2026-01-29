from __future__ import annotations

import yaml

from datetime import timedelta
from freezegun import freeze_time
from onegov.core.utils import module_path
from onegov.file import FileCollection
from onegov.org.models import Topic
from onegov.page import Page, PageCollection
from sedate import utcnow
from tests.onegov.org.common import edit_bar_links
from tests.onegov.town6.test_views_topics import get_select_option_id_by_text
from tests.shared.utils import (get_meta, create_image,
                                extract_intercooler_delete_link)
from webtest import Upload


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from tests.shared.client import ExtendedResponse
    from .conftest import Client


def check_breadcrumbs(page: ExtendedResponse, excluded: str) -> None:
    # check the breadcrumbs
    breadcrumbs = page.pyquery('ul.breadcrumbs a')
    for b in breadcrumbs:
        url = b.attrib['href']
        assert excluded not in url, f'{excluded} still in {url}'


def check_navlinks(page: ExtendedResponse, excluded: str) -> None:
    # check the nav links
    nav_links = page.pyquery('ul.side-nav a')
    for link in nav_links:
        url = link.attrib['href']
        assert excluded not in url, f'{excluded} still in {url}'


def test_pages_cache(client: Client) -> None:
    client.login_admin()
    editor = client.spawn()
    editor.login_editor()

    root_url = client.get('/').pyquery('.top-bar-section a').attr('href')
    root_page = client.get(root_url)
    links = edit_bar_links(root_page, 'text')
    assert 'URL ändern' in links

    # Test changing the url of the root page organisation
    assert 'URL ändern' not in editor.get(root_page.request.url)
    url_page = root_page.click('URL ändern')

    old_name = url_page.form['name'].value
    new_name = 'my-govikon'

    url_page.form['name'] = 'my govikoN'
    url_page = url_page.form.submit()
    assert ('Ungültiger Name. Ein gültiger Vorschlag ist: my-govikon'
        ) in url_page
    url_page.form['name'] = new_name
    url_page.form['test'] = True
    url_page = url_page.form.submit()
    assert 'Insgesamt 0 Unterseiten sind betroffen' in url_page
    assert '0 Links' in url_page

    assert url_page.form['name'].value == new_name
    url_page.form['test'] = False
    org_page = url_page.form.submit().follow()

    org_page = org_page.click('Organisation', index=0)

    assert f'/topics/{new_name}' in org_page.request.url
    check_breadcrumbs(org_page, old_name)
    check_navlinks(org_page, old_name)

    # check editor access
    assert editor.get(url_page.request.url, status=403)


def test_pages(client: Client) -> None:
    root_url = client.get('/').pyquery('.top-bar-section a').attr('href')
    assert len(client.get(root_url).pyquery('.edit-bar')) == 0

    admin = client.spawn()
    admin.login_admin()

    images = admin.get('/images')
    images.form['file'] = [Upload('Test.jpg', create_image().read())]
    images.form.submit()
    img_url = admin.get('/images').pyquery('.image-box a').attr('href')

    embedded_img = (
        f'<p class="has-img">'
        f'<img src="${img_url}" class="lazyload-alt" '
        f'width="1167px" height="574px"></p>'
    )

    client.login_admin()
    editor = client.spawn()
    editor.login_editor()
    root_page = client.get(root_url)
    new_page = root_page.click('Thema')
    assert "Neues Thema" in new_page

    new_page.form['title'] = "Living in Govikon is Swell"
    new_page.form['lead'] = "Living in Govikon..."
    new_page.form['text'] = ("<h2>Living in Govikon is Really Great</h2>"
                             "<i>Experts say it's the fact that Govikon does "
                             "not really exist.</i>" + embedded_img
                             )
    page = new_page.form.submit().follow()

    assert page.pyquery('.main-title').text() == "Living in Govikon is Swell"
    assert page.pyquery('h2:first').text() == (
        "Living in Govikon is Really Great")
    assert page.pyquery('.page-text i').text().startswith(
        "Experts say it's the fact")

    # Test OpenGraph Meta
    assert get_meta(page, 'og:title') == 'Living in Govikon is Swell'
    assert get_meta(page, 'og:description') == 'Living in Govikon...'
    assert get_meta(page, 'og:image') == img_url

    edit_page = page.click("Bearbeiten")
    assert "Thema Bearbeiten" in edit_page
    assert "&lt;h2&gt;Living in Govikon is Really Great&lt;/h2&gt" in edit_page

    edit_page.form['title'] = "Living in Govikon is Awful"
    edit_page.form['text'] = (
        "<h2>Living in Govikon Really Sucks</h2>"
        "<i>Experts say hiring more experts would help.</i>"
        "<script>alert('yes')</script>"
    )
    page = edit_page.form.submit().follow()

    assert page.pyquery('.main-title').text() == "Living in Govikon is Awful"
    assert page.pyquery('h2:first').text() == "Living in Govikon Really Sucks"
    assert page.pyquery('.page-text i').text().startswith("Experts say hiring")
    assert "<script>alert('yes')</script>" not in page
    assert "&lt;script&gt;alert('yes')&lt;/script&gt;" in page

    client.get('/auth/logout')

    assert page.pyquery('.main-title').text() == "Living in Govikon is Awful"
    assert page.pyquery('h2:first').text() == "Living in Govikon Really Sucks"
    assert page.pyquery('.page-text i').text().startswith("Experts say hiring")


def test_pages_explicitly_link_referenced_files(client: Client) -> None:
    root_url = client.get('/').pyquery('.top-bar-section a').attr('href')

    admin = client.spawn()
    admin.login_admin()

    path = module_path('tests.onegov.org', 'fixtures/sample.pdf')
    with open(path, 'rb') as f:
        files = admin.get('/files')
        files.form['file'] = [
            Upload('Sample.pdf', f.read(), 'application/pdf')
        ]
        files.form.submit()

    pdf_url = (
        admin.get('/files')
        .pyquery('[ic-trigger-from="#button-1"]')
        .attr('ic-get-from')
        .removesuffix('/details')
    )
    pdf_link = f'<a href="{pdf_url}">Sample.pdf</a>'

    editor = client.spawn()
    editor.login_editor()
    root_page = editor.get(root_url)
    new_page = root_page.click('Thema')

    new_page.form['title'] = "Linking files"
    new_page.form['lead'] = "..."
    new_page.form['text'] = pdf_link
    new_page.form.submit().follow()

    session = client.app.session()
    pdf = FileCollection(session).query().one()
    page = (
        PageCollection(session).query()
        .filter(Page.title == 'Linking files').one()
    )
    assert page.files == [pdf]
    assert pdf.access == 'public'

    page.access = 'mtan'  # type: ignore[attr-defined]
    session.flush()
    assert pdf.access == 'mtan'

    # publication has ended
    page.publication_end = utcnow() - timedelta(days=1)
    session.flush()
    assert pdf.access == 'private'

    # link removed
    page.files = []
    session.flush()
    assert pdf.access == 'secret'


def test_pages_person_link_extension(client: Client) -> None:
    root_url = client.get('/').pyquery('.top-bar-section a').attr('href')
    assert len(client.get(root_url).pyquery('.edit-bar')) == 0

    admin = client.spawn()
    admin.login_admin()

    images = admin.get('/images')
    images.form['file'] = [Upload('Test.jpg', create_image().read())]
    images.form.submit()
    img_url = admin.get('/images').pyquery('.image-box a').attr('href')

    embedded_img = (
        f'<p class="has-img">'
        f'<img src="${img_url}" class="lazyload-alt" '
        f'width="1167px" height="574px"></p>'
    )

    client.login_admin()
    editor = client.spawn()
    editor.login_editor()

    # add person
    people_page = client.get('/people')
    new_person_page = people_page.click('Person')
    assert "Neue Person" in new_person_page

    new_person_page.form['first_name'] = 'Franz'
    new_person_page.form['last_name'] = 'Müller'
    new_person_page.form['function'] = 'Gemeindeschreiber'

    page = new_person_page.form.submit()
    assert page.location is not None
    person_uuid = page.location.split('/')[-1]
    page = page.follow()
    assert 'Müller Franz' in page

    # add topic
    root_page = client.get(root_url)
    new_page = root_page.click('Thema')
    assert "Neues Thema" in new_page

    new_page.form['title'] = "Living in Govikon is Swell"
    new_page.form['lead'] = "Living in Govikon..."
    new_page.form['text'] = ("<h2>Living in Govikon is Really "
                             "Great</h2><i>Experts say it's the fact that "
                             "Govikon does not really exist.</i>"
                             )
    new_page.form['western_name_order'] = False
    new_page.form['people-0-person'] = person_uuid
    page = new_page.form.submit().follow()
    assert 'Müller Franz' in page

    edit_page = page.click("Bearbeiten")
    edit_page.form['western_name_order'] = True
    page = edit_page.form.submit().follow()
    assert 'Franz Müller' in page


def test_delete_pages(client: Client) -> None:
    root_url = client.get('/').pyquery('.top-bar-section a').attr('href')

    client.login_admin()
    root_page = client.get(root_url)
    new_page = root_page.click('Thema')

    new_page.form['title'] = "Living in Govikon is Swell"
    new_page.form['text'] = (
        "## Living in Govikon is Really Great\n"
        "*Experts say it's the fact that Govikon does not really exist.*"
    )
    # we add a file attachment to ensure we can delete a page, even if
    # it contains file attachments
    new_page.form.set('files', [
        Upload('test.txt', b'foo', 'text/plain')
    ], -1)
    page = new_page.form.submit().follow()
    delete_link = page.pyquery('a[ic-delete-from]')[0].attrib['ic-delete-from']

    result = client.delete(delete_link.split('?')[0], expect_errors=True)
    assert result.status_code == 403

    assert client.delete(delete_link).status_code == 200
    assert client.delete(delete_link, expect_errors=True).status_code == 404


def test_delete_root_page_with_nested_pages(client: Client) -> None:

    root_page_organisation = (
        client.get('/').pyquery('.top-bar-section a').attr('href')
    )

    # root page contains single page:
    client.login_admin()
    root_page = client.get(root_page_organisation)
    new_page = root_page.click('Thema')
    new_page.form['title'] = "Child Page"
    new_page.form['text'] = (
        "## Living in Govikon is Really Great\n"
        "*Experts say it's the fact that Govikon does not really exist.*"
    )

    new_page.form.submit().follow()
    query = client.app.session().query(Topic)
    # Check that the pages were created
    for topic in ('organisation', 'themen', 'kontakt', 'child-page'):
        assert query.filter_by(name=topic).count() == 1

    #  Attempt to delete the root page as an editor
    client.logout()
    client.login_editor()
    page = client.get(root_page_organisation)
    assert "Diese Seite kann nicht gelöscht werden" in page

    client.logout()
    client.login_admin()

    # finally delete root page
    page = client.get(root_page_organisation)
    delete_link = extract_intercooler_delete_link(client, page)
    client.delete(delete_link)

    query = client.app.session().query(Topic)
    # Deleting root page 'organisation' should delete 'child-page' as well
    for topic in ('themen', 'kontakt'):
        assert query.filter_by(name=topic).count() == 1

    assert query.filter_by(name='organisation').count() == 0
    assert query.filter_by(name='child-page').count() == 0


def test_hide_page(client: Client) -> None:
    client.login_editor()

    new_page = client.get('/topics/organisation').click('Thema')

    new_page.form['title'] = "Test"
    new_page.form['access'] = 'private'
    page = new_page.form.submit().follow()
    page_url = '/topics/organisation/test'

    anonymous = client.spawn()
    anonymous.get(page_url, status=403)

    edit_page = page.click("Bearbeiten")
    edit_page.form['access'] = 'public'
    edit_page.form.submit().follow()

    anonymous.get(page_url, status=200)

    with freeze_time('2019-01-01'):
        edit_page = page.click("Bearbeiten")
        edit_page.form['publication_end'] = '2019-02-01T00:00'
        edit_page.form.submit().follow()

    anonymous.get(page_url, status=403)
    anon = client.spawn()
    page = anon.get('/topics/organisation')

    # Test the links in the page
    assert 'Test' not in page


def setup_main_and_subpage(client: Client) -> None:
    root_url = client.get('/').pyquery('.top-bar-section a').attr('href')
    client.login_admin()
    root_page = client.get(root_url)
    page_1 = root_page.click('Thema')
    page_1.form['title'] = "Mainpage"
    page_1.form['text'] = (
        "## Living in Govikon is Really Great\n"
        "*Experts say it's a fact that Govikon does not really exist.*"
    )
    assert page_1.form.submit().follow().status_code == 200
    # create subpage
    page_1 = client.get('/topics/organisation/mainpage')
    page_2 = page_1.click('Thema')
    page_2.form['title'] = "Subpage"
    page_2.form['text'] = (
        "## Govikon and its lake view\n"
        "*It is terrific!*"
    )
    assert page_2.form.submit().follow().status_code == 200

    assert client.get('/topics/organisation/mainpage')
    assert client.get('/topics/organisation/mainpage/subpage')


def test_move_page_to_root(client: Client) -> None:
    setup_main_and_subpage(client)

    # move subpage to top level (as mainpage)
    page = client.get('/topics/organisation/mainpage/subpage')
    move_page = page.click('Verschieben')
    assert 'move' in move_page.form.action
    move_page.form['parent_id'].select('0')
    # ensure that news is not a valid destination
    assert not any('Aktuelles' in o[2] for o in
                   move_page.form['parent_id'].options)
    move_page = move_page.form.submit().follow()
    assert move_page.status_code == 200

    # verify main page remains but subpage is on the root level now
    mainpage = client.get('/topics/organisation/mainpage')
    assert mainpage.status_code == 200
    assert mainpage.pyquery('.main-title').text() == 'Mainpage'

    subpage = client.get('/topics/subpage')
    assert subpage.status_code == 200
    assert subpage.pyquery('.main-title').text() == 'Subpage'


def test_move_page_with_child_to_root(client: Client) -> None:
    setup_main_and_subpage(client)

    # move main page to top level
    mainpage = client.get('/topics/organisation/mainpage')
    move_page = mainpage.click('Verschieben')
    assert 'move' in move_page.form.action
    move_page.form['parent_id'].select('0')
    move_page = move_page.form.submit().follow()
    assert move_page.status_code == 200

    # verify main page on root level, subpage is still the sub-page of
    # the main page
    mainpage = client.get('/topics/mainpage')
    assert mainpage.status_code == 200
    assert mainpage.pyquery('.main-title').text() == 'Mainpage'

    subpage = client.get('/topics/mainpage/subpage')
    assert subpage.status_code == 200
    assert subpage.pyquery('.main-title').text() == 'Subpage'


def test_move_page_assign_yourself_as_parent(client: Client) -> None:
    setup_main_and_subpage(client)

    mainpage = client.get('/topics/organisation/mainpage')
    move_page = mainpage.click('Verschieben')
    assert 'move' in move_page.form.action
    parent_id = get_select_option_id_by_text(move_page.form['parent_id'],
                                             'Mainpage')
    move_page.form['parent_id'].select(parent_id)
    move_page = move_page.form.submit()
    assert move_page.pyquery('.alert')
    assert move_page.pyquery('.error')
    assert 'Ungültiger Zielort gewählt' in move_page


def test_move_page_assigning_a_child_as_parent(client: Client) -> None:
    setup_main_and_subpage(client)
    mainpage = client.get('/topics/organisation/mainpage')
    move_page = mainpage.click('Verschieben')
    assert 'move' in move_page.form.action
    parent_id = get_select_option_id_by_text(move_page.form['parent_id'],
                                             'Subpage')
    move_page.form['parent_id'].select(parent_id)
    move_page = move_page.form.submit()
    assert move_page.pyquery('.alert')
    assert move_page.pyquery('.error')
    assert 'Ungültiger Zielort gewählt' in move_page


def test_links(client: Client) -> None:
    root_url = client.get('/').pyquery('.top-bar-section a').attr('href')
    client.login_admin()
    root_page = client.get(root_url)

    assert 'URL ändern' in edit_bar_links(root_page, 'text')
    new_link = root_page.click("Verknüpfung")
    assert "Neue Verknüpfung" in new_link

    new_link.form['title'] = 'Google'
    new_link.form['url'] = 'https://www.google.ch'
    link = new_link.form.submit().follow()

    assert "Sie wurden nicht automatisch weitergeleitet" in link
    assert 'https://www.google.ch' in link

    new_link = root_page.click("Verknüpfung")
    new_link.form['url'] = root_url
    new_link.form['title'] = 'Link to Org'
    internal_link = new_link.form.submit().follow()

    # Change the root url
    change_url = root_page.click('URL ändern')
    change_url.form['name'] = 'org'
    change_url.form['test'] = True

    change_url_check = change_url.form.submit()
    callout = change_url_check.pyquery('.callout').text()
    assert '1 Links werden nach dieser Aktion ersetzt.' in callout
    change_url_check.form['test'] = False
    root_page = change_url_check.form.submit().follow()
    root_url = root_page.request.url
    # check the link to org is updated getting 200 OK
    link_page = root_page.click('Link to Org', index=0)

    assert internal_link.request.url != link_page.request.url

    client.get('/auth/logout')

    root_page = client.get(root_url)
    assert "Google" in root_page
    google = root_page.click("Google", index=0)

    assert google.status_code == 302
    assert google.location == 'https://www.google.ch'


def test_copy_paste_with_same_trait_only(client: Client) -> None:
    client.login_admin()

    # test copy and paste topic (to different location in tree)
    page = client.get('/topics/organisation')
    edit = page.click('Thema')

    edit.form['title'] = 'Dance Party'
    edit.form['lead'] = '0xcafebabe'
    party = edit.form.submit().follow()

    assert '/topics/organisation/dance-party' in party.request.url

    party.click('Kopieren')

    edit = client.get('/topics/themen').click('Einf')

    assert '0xcafebabe' in edit
    page = edit.form.submit().follow()

    assert 'Dance Party' in page
    assert '/topics/themen/dance-party' in page.request.url

    # test copy topic paste in news, fails
    page.click('Kopieren')

    news = client.get('/news')
    assert 'Kopieren' in news
    # paste button exists but disabled
    assert 'Einf' in news
    paste_link = news.pyquery('.paste-link.disabled-link')[0]
    assert 'Einf' in paste_link.text
    assert 'editor/paste/news' in paste_link.attrib['href']

    # test copy and paste news
    news = client.get('/news')
    edit = news.click('Nachricht')

    edit.form['title'] = 'Sink Hole'
    edit.form['lead'] = '0xdeadbeef'

    sinkhole = edit.form.submit().follow()

    assert 'Sink Hole' in sinkhole
    assert '0xdeadbeef' in sinkhole

    sinkhole.click('Kopieren')

    assert 'Einf' in sinkhole
    edit = sinkhole.click('Einf')
    edit.form['title'] = 'Sink Hole COPIED'

    sinkhole_2 = edit.form.submit().follow()
    assert 'Sink Hole COPIED' in sinkhole_2

    # test copy news paste in topic, fails
    sinkhole_2.click('Kopieren')
    topics = client.get('/topics/themen')

    assert 'Kopieren' in topics
    # paste button exists but disabled
    assert 'Einf' in topics
    paste_link = topics.pyquery('.paste-link.disabled-link')[0]
    assert 'Einf' in paste_link.text
    assert 'editor/paste/page' in paste_link.attrib['href']


def test_copy_pages_to_news(client: Client) -> None:
    client.login_admin()

    page = client.get('/topics/organisation')
    edit = page.click('Bearbeiten')

    edit.form['lead'] = '0xdeadbeef'
    page = edit.form.submit().follow()

    page.click('Kopieren')

    edit = client.get('/news').click('Einf')

    assert '0xdeadbeef' in edit
    page = edit.form.submit().follow()

    assert '/news/organisation' in page.request.url


def test_clipboard(client: Client) -> None:
    client.login_admin()

    page = client.get('/topics/organisation')
    assert 'paste-link' not in page

    page = page.click(
        'Kopieren',
        extra_environ={'HTTP_REFERER': page.request.url}
    ).follow()

    assert 'paste-link' in page

    page = page.click('Einf').form.submit().follow()
    assert '/organisation/organisation' in page.request.url


def test_clipboard_separation(client: Client) -> None:
    client.login_admin()

    page = client.get('/topics/organisation')
    page = page.click('Kopieren')

    assert 'paste-link' in client.get('/topics/organisation')

    # new client (browser) -> new clipboard
    client = client.spawn()
    client.login_admin()

    assert 'paste-link' not in client.get('/topics/organisation')


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


def test_add_iframe(client: Client) -> None:
    fs = client.app.filestorage
    assert fs is not None
    data = {  # with and without trailing slash
        'allowed_domains': ['https://www.seantis.ch/', 'https://www.myorg.org']
    }
    with fs.open('allowed_iframe_domains.yml', 'w') as f:
        yaml.dump(data, f)

    client.login_admin()
    page = client.get('/topics/organisation').click('iFrame')
    page.form['title'] = "Success"
    page.form['url'] = "https://www.seantis.ch/success-stories/"
    page = page.form.submit().follow()
    assert 'Die Domäne der URL ist für iFrames nicht zulässig.' not in page
    assert 'iFrame wurde hinzugefügt' in page

    csp_str = page.headers['Content-Security-Policy']
    csp = {v.split(' ')[0]: v.split(' ', 1)[-1] for v in csp_str.split(';')}
    assert "https://www.seantis.ch/" in csp['child-src']
    assert "https://www.myorg.org" in csp['child-src']

    page = client.get('/topics/organisation').click('iFrame')
    page.form['title'] = "Fine"
    page.form['url'] = "https://www.myorg.org/success-stories/"
    page = page.form.submit().follow()
    assert 'Die Domäne der URL ist für iFrames nicht zulässig.' not in page
    assert 'iFrame wurde hinzugefügt' in page

    page = client.get('/topics/organisation').click('iFrame')
    page.form['title'] = "Failure"
    page.form['url'] = "https://www.organisation.org/success-stories/"
    page = page.form.submit()
    assert 'Die Domäne der URL ist für iFrames nicht zulässig.' in page
