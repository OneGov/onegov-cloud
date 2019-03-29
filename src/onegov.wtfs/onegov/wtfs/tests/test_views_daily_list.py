from freezegun import freeze_time
from onegov.core.request import CoreRequest
from unittest.mock import patch
from webtest.forms import Upload


def test_views_daily_job(client):
    # Add a municipality with dates
    client.login_admin()

    add = client.get('/municipalities').click(href='/add')
    add.form['name'] = "My Municipality"
    add.form['bfs_number'] = '1'
    add.form['payment_type'] = 'normal'
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
        add = client.get('/scan-jobs/unrestricted').click(href='/add')
        add.form['type'].select("normal")
        add.form['municipality_id'].select(text="My Municipality (1)")
        add.form['dispatch_date'] = "2019-01-05"
        add.form['dispatch_boxes'] = "1111"
        add.form['dispatch_cantonal_tax_office'] = "2222"
        add.form['dispatch_cantonal_scan_center'] = "3333"
        add.form['dispatch_tax_forms_older'] = "4444"
        add.form['dispatch_tax_forms_last_year'] = "5555"
        add.form['dispatch_tax_forms_current_year'] = "6666"
        add.form['dispatch_single_documents'] = "7777"
        assert "Scan-Auftrag hinzugefügt." in add.form.submit().maybe_follow()

        edit = client.get('/scan-jobs/unrestricted')\
            .click("05.01.2019").click("Bearbeiten")
        edit.form['return_date'] = "2019-01-10"
        edit.form['return_boxes'] = "8888"
        assert "Scan-Auftrag geändert." in edit.form.submit().maybe_follow()

    def get_daily_list(type, date_):
        select = client.get('/daily-list')
        select.form['type'].select(type)
        select.form['date'] = date_
        return select.form.submit().follow()

    # View daily list boxes
    view = get_daily_list('boxes', '2019-01-05')
    assert "1111" in view
    assert "2222" in view
    assert "3333" in view
    assert "8888" not in view

    view = get_daily_list('boxes', '2019-01-10')
    assert "1111" not in view
    assert "2222" not in view
    assert "3333" not in view
    assert "8888" in view

    # View daily list boxes and forms
    view = get_daily_list('boxes_and_forms', '2019-01-05')
    assert "1111" in view
    assert "2222" in view
    assert "3333" in view
    assert "4444" in view
    assert "5555" in view
    assert "6666" in view

    view = get_daily_list('boxes_and_forms', '2019-01-10')
    assert "1111" not in view
    assert "2222" not in view
    assert "3333" not in view
    assert "4444" not in view
    assert "5555" not in view
    assert "6666" not in view


@patch.object(CoreRequest, 'assert_valid_csrf_token')
def test_views_daily_jobs_permissions(mock_method, client):
    client.get(f'/daily-list/boxes/2019-01-10', status=403)
    client.get(f'/daily-list/boxes-and-forms/2019-01-10', status=403)

    client.login_optimo()
    client.get(f'/daily-list/boxes/2019-01-10')
    client.get(f'/daily-list/boxes-and-forms/2019-01-10', status=403)
    client.logout()

    client.login_member()
    client.get(f'/daily-list/boxes/2019-01-10', status=403)
    client.get(f'/daily-list/boxes-and-forms/2019-01-10', status=403)
    client.logout()

    client.login_editor()
    client.get(f'/daily-list/boxes/2019-01-10', status=403)
    client.get(f'/daily-list/boxes-and-forms/2019-01-10', status=403)
    client.logout()

    client.login_admin()
    client.get(f'/daily-list/boxes/2019-01-10')
    client.get(f'/daily-list/boxes-and-forms/2019-01-10')
    client.logout()
