import datetime

import freezegun
from dateutil.relativedelta import relativedelta
from webtest import Upload


def test_view_files(client):
    assert client.get('/files', expect_errors=True).status_code == 403

    client.login_admin()

    files_page = client.get('/files')

    assert "Noch keine Dateien hochgeladen" in files_page

    files_page.form['file'] = Upload('Test.txt', b'File content.')
    files_page.form.submit()

    files_page = client.get('/files')
    assert "Noch keine Dateien hochgeladen" not in files_page
    assert 'Test.txt' in files_page


def test_view_files_order_by_date(client):
    assert client.get('/files', expect_errors=True).status_code == 403

    client.login_admin()
    files_page = client.get('/files')
    assert "Noch keine Dateien hochgeladen" in files_page
    client.logout()

    start_of_this_month = datetime.datetime.now().replace(
        day=1, hour=0, minute=0, second=0, microsecond=0)
    end_of_last_month = start_of_this_month + relativedelta(microseconds=-1)

    with freezegun.freeze_time(end_of_last_month.astimezone()):
        client.login_admin()
        files_page = client.get('/files')
        files_page.form['file'] = Upload('Last Month.txt',
                                         b'File content .')
        files_page.form.submit()
        client.logout()

    with freezegun.freeze_time(start_of_this_month.astimezone()):
        client.login_admin()
        files_page = client.get('/files')
        files_page.form['file'] = Upload('This Month.txt',
                                         b'File content.')
        files_page.form.submit()
        client.logout()

    client.login_admin()
    files_page = client.get('/files?order_by=date')
    assert "Noch keine Dateien hochgeladen" not in files_page
    assert start_of_this_month.strftime('%d.%m.%Y %H:%M') in files_page
    assert end_of_last_month.strftime('%d.%m.%Y %H:%M') in files_page
    assert 'Last Month.txt' in files_page
    assert 'This Month.txt' in files_page
    assert 'Letzter Monat' in files_page
    assert 'Diesen Monat' in files_page

    # page content:
    # ...
    # Alle Dateien
    # Name 		Erweiterung 	Diesen Monat
    # This Month.txt 		txt 	01.06.2024 00:00
    # Name 		Erweiterung 	Letzter Monat
    # Last Month.txt 		txt 	31.05.2024 23:59
    # ...
