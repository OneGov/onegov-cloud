from freezegun import freeze_time
from onegov.core.request import CoreRequest
from unittest.mock import patch
from webtest.forms import Upload


def test_views_report(client):
    # Add a municipality with dates
    client.login_admin()

    add = client.get('/municipalities').click(href='/add')
    add.form['name'] = "Adlikon"
    add.form['bfs_number'] = '1'
    add.form['payment_type'] = 'normal'
    assert "Adlikon" in add.form.submit().follow()

    upload = client.get('/municipalities').click("Daten importieren")
    upload.form['file'] = Upload(
        'test.csv',
        "Gemeinde;1;-1;Normal;5.1.2019".encode('cp1252'),
        'text/csv'
    )
    assert "Gemeindedaten importiert." in upload.form.submit().follow()

    # Add a scan job
    with freeze_time("2019-01-01"):
        add = client.get('/scan-jobs/unrestricted').click(href='/add')
        add.form['type'].select("normal")
        add.form['municipality_id'].select(text="Adlikon (1)")
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
        edit.form['return_tax_forms_older'] = "9600"
        edit.form['return_tax_forms_last_year'] = "9700"
        edit.form['return_tax_forms_current_year'] = "9800"
        edit.form['return_single_documents'] = "9900"
        edit.form['return_unscanned_tax_forms_older'] = "96"
        edit.form['return_unscanned_tax_forms_last_year'] = "97"
        edit.form['return_unscanned_tax_forms_current_year'] = "98"
        edit.form['return_unscanned_single_documents'] = "99"
        assert "Scan-Auftrag geändert." in edit.form.submit().maybe_follow()

    def get_report(report_type, start, end, scan_job_type='all'):
        select = client.get('/report')
        select.form['start'] = start
        select.form['end'] = end
        select.form['report_type'].select(report_type)
        select.form['scan_job_type'].select(scan_job_type)
        select.form['municipality_id'].select(text='Adlikon (1)')
        return select.form.submit().follow()

    # Boxes
    view = get_report('boxes', '2019-01-01', '2019-01-05')
    assert "1111" in view
    assert "2222" in view
    assert "3333" in view
    assert "8888" in view

    view = get_report('boxes', '2019-01-06', '2019-01-10')
    assert "1111" not in view
    assert "2222" not in view
    assert "3333" not in view
    assert "8888" not in view

    # Boxes and forms
    view = get_report('boxes_and_forms', '2019-01-01', '2019-01-05')
    assert "8888" in view
    assert "9504" in view
    assert "9603" in view
    assert "9702" in view
    assert "9801" in view

    view = get_report('boxes_and_forms', '2019-01-06', '2019-01-10')
    assert "8888" not in view
    assert "9504" not in view
    assert "9603" not in view
    assert "9702" not in view
    assert "9801" not in view

    # Forms
    view = get_report('forms', '2019-01-01', '2019-01-05')
    assert "9504" in view
    assert "9603" in view
    assert "9702" in view

    view = get_report('forms', '2019-01-06', '2019-01-10')
    assert "9504" not in view
    assert "9603" not in view
    assert "9702" not in view

    # By delivery
    view = get_report('delivery', '2019-01-01', '2019-01-05')
    assert "8888" in view
    assert "9504" in view
    assert "9603" in view
    assert "9702" in view
    assert "9801" in view

    view = get_report('delivery', '2019-01-06', '2019-01-10')
    assert "8888" not in view
    assert "9504" not in view
    assert "9603" not in view
    assert "9702" not in view
    assert "9801" not in view


@patch.object(CoreRequest, 'assert_valid_csrf_token')
def test_views_report_permissions(mock_method, client):
    client.login_admin()
    add = client.get('/municipalities').click(href='/add')
    add.form['name'] = "Adlikon"
    add.form['bfs_number'] = '1'
    add.form['payment_type'] = 'normal'
    added = add.form.submit().follow()
    assert "Adlikon" in added
    id = added.click("Adlikon").request.url.split('/')[-1]
    client.logout()

    urls = (
        '/report/boxes/2019-02-19/2019-02-19',
        '/report/boxes-and-forms/2019-02-19/2019-02-19/all',
        f'/report/forms/2019-02-19/2019-02-19/all/{id}',
    )

    for url in urls:
        client.get(url, status=403)

    client.login_member()
    for url in urls:
        client.get(url, status=403)
    client.logout()

    client.login_editor()
    for url in urls:
        client.get(url, status=403)
    client.logout()

    client.login_admin()
    for url in urls:
        client.get(url)
    client.logout()
