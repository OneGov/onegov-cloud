from freezegun import freeze_time
from onegov.core.request import CoreRequest
from unittest.mock import patch
from webtest.forms import Upload


def test_views_daily_job(client):
    # Add a municipality with dates
    client.login_admin()

    add = client.get('/municipalities').click(href='add')
    add.form['name'] = "My Municipality"
    add.form['bfs_number'] = '1'
    add.form['group_id'].select(text="My Group")
    assert "My Municipality" in add.form.submit().follow()

    upload = client.get('/municipalities').click("Daten importieren")
    upload.form['file'] = Upload(
        'test.csv',
        "Gemeinde-Nr,Vordefinierte Termine\n1,5.1.2019".encode('utf-8'),
        'text/csv'
    )
    assert "Gemeindedaten importiert." in upload.form.submit().follow()

    # Add a scan job
    with freeze_time("2019-01-01"):
        add = client.get('/scan-jobs').click(href='add')
        add.form['type'].select("normal")
        add.form['municipality_id'].select(text="My Municipality")
        add.form['dispatch_date'] = "2019-01-05"
        add.form['dispatch_boxes'] = "10034550"
        add.form['dispatch_cantonal_tax_office'] = "62388304"
        add.form['dispatch_cantonal_scan_center'] = "712283912"
        added = add.form.submit().follow()
        assert "Scan-Auftrag hinzugefügt." in added

        edit = client.get('/scan-jobs').click("05.01.2019").click("Bearbeiten")
        edit.form['return_date'] = "2019-01-10"
        edit.form['return_boxes'] = "28891238"
        assert "Scan-Auftrag geändert." in edit.form.submit().follow()

    # View daily list
    view = client.get('/daily-list/boxes/2019-01-05')
    assert "10034550" in view
    assert "62388304" in view
    assert "712283912" in view
    assert "28891238" not in view

    view = client.get('/daily-list/boxes/2019-01-10')
    assert "10034550" not in view
    assert "62388304" not in view
    assert "712283912" not in view
    assert "28891238" in view


@patch.object(CoreRequest, 'assert_valid_csrf_token')
def test_views_daily_jobs_permissions(mock_method, client):
    client.get(f'/daily-list/boxes/2019-01-10', status=403)

    client.login_optimo()
    client.get(f'/daily-list/boxes/2019-01-10')
    client.logout()

    client.login_member()
    client.get(f'/daily-list/boxes/2019-01-10', status=403)
    client.logout()

    client.login_editor()
    client.get(f'/daily-list/boxes/2019-01-10', status=403)
    client.logout()

    client.login_admin()
    client.get(f'/daily-list/boxes/2019-01-10')
    client.logout()
