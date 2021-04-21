from freezegun import freeze_time

from tests.onegov.org.common import edit_bar_links


def test_pages(client):

    root_url = client.get('/').pyquery('.top-bar-section a').attr('href')
    assert len(client.get(root_url).pyquery('.edit-bar')) == 0

    client.login_admin()
    editor = client.spawn()
    editor.login_editor()
    root_page = client.get(root_url)

    links = edit_bar_links(root_page, 'text')
    assert 'Url ändern' in links
    assert len(links) == 5
    new_page = root_page.click('Thema')
    assert "Neues Thema" in new_page

    new_page.form['title'] = "Living in Govikon is Swell"
    new_page.form['text'] = (
        "<h2>Living in Govikon is Really Great</h2>"
        "<i>Experts say it's the fact that Govikon does not really exist.</i>"
    )
    page = new_page.form.submit().follow()

    assert page.pyquery('.main-title').text() == "Living in Govikon is Swell"
    assert page.pyquery('h2:first').text() \
        == "Living in Govikon is Really Great"
    assert page.pyquery('.page-text i').text()\
        .startswith("Experts say it's the fact")

    # Test changing the url
    assert 'Url ändern' not in editor.get(page.request.url)
    url_page = page.click('Url ändern')
    url_page.form['name'] = 'my govikoN'
    url_page = url_page.form.submit()
    assert 'Ungültiger Name. Ein gültiger Vorschlag ist: my-govikon' in url_page
    url_page.form['name'] = 'my-govikon'
    url_page.form['test'] = False
    page = url_page.form.submit().follow()
    assert 'organisation/my-govikon' in page.request.url
    assert editor.get(url_page.request.url, status=403)

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
    root_page = client.get(root_url)

    assert len(root_page.pyquery('.edit-bar')) == 0

    assert page.pyquery('.main-title').text() == "Living in Govikon is Awful"
    assert page.pyquery('h2:first').text() == "Living in Govikon Really Sucks"
    assert page.pyquery('.page-text i').text().startswith("Experts say hiring")


def test_delete_pages(client):
    root_url = client.get('/').pyquery('.top-bar-section a').attr('href')

    client.login_admin()
    root_page = client.get(root_url)
    new_page = root_page.click('Thema')

    new_page.form['title'] = "Living in Govikon is Swell"
    new_page.form['text'] = (
        "## Living in Govikon is Really Great\n"
        "*Experts say it's the fact that Govikon does not really exist.*"
    )
    page = new_page.form.submit().follow()
    delete_link = page.pyquery('a[ic-delete-from]')[0].attrib['ic-delete-from']

    result = client.delete(delete_link.split('?')[0], expect_errors=True)
    assert result.status_code == 403

    assert client.delete(delete_link).status_code == 200
    assert client.delete(delete_link, expect_errors=True).status_code == 404


def test_hide_page(client):
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

    anonymous.get(page_url, status=404)
    anon = client.spawn()
    page = anon.get('/topics/organisation')

    # Test the links in the
    assert 'Test' not in page


def test_links(client):
    root_url = client.get('/').pyquery('.top-bar-section a').attr('href')
    client.login_admin()
    root_page = client.get(root_url)

    assert 'Url ändern' in edit_bar_links(root_page, 'text')
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
    change_url = root_page.click('Url ändern')
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


def test_copy_pages_to_news(client):
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


def test_clipboard(client):
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


def test_clipboard_separation(client):
    client.login_admin()

    page = client.get('/topics/organisation')
    page = page.click('Kopieren')

    assert 'paste-link' in client.get('/topics/organisation')

    # new client (browser) -> new clipboard
    client = client.spawn()
    client.login_admin()

    assert 'paste-link' not in client.get('/topics/organisation')