from __future__ import annotations

from datetime import datetime
from freezegun import freeze_time


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .conftest import Client


def test_news(client: Client) -> None:
    client.login_admin().follow()

    with freeze_time("2021-12-30 8:00"):
        page = client.get('/news').click('Nachricht')
        page.form['title'] = 'News created 30.12.2021, no publication date'
        page.form['lead'] = 'Lead'
        page.form['text'] = 'hashtag #one'
        assert '30. Dezember 2021' in page.form.submit().follow()

        page = client.get('/news').click('Nachricht')
        page.form['title'] = 'News created 30.12.2021, published 31.12.2021'
        page.form['lead'] = 'Lead'
        page.form['text'] = 'hashtag #two'
        page.form['publication_start'] = datetime(2021, 12, 31, 8).isoformat()
        assert '31. Dezember 2021' in page.form.submit().follow()

        page = client.get('/news').click('Nachricht')
        page.form['title'] = 'News created 30.12.2021, published 1.1.2022'
        page.form['lead'] = 'Lead'
        page.form['text'] = 'hashtag #three'
        page.form['publication_start'] = datetime(2022, 1, 1, 8).isoformat()
        assert '1. Januar 2022' in page.form.submit().follow()

    with freeze_time('2022-1-2 8:00'):
        page = client.get('/news').click('Nachricht')
        page.form['title'] = 'News created 2.1.2022, no publication date'
        page.form['lead'] = 'Lead'
        page.form['text'] = 'hashtag #one'
        assert '2. Januar 2022' in page.form.submit().follow()

        page = client.get('/news').click('Nachricht')
        page.form['title'] = 'News created 2.1.2022, published 31.12.2021'
        page.form['lead'] = 'Lead'
        page.form['text'] = 'hashtag #two'
        page.form['publication_start'] = datetime(2021, 12, 31, 8).isoformat()
        assert '31. Dezember 2021' in page.form.submit().follow()

        page = client.get('/news').click('Nachricht')
        page.form['title'] = 'News created 2.1.2022, published 1.1.2022'
        page.form['lead'] = 'Lead'
        page.form['text'] = 'hashtag #three'
        page.form['publication_start'] = datetime(2022, 1, 1, 8).isoformat()
        assert '1. Januar 2022' in page.form.submit().follow()

    # No filter
    page = client.get('/news')
    assert 'News created 30.12.2021, no publication date' in page
    assert 'News created 30.12.2021, published 31.12.2021' in page
    assert 'News created 30.12.2021, published 1.1.2022' in page
    assert 'News created 2.1.2022, no publication date' in page
    assert 'News created 2.1.2022, published 31.12.2021' in page
    assert 'News created 2.1.2022, published 1.1.2022' in page

    # 2020
    page = client.get('/news?filter_years=2020')
    assert 'News created 30.12.2021, no publication date' not in page
    assert 'News created 30.12.2021, published 31.12.2021' not in page
    assert 'News created 30.12.2021, published 1.1.2022' not in page
    assert 'News created 2.1.2022, no publication date' not in page
    assert 'News created 2.1.2022, published 31.12.2021' not in page
    assert 'News created 2.1.2022, published 1.1.2022' not in page

    # 2021
    page = client.get('/news?filter_years=2021')
    assert 'News created 30.12.2021, no publication date' in page
    assert 'News created 30.12.2021, published 31.12.2021' in page
    assert 'News created 30.12.2021, published 1.1.2022' not in page
    assert 'News created 2.1.2022, no publication date' not in page
    assert 'News created 2.1.2022, published 31.12.2021' in page
    assert 'News created 2.1.2022, published 1.1.2022' not in page

    # 2022
    page = client.get('/news?filter_years=2022')
    assert 'News created 30.12.2021, no publication date' not in page
    assert 'News created 30.12.2021, published 31.12.2021' not in page
    assert 'News created 30.12.2021, published 1.1.2022' in page
    assert 'News created 2.1.2022, no publication date' in page
    assert 'News created 2.1.2022, published 31.12.2021' not in page
    assert 'News created 2.1.2022, published 1.1.2022' in page

    # 2023
    page = client.get('/news?filter_years=2023')
    assert 'News created 30.12.2021, no publication date' not in page
    assert 'News created 30.12.2021, published 31.12.2021' not in page
    assert 'News created 30.12.2021, published 1.1.2022' not in page
    assert 'News created 2.1.2022, no publication date' not in page
    assert 'News created 2.1.2022, published 31.12.2021' not in page
    assert 'News created 2.1.2022, published 1.1.2022' not in page

    # 2021 & 2022
    page = client.get('/news?filter_years=2021&filter_years=2022')
    assert 'News created 30.12.2021, no publication date' in page
    assert 'News created 30.12.2021, published 31.12.2021' in page
    assert 'News created 30.12.2021, published 1.1.2022' in page
    assert 'News created 2.1.2022, no publication date' in page
    assert 'News created 2.1.2022, published 31.12.2021' in page
    assert 'News created 2.1.2022, published 1.1.2022' in page

    # #one
    page = client.get('/news?filter_tags=one')
    assert 'News created 30.12.2021, no publication date' in page
    assert 'News created 30.12.2021, published 31.12.2021' not in page
    assert 'News created 30.12.2021, published 1.1.2022' not in page
    assert 'News created 2.1.2022, no publication date' in page
    assert 'News created 2.1.2022, published 31.12.2021' not in page
    assert 'News created 2.1.2022, published 1.1.2022' not in page

    # #two
    page = client.get('/news?filter_tags=two')
    assert 'News created 30.12.2021, no publication date' not in page
    assert 'News created 30.12.2021, published 31.12.2021' in page
    assert 'News created 30.12.2021, published 1.1.2022' not in page
    assert 'News created 2.1.2022, no publication date' not in page
    assert 'News created 2.1.2022, published 31.12.2021' in page
    assert 'News created 2.1.2022, published 1.1.2022' not in page

    # #three
    page = client.get('/news?filter_tags=three')
    assert 'News created 30.12.2021, no publication date' not in page
    assert 'News created 30.12.2021, published 31.12.2021' not in page
    assert 'News created 30.12.2021, published 1.1.2022' in page
    assert 'News created 2.1.2022, no publication date' not in page
    assert 'News created 2.1.2022, published 31.12.2021' not in page
    assert 'News created 2.1.2022, published 1.1.2022' in page

    # #four
    page = client.get('/news?filter_tags=four')
    assert 'News created 30.12.2021, no publication date' not in page
    assert 'News created 30.12.2021, published 31.12.2021' not in page
    assert 'News created 30.12.2021, published 1.1.2022' not in page
    assert 'News created 2.1.2022, no publication date' not in page
    assert 'News created 2.1.2022, published 31.12.2021' not in page
    assert 'News created 2.1.2022, published 1.1.2022' not in page

    # #one & #two
    page = client.get('/news?filter_tags=one&filter_tags=two')
    assert 'News created 30.12.2021, no publication date' in page
    assert 'News created 30.12.2021, published 31.12.2021' in page
    assert 'News created 30.12.2021, published 1.1.2022' not in page
    assert 'News created 2.1.2022, no publication date' in page
    assert 'News created 2.1.2022, published 31.12.2021' in page
    assert 'News created 2.1.2022, published 1.1.2022' not in page

    # 2021 & #one
    page = client.get('/news?filter_years=2021&filter_tags=one')
    assert 'News created 30.12.2021, no publication date' in page
    assert 'News created 30.12.2021, published 31.12.2021' not in page
    assert 'News created 30.12.2021, published 1.1.2022' not in page
    assert 'News created 2.1.2022, no publication date' not in page
    assert 'News created 2.1.2022, published 31.12.2021' not in page
    assert 'News created 2.1.2022, published 1.1.2022' not in page


def test_hide_news(client: Client) -> None:
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


def test_news_overview_detail(client: Client) -> None:
    client.login_admin()

    news_list = client.get('/news')

    page = news_list.click('Nachricht')
    page.form['title'] = "Foo"
    page.form['page_image'] = "/image.png"
    page.form['lead'] = "Lorem"
    page.form['publication_start'] = '2020-05-01T00:00'
    page.form.submit().follow()

    page = news_list.click('Nachricht')
    page.form['title'] = "Bar"
    page.form['lead'] = "Lorem"
    page.form['publication_start'] = '2020-04-01T00:00'
    page.form.submit().follow()

    page = news_list.click('Nachricht')
    page.form['title'] = "Zap"
    page.form['lead'] = "Lorem"
    page.form['publication_start'] = '2020-03-01T00:00'
    page.form.submit().follow()

    page = news_list.click('Nachricht')
    page.form['title'] = "One"
    page.form['lead'] = "Lorem"
    page.form['publication_start'] = '2020-02-01T00:00'
    page.form.submit().follow()

    news_list = client.get('/news')
    news_detail = news_list.click('Foo')

    more_news = news_detail.pyquery(".more-list a span")
    more_news = ' '.join([a.text for a in more_news])

    assert "/image.png" in news_detail

    assert "/image.png" in news_list

    assert "Foo" not in more_news
    assert "One" not in more_news

    assert "Wir haben" in more_news
    assert "Bar" in more_news
    assert "Zap" in more_news
