from datetime import datetime
from freezegun import freeze_time


def test_news(client):
    client.login_admin().follow()

    with freeze_time("2022-02-03 8:00"):
        page = client.get('/news')
        page = page.click('Nachricht')
        page.form['title'] = "Corona-Virus: Status-Update from 28.01.2022"
        page.form['lead'] = "First lead"
        page.form['text'] = "First hashtag #onegov"
        page.form['publication_start'] = datetime(2022, 1, 28, 8).isoformat()
        page = page.form.submit().follow()
        assert "28. Januar 2022" in page
        assert "#onegov" in page

    with freeze_time("2022-01-05 8:00"):
        page = client.get('/news')
        page = page.click('Nachricht')
        page.form['title'] = "Corona-Virus: Status-Update from 31.12.2021"
        page.form['lead'] = "Second lead"
        page.form['text'] = "Second hashtag #pilatus"
        page.form['publication_start'] = datetime(2021, 12, 31, 8).isoformat()
        page = page.form.submit().follow()
        assert "31. Dezember 2021" in page
        assert "#pilatus" in page

    #  Test if both are in the overview
    page = client.get('/news')
    assert "Corona-Virus: Status-Update from 28.01.2022" in page
    assert "Corona-Virus: Status-Update from 31.12.2021" in page

    #  Test if both are not in the overview with 2020 Year Filter
    page = client.get('/news?filter_years=2020')
    assert "Corona-Virus: Status-Update from 28.01.2022" not in page
    assert "Corona-Virus: Status-Update from 31.12.2021" not in page

    #  Test if 2021 news are in the overview with Year Filter
    page = client.get('/news?filter_years=2021')
    assert "Corona-Virus: Status-Update from 28.01.2022" not in page
    assert "Corona-Virus: Status-Update from 31.12.2021" in page
    # Test result = not in page

    #  Test if 2022 news are in the overview with Year Filter
    page = client.get('/news?filter_years=2022')
    assert "Corona-Virus: Status-Update from 28.01.2022" in page
    assert "Corona-Virus: Status-Update from 31.12.2021" not in page
    # Test result = in page

    #  Test if news are in the overview with #onegov Hash Filter
    page = client.get('/news?filter_tags=onegov')
    assert "Corona-Virus: Status-Update from 28.01.2022" in page
    assert "Corona-Virus: Status-Update from 31.12.2021" not in page

    #  Test if news are in the overview with #pilatus Hash Filter
    page = client.get('/news?filter_tags=pilatus')
    assert "Corona-Virus: Status-Update from 28.01.2022" not in page
    assert "Corona-Virus: Status-Update from 31.12.2021" in page

    #  Test if news are in the overview with #onegov Hash Filter and Year 2021
    page = client.get('/news?filter_tags=onegov&filter_years=2021')
    assert "Corona-Virus: Status-Update from 28.01.2022" not in page
    assert "Corona-Virus: Status-Update from 31.12.2021" not in page

    #  Test if news are in the overview with #onegov Hash Filter and Year 2022
    page = client.get('/news?filter_tags=onegov&filter_years=2022')
    assert "Corona-Virus: Status-Update from 28.01.2022" in page
    assert "Corona-Virus: Status-Update from 31.12.2021" not in page

    #  Test if news are in the overview with #pilatus Hash Filter and Year 2021
    page = client.get('/news?filter_tags=pilatus&filter_years=2021')
    assert "Corona-Virus: Status-Update from 28.01.2022" not in page
    assert "Corona-Virus: Status-Update from 31.12.2021" in page
    #  Test result = not in page

    #  Test if news are in the overview with #pilatus Hash Filter and Year 2022
    page = client.get('/news?filter_tags=pilatus&filter_years=2022')
    assert "Corona-Virus: Status-Update from 28.01.2022" not in page
    assert "Corona-Virus: Status-Update from 31.12.2021" not in page
    #  Test result = in page


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
