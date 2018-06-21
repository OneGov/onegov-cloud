from freezegun import freeze_time
from io import BytesIO
from onegov.gazette.tests.common import login_editor_1
from onegov.gazette.tests.common import login_publisher
from PyPDF2 import PdfFileReader
from pyquery import PyQuery as pq
from webtest import TestApp as Client
from xlrd import open_workbook
from xlrd import xldate_as_tuple
from datetime import datetime


def test_view_issues(gazette_app):
    with freeze_time("2017-11-01 12:00"):
        client = Client(gazette_app)
        login_publisher(client)

        # Test data:
        # 2017:
        #     40: 2017-10-06 / 2017-10-04T12:00:00
        #     41: 2017-10-13 / 2017-10-11T12:00:00
        #     42: 2017-10-20 / 2017-10-18T12:00:00
        #     43: 2017-10-27 / 2017-10-25T12:00:00
        # >>>>>
        #     44: 2017-11-03 / 2017-11-01T12:00:00
        #     45: 2017-11-10 / 2017-11-08T12:00:00
        #     46: 2017-11-17 / 2017-11-15T12:00:00
        #     47: 2017-11-24 / 2017-11-22T12:00:00
        #     48: 2017-12-01 / 2017-11-29T12:00:00
        #     49: 2017-12-08 / 2017-12-06T12:00:00
        #     50: 2017-12-15 / 2017-12-13T12:00:00
        #     51: 2017-12-22 / 2017-12-20T12:00:00
        #     52: 2017-12-29 / 2017-12-27T12:00:00
        # 2018:
        #     1: 2018-01-05 / 2018-01-03T12:00:00

        # add a issue
        manage = client.get('/issues')
        manage = manage.click('Neu')
        manage.form['number'] = '1'
        manage.form['date_'] = '2019-01-02'
        manage.form['deadline'] = '2019-01-01T12:00'
        manage = manage.form.submit().maybe_follow()
        assert 'Ausgabe hinzugefügt.' in manage
        assert '2019-1' in manage
        upcoming_issues = [
            [td.text.strip() for td in pq(tr)('td')]
            for tr in manage.pyquery('#panel_upcoming table.issues tbody tr')
        ]
        past_issues = [
            [td.text.strip() for td in pq(tr)('td')]
            for tr in manage.pyquery('#panel_past table.issues tbody tr')
        ]
        assert upcoming_issues == [
            ['2017-44', '03.11.2017', 'Mittwoch 01.11.2017 13:00', '', ''],
            ['2017-45', '10.11.2017', 'Mittwoch 08.11.2017 13:00', '', ''],
            ['2017-46', '17.11.2017', 'Mittwoch 15.11.2017 13:00', '', ''],
            ['2017-47', '24.11.2017', 'Mittwoch 22.11.2017 13:00', '', ''],
            ['2017-48', '01.12.2017', 'Mittwoch 29.11.2017 13:00', '', ''],
            ['2017-49', '08.12.2017', 'Mittwoch 06.12.2017 13:00', '', ''],
            ['2017-50', '15.12.2017', 'Mittwoch 13.12.2017 13:00', '', ''],
            ['2017-51', '22.12.2017', 'Mittwoch 20.12.2017 13:00', '', ''],
            ['2017-52', '29.12.2017', 'Mittwoch 27.12.2017 13:00', '', ''],
            ['2018-1', '05.01.2018', 'Mittwoch 03.01.2018 13:00', '', ''],
            ['2019-1', '02.01.2019', 'Dienstag 01.01.2019 12:00', '', '']
        ]
        assert past_issues == [
            ['2017-43', '27.10.2017', 'Mittwoch 25.10.2017 14:00', '', ''],
            ['2017-42', '20.10.2017', 'Mittwoch 18.10.2017 14:00', '', ''],
            ['2017-41', '13.10.2017', 'Mittwoch 11.10.2017 14:00', '', ''],
            ['2017-40', '06.10.2017', 'Mittwoch 04.10.2017 14:00', '', ''],
        ]

        # use the first available issue in a notice
        manage = client.get('/notices/drafted/new-notice')
        manage.form['title'] = 'Titel'
        manage.form['organization'] = '200'
        manage.form['category'] = '13'
        manage.form['issues'] = ['2017-44']
        manage.form['text'] = 'Text'
        manage.form['author_place'] = 'Govikon'
        manage.form['author_name'] = 'State Chancellerist'
        manage.form['author_date'] = '2019-01-01'
        manage = manage.form.submit().maybe_follow()
        assert '<h2>Titel</h2>' in manage
        assert 'Nr. 44, 03.11.2017' in manage

        # edit the issue
        manage = client.get('/issues')
        manage = manage.click('Bearbeiten', index=0)
        manage.form['date_'] = '2017-11-02'
        manage.form['deadline'] = '2017-11-01T12:00'
        manage = manage.form.submit().maybe_follow()
        assert 'Ausgabe geändert.' in manage

        upcoming_issues = [
            [td.text.strip() for td in pq(tr)('td')]
            for tr in manage.pyquery('#panel_upcoming table.issues tbody tr')
        ]
        past_issues = [
            [td.text.strip() for td in pq(tr)('td')]
            for tr in manage.pyquery('#panel_past table.issues tbody tr')
        ]
        assert upcoming_issues == [
            ['2017-44', '02.11.2017', 'Mittwoch 01.11.2017 12:00', '', ''],
            ['2017-45', '10.11.2017', 'Mittwoch 08.11.2017 13:00', '', ''],
            ['2017-46', '17.11.2017', 'Mittwoch 15.11.2017 13:00', '', ''],
            ['2017-47', '24.11.2017', 'Mittwoch 22.11.2017 13:00', '', ''],
            ['2017-48', '01.12.2017', 'Mittwoch 29.11.2017 13:00', '', ''],
            ['2017-49', '08.12.2017', 'Mittwoch 06.12.2017 13:00', '', ''],
            ['2017-50', '15.12.2017', 'Mittwoch 13.12.2017 13:00', '', ''],
            ['2017-51', '22.12.2017', 'Mittwoch 20.12.2017 13:00', '', ''],
            ['2017-52', '29.12.2017', 'Mittwoch 27.12.2017 13:00', '', ''],
            ['2018-1', '05.01.2018', 'Mittwoch 03.01.2018 13:00', '', ''],
            ['2019-1', '02.01.2019', 'Dienstag 01.01.2019 12:00', '', '']
        ]
        assert past_issues == [
            ['2017-43', '27.10.2017', 'Mittwoch 25.10.2017 14:00', '', ''],
            ['2017-42', '20.10.2017', 'Mittwoch 18.10.2017 14:00', '', ''],
            ['2017-41', '13.10.2017', 'Mittwoch 11.10.2017 14:00', '', ''],
            ['2017-40', '06.10.2017', 'Mittwoch 04.10.2017 14:00', '', ''],
        ]

        # check if the notice has been updated
        manage = client.get('/notice/titel')
        assert 'Nr. 44, 03.11.2017' not in manage
        assert 'Nr. 44, 02.11.2017' in manage

        # delete all but one (unused) issues
        manage = client.get('/issues')
        manage.click('Löschen', index=1).form.submit()
        manage.click('Löschen', index=2).form.submit()
        manage.click('Löschen', index=3).form.submit()
        manage.click('Löschen', index=4).form.submit()
        manage.click('Löschen', index=5).form.submit()
        manage.click('Löschen', index=6).form.submit()
        manage.click('Löschen', index=7).form.submit()
        manage.click('Löschen', index=8).form.submit()
        manage.click('Löschen', index=9).form.submit()
        manage.click('Löschen', index=10).form.submit()
        manage.click('Löschen', index=11).form.submit()
        manage.click('Löschen', index=12).form.submit()
        manage.click('Löschen', index=13).form.submit()
        manage.click('Löschen', index=14).form.submit()

        manage = client.get('/issues')
        issues = [
            [td.text.strip() for td in pq(tr)('td')]
            for tr in manage.pyquery('table.issues tbody tr')
        ]
        assert issues == [
            ['2017-44', '02.11.2017', 'Mittwoch 01.11.2017 12:00', '', '']
        ]

        # Try to delete the used issue
        manage = client.get('/issues')
        manage = manage.click('Löschen')
        assert 'Es können nur unbenutzte Ausgaben gelöscht werden.' in manage
        assert not manage.forms


def test_view_issues_permissions(gazette_app):
    with freeze_time("2017-10-20 12:00"):
        client = Client(gazette_app)

        login_publisher(client)
        manage = client.get('/issues').click('Neu')
        manage.form['number'] = '1'
        manage.form['date_'] = '2017-01-02'
        manage.form['deadline'] = '2017-01-01T12:00'
        manage = manage.form.submit().maybe_follow()
        edit_link = manage.click('Bearbeiten', index=0).request.url
        delete_link = manage.click('Löschen', index=0).request.url

        login_editor_1(client)
        client.get('/issues', status=403)
        client.get(edit_link, status=403)
        client.get(delete_link, status=403)


def test_view_issues_publish(gazette_app):
    with freeze_time("2017-11-01 12:00"):
        client = Client(gazette_app)
        login_publisher(client)

        for number, issues in enumerate(((44, 45), (45, 46), (45,))):
            slug = 'notice-{}'.format(number)
            manage = client.get('/notices/drafted/new-notice')
            manage.form['title'] = slug
            manage.form['organization'] = '200'
            manage.form['category'] = '13'
            manage.form['issues'] = ['2017-{}'.format(i) for i in issues]
            manage.form['text'] = 'Text'
            manage.form['author_place'] = 'Govikon'
            manage.form['author_name'] = 'State Chancellerist'
            manage.form['author_date'] = '2019-01-01'
            manage = manage.form.submit()

            client.get('/notice/{}/submit'.format(slug)).form.submit()
            if len(issues) > 1:
                client.get('/notice/{}/accept'.format(slug)).form.submit()

        # publish 44
        manage = client.get('/issues').click('Veröffentlichen', index=0)
        manage = manage.form.submit().maybe_follow()
        assert "Ausgabe veröffentlicht." in manage
        assert "2017-44.pdf" in manage

        manage = manage.click('2017-44.pdf')
        assert manage.content_type == 'application/pdf'
        reader = PdfFileReader(BytesIO(manage.body))
        text = ''.join([page.extractText() for page in reader.pages])
        assert text == (
            '© 2017 Govikon\n'
            '1\nAmtsblatt Nr. 44, 03.11.2017\n'
            'Civic Community\n'
            'Commercial Register\n'
            '1\nnotice-0\n'
            'Text\n'
            'Govikon, 1. Januar 2019\n'
            'State Chancellerist\n'
        )

        notice_0 = client.get('/notice/notice-0')
        notice_1 = client.get('/notice/notice-1')
        notice_2 = client.get('/notice/notice-2')
        assert '<li>Nr. 44, 03.11.2017 / 1</li>' in notice_0
        assert '<li>Nr. 45, 10.11.2017</li>' in notice_0
        assert '<li>Nr. 45, 10.11.2017</li>' in notice_1
        assert '<li>Nr. 46, 17.11.2017</li>' in notice_1
        assert '<li>Nr. 45, 10.11.2017</li>' in notice_2

        # publish 46
        manage = client.get('/issues').click('Veröffentlichen', index=2)
        manage = manage.form.submit().maybe_follow()
        assert "Ausgabe veröffentlicht." in manage
        assert "2017-46.pdf" in manage

        manage = manage.click('2017-46.pdf')
        assert manage.content_type == 'application/pdf'
        reader = PdfFileReader(BytesIO(manage.body))
        text = ''.join([page.extractText() for page in reader.pages])
        assert text == (
            '© 2017 Govikon\n'
            '1\nAmtsblatt Nr. 46, 17.11.2017\n'
            'Civic Community\n'
            'Commercial Register\n'
            '2\nnotice-1\n'
            'Text\n'
            'Govikon, 1. Januar 2019\n'
            'State Chancellerist\n'
        )

        notice_0 = client.get('/notice/notice-0')
        notice_1 = client.get('/notice/notice-1')
        notice_2 = client.get('/notice/notice-2')
        assert '<li>Nr. 44, 03.11.2017 / 1</li>' in notice_0
        assert '<li>Nr. 45, 10.11.2017</li>' in notice_0
        assert '<li>Nr. 45, 10.11.2017</li>' in notice_1
        assert '<li>Nr. 46, 17.11.2017 / 2</li>' in notice_1
        assert '<li>Nr. 45, 10.11.2017</li>' in notice_2

        # publish 45
        manage = client.get('/issues').click('Veröffentlichen', index=1)
        assert "Diese Ausgabe hat eingereichte Meldungen!" in manage
        manage = manage.form.submit().maybe_follow()
        assert "Ausgabe veröffentlicht." in manage
        assert "2017-45.pdf" in manage

        manage = manage.click('2017-45.pdf')
        assert manage.content_type == 'application/pdf'
        reader = PdfFileReader(BytesIO(manage.body))
        text = ''.join([page.extractText() for page in reader.pages])
        assert text == (
            '© 2017 Govikon\n'
            '1\nAmtsblatt Nr. 45, 10.11.2017\n'
            'Civic Community\n'
            'Commercial Register\n'
            '2\nnotice-0\n'
            'Text\n'
            'Govikon, 1. Januar 2019\n'
            'State Chancellerist\n'
            '3\nnotice-1\n'
            'Text\n'
            'Govikon, 1. Januar 2019\n'
            'State Chancellerist\n'
        )

        notice_0 = client.get('/notice/notice-0')
        notice_1 = client.get('/notice/notice-1')
        notice_2 = client.get('/notice/notice-2')
        assert '<li>Nr. 44, 03.11.2017 / 1</li>' in notice_0
        assert '<li>Nr. 45, 10.11.2017 / 2</li>' in notice_0
        assert '<li>Nr. 45, 10.11.2017 / 3</li>' in notice_1
        assert '<li>Nr. 46, 17.11.2017 / 2</li>' in notice_1
        assert '<li>Nr. 45, 10.11.2017</li>' in notice_2  # submitted

        # re-publish 46
        manage = client.get('/issues').click('Veröffentlichen', index=2)
        assert "Diese Ausgabe hat bereits ein PDF!" in manage
        assert "Diese Ausgabe hat bereits Publikationsnummern!" in manage
        manage = manage.form.submit().maybe_follow()
        assert "Ausgabe veröffentlicht." in manage
        assert "2017-46.pdf" in manage
        assert "Publikationsnummern haben geändert" in manage

        manage = manage.click('2017-46.pdf')
        assert manage.content_type == 'application/pdf'
        reader = PdfFileReader(BytesIO(manage.body))
        text = ''.join([page.extractText() for page in reader.pages])
        assert text == (
            '© 2017 Govikon\n'
            '1\nAmtsblatt Nr. 46, 17.11.2017\n'
            'Civic Community\n'
            'Commercial Register\n'
            '4\nnotice-1\n'
            'Text\n'
            'Govikon, 1. Januar 2019\n'
            'State Chancellerist\n'
        )

        notice_0 = client.get('/notice/notice-0')
        notice_1 = client.get('/notice/notice-1')
        notice_2 = client.get('/notice/notice-2')
        assert '<li>Nr. 44, 03.11.2017 / 1</li>' in notice_0
        assert '<li>Nr. 45, 10.11.2017 / 2</li>' in notice_0
        assert '<li>Nr. 45, 10.11.2017 / 3</li>' in notice_1
        assert '<li>Nr. 46, 17.11.2017 / 4</li>' in notice_1
        assert '<li>Nr. 45, 10.11.2017</li>' in notice_2  # submitted


def test_view_issues_publish_disabled(gazette_app):
    client = Client(gazette_app)
    login_publisher(client)

    manage = client.get('/issues')
    assert "PDF" in manage
    assert "Veröffentlichen" in manage

    manage = client.get('/issue/2017-40/publish')
    assert "Veröffentlichung ist deaktiviert." not in manage
    assert 'form' in manage

    principal = gazette_app.principal
    principal.publishing = False
    gazette_app.cache.set('principal', principal)

    manage = client.get('/issues')
    assert "PDF" not in manage
    assert "Veröffentlichen" not in manage

    manage = client.get('/issue/2017-40/publish')
    assert "Veröffentlichung ist deaktiviert." in manage
    assert 'form' not in manage


def test_view_issues_export(gazette_app):
    client = Client(gazette_app)

    client.get('/issues/export', status=403)

    login_editor_1(client)
    client.get('/issues/export', status=403)

    login_publisher(client)
    response = client.get('/issues/export')

    book = open_workbook(file_contents=response.body)
    assert book.nsheets == 1

    sheet = book.sheets()[0]
    assert sheet.ncols == 4
    assert sheet.nrows == 15

    def as_date(cell):
        return datetime(
            *xldate_as_tuple(cell.value, book.datemode)
        ).date().isoformat()

    def as_datetime(cell):
        return datetime(
            *xldate_as_tuple(cell.value, book.datemode)
        ).isoformat()

    assert sheet.cell(0, 0).value == 'Jahr'
    assert sheet.cell(0, 1).value == 'Nummer'
    assert sheet.cell(0, 2).value == 'Datum'
    assert sheet.cell(0, 3).value == 'Eingabeschluss'

    assert int(sheet.cell(1, 0).value) == 2017
    assert int(sheet.cell(1, 1).value) == 40
    assert as_date(sheet.cell(1, 2)) == '2017-10-06'
    assert as_datetime(sheet.cell(1, 3)) == '2017-10-04T14:00:00'

    assert int(sheet.cell(5, 0).value) == 2017
    assert int(sheet.cell(5, 1).value) == 44
    assert as_date(sheet.cell(5, 2)) == '2017-11-03'
    assert as_datetime(sheet.cell(5, 3)) == '2017-11-01T13:00:00'

    assert int(sheet.cell(13, 0).value) == 2017
    assert int(sheet.cell(13, 1).value) == 52
    assert as_date(sheet.cell(13, 2)) == '2017-12-29'
    assert as_datetime(sheet.cell(13, 3)) == '2017-12-27T13:00:00'

    assert int(sheet.cell(14, 0).value) == 2018
    assert int(sheet.cell(14, 1).value) == 1
    assert as_date(sheet.cell(14, 2)) == '2018-01-05'
    assert as_datetime(sheet.cell(14, 3)) == '2018-01-03T13:00:00'
