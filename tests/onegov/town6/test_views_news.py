import transaction

from onegov.page import PageCollection
from tests.shared.utils import open_in_browser


def test_news(client):
    client.login_admin().follow()

    page = client.get('/news')
    page = page.click('Nachricht')
    page.form['title'] = "We have a new homepage"
    page.form['lead'] = "It is very good"
    page.form['text'] = "It is lots of fun"
    page = page.form.submit().follow()

    assert "We have a new homepage" in page.text
    assert "It is very good" in page.text
    assert "It is lots of fun" in page.text

    page = client.get('/news')
    assert "We have a new homepage" in page.text
    assert "It is very good" in page.text
    assert "It is lots of fun" not in page.text

    page = client.get('/news/we-have-a-new-homepage')
    client.delete(page.pyquery('a[ic-delete-from]').attr('ic-delete-from'))
    page = client.get('/news')
    assert "We have a new homepage" not in page.text
    assert "It is very good" not in page.text
    assert "It is lots of fun" not in page.text


def test_hide_news(client):
    client.login_editor()

    new_page = client.get('/news').click('Nachricht')

    new_page.form['title'] = "Test"
    new_page.form['access'] = 'private'
    page = new_page.form.submit().follow()

    anonymous = client.spawn()
    response = anonymous.get(page.request.url, expect_errors=True)
    assert response.status_code == 403

    edit_page = page.click("Bearbeiten")
    edit_page.form['access'] = 'public'
    page = edit_page.form.submit().follow()

    response = anonymous.get(page.request.url)
    assert response.status_code == 200
