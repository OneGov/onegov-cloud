from __future__ import annotations

import transaction

from datetime import timedelta, datetime
from onegov.org.models import News
from onegov.page import PageCollection
from sedate import utcnow
from tests.onegov.org.common import edit_bar_links
from tests.shared.utils import get_meta


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .conftest import Client


def test_news(client: Client) -> None:
    client.login_admin().follow()
    anon = client.spawn()

    # Test edit the root news page
    page = client.get('/news')
    assert 'Aktuelles' in page

    # Top page with path /news is fix, and all others are children
    links = edit_bar_links(page, 'text')
    assert 'URL ändern' not in links
    # 5 links: Edit, Copy, iFrame, Closing link for the Iframe Modal,
    # Add News Entry
    assert len(links) == 5

    edit = page.click('Bearbeiten')
    edit.form['contact'] = 'We could show this address on the root news page'
    edit.form['access'] = 'private'
    edit.form.submit().follow()

    assert 'Aktuelles' not in anon.get('/')
    anon.get('/news', status=403)

    page = page.click('Nachricht')
    page.form['title'] = "We have a new homepage"
    page.form['page_image'] = "/image.png"
    page.form['lead'] = "It is very good"
    page.form['text'] = "It is lots of fun \n #fun"
    page = page.form.submit().follow()

    assert "We have a new homepage" in page.text
    assert "image.png" in page.text
    assert "It is very good" in page.text
    assert "It is lots of fun" in page.text

    overview = client.get('/news')
    assert "We have a new homepage" in overview.text
    assert "image.png" in overview.text
    assert "It is very good" in overview.text
    assert "It is lots of fun" not in overview.text

    # Test OpenGraph Meta
    assert get_meta(page, 'og:title') == 'We have a new homepage'
    assert get_meta(page, 'og:description') == 'It is very good'
    assert not get_meta(page, 'og:image')

    page = client.get('/news')
    assert "We have a new homepage" in page.text
    assert "It is very good" in page.text
    assert "It is lots of fun" not in page.text
    assert "/news?filter_tags=fun" in page.text

    # Test RSS Feed
    page = client.get('/news?format=rss')
    assert '<atom:link ' in page.text
    assert 'rel="alternate"' in page.text
    assert '/news?page=0</link>' in page.text
    assert "We have a new homepage" in page.text
    assert "It is very good" in page.text
    assert "It is lots of fun" not in page.text

    page = client.get('/news/we-have-a-new-homepage')
    client.delete(page.pyquery('a[ic-delete-from]').attr('ic-delete-from'))
    page = client.get('/news')
    assert "We have a new homepage" not in page.text
    assert "It is very good" not in page.text
    assert "It is lots of fun" not in page.text


def test_news_on_homepage(client: Client) -> None:
    client.login_admin()
    anon = client.spawn()

    news_list = client.get('/news')

    page = news_list.click('Nachricht')
    page.form['title'] = "Foo"
    page.form['lead'] = "Lorem"
    page.form['publication_start'] = '2020-01-01T00:00'
    page.form['publication_end'] = '2200-01-01T00:00'
    page.form.submit().follow()

    page = news_list.click('Nachricht')
    page.form['title'] = "Bar"
    page.form['lead'] = "Lorem"
    page.form.submit()

    page = news_list.click('Nachricht')
    page.form['title'] = "Baz"
    page.form['lead'] = "Lorem"
    page.form.submit()

    # only two items are shown on the homepage
    homepage = client.get('/')
    assert "Baz" in homepage
    assert "Bar" in homepage
    assert "Foo" not in homepage

    # sticky news don't count toward that limit
    foo = PageCollection(client.app.session()).by_path('news/foo')
    assert isinstance(foo, News)
    foo.is_visible_on_homepage = True

    transaction.commit()

    homepage = client.get('/')
    assert "Baz" in homepage
    assert "Bar" in homepage
    assert "Foo" in homepage

    # hidden news don't count for anonymous users
    baz = PageCollection(client.app.session()).by_path('news/baz')
    assert isinstance(baz, News)
    baz.access = 'private'

    transaction.commit()

    homepage = anon.get('/')
    assert "Baz" not in homepage
    assert "Bar" in homepage
    assert "Foo" in homepage

    homepage = client.get('/')
    assert "Baz" in homepage
    assert "Bar" in homepage
    assert "Foo" in homepage

    # even if they are stickied
    baz = PageCollection(client.app.session()).by_path('news/baz')
    assert isinstance(baz, News)
    baz.access = 'private'
    baz.is_visible_on_homepage = True
    baz.publication_end = utcnow() - timedelta(minutes=5)

    transaction.commit()

    homepage = anon.get('/')
    assert "Baz" not in homepage
    assert "Bar" in homepage
    assert "Foo" in homepage

    homepage = client.get('/')
    assert "Baz" in homepage
    assert "Bar" in homepage
    assert "Foo" in homepage

    baz = PageCollection(client.app.session()).by_path('news/baz')
    assert isinstance(baz, News)
    baz.access = 'public'
    transaction.commit()
    assert "Baz" not in anon.get('/')


def test_hide_news(client: Client) -> None:
    client.login_editor()

    new_page = client.get('/news').click('Nachricht')

    new_page.form['title'] = "Test"
    new_page.form['access'] = 'private'
    page = new_page.form.submit().follow()
    overview = client.get("/news")

    assert "Test" in page
    assert "Test" in overview

    anonymous = client.spawn()
    response = anonymous.get(page.request.url, expect_errors=True)
    assert response.status_code == 403
    overview = anonymous.get("/news")
    assert "Test" not in overview

    edit_page = page.click("Bearbeiten")
    edit_page.form['access'] = 'public'
    page = edit_page.form.submit().follow()

    response = anonymous.get(page.request.url)
    assert response.status_code == 200
    tomorrow = datetime.now() + timedelta(days=1)
    tomorrow_str = tomorrow.strftime("%Y-%m-%dT%H:%M")

    edit_page = page.click("Bearbeiten")
    edit_page.form['publication_start'] = tomorrow_str
    page = edit_page.form.submit().follow()

    overview = client.get("/news")
    assert "Test" in overview
    overview = anonymous.get("/news")
    assert "Test" not in overview


def test_news_filter_invalid_years(client: Client) -> None:

    page = client.get('/news?filter_years=20263', status=400)
    assert 'Cannot decode URL parameter' in page

    page = client.get('/news?filter_years=0', status=400)
    assert 'Cannot decode URL parameter' in page

    page = client.get('/news?filter_years=2020')
    assert 'Aktuelles' in page
