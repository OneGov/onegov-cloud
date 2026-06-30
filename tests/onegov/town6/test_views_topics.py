from __future__ import annotations


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from webtest.forms import Select
    from .conftest import Client


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
