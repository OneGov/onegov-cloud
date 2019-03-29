from freezegun import freeze_time
from onegov.core.request import CoreRequest
from unittest.mock import patch
from webtest.forms import Upload


def test_views_scan_job(client):
    # Add municipality dates
    client.login_admin()

    upload = client.get('/municipalities').click("Daten importieren")
    upload.form['file'] = Upload(
        'test.csv',
        "Gemeinde-Nr,Vordefinierte Termine\n1,5.1.2019".encode('utf-8'),
        'text/csv'
    )
    assert "Gemeindedaten importiert." in upload.form.submit().follow()

    # Add a scan job
    client.logout()
    client.login_member()
    with freeze_time("2019-01-01"):
        add = client.get('/scan-jobs').click(href='/add')
        add.form['type'].select("normal")
        add.form['dispatch_date_normal'].select("2019-01-05")
        add.form['dispatch_boxes'] = "1"
        add.form['dispatch_tax_forms_current_year'] = "2"
        add.form['dispatch_tax_forms_last_year'] = "3"
        add.form['dispatch_tax_forms_older'] = "4"
        add.form['dispatch_single_documents'] = "5"
        add.form['dispatch_cantonal_tax_office'] = "6"
        add.form['dispatch_cantonal_scan_center'] = "7"
        add.form['dispatch_note'] = "Bemerkung zur Abholung"
        added = add.form.submit().follow()
        assert "Scan-Auftrag hinzugefügt." in added
        assert "05.01.2019" in added

        message = client.app.smtp.outbox.pop()
        assert message['From'] == 'mails@govikon.ch'
        assert message['To'] == 'member@example.org'
        assert message['Reply-To'] == 'mails@govikon.ch'
        payload = message.get_payload(1).get_payload(decode=True)
        payload = payload.decode('utf-8')
        assert "am 05.01.2019 Ihre Sendung abholen" in payload

    # View scan job
    view = client.get('/scan-jobs').click("05.01.2019")
    assert "Scan-Auftrag Nr. 1" in view
    assert "My Municipality" in view
    assert "05.01.2019" in view
    assert all([f">{number}<" in view for number in range(1, 7 + 1)])
    assert "Lieferung an das Steueramt Winterthur am 05.01.2019" in view
    assert "Bemerkung zur Abholung" in view

    # Delivery note
    view = view.click("Lieferschein")
    assert "My Municipality" in view
    assert "05.01.2019" in view
    assert all([f">{number}<" in view for number in range(1, 5 + 1)])
    assert "Lieferung an das Steueramt Winterthur" in view

    # Edit scan job
    client.logout()
    client.login_editor()
    edit = client.get('/scan-jobs').click("05.01.2019").click("Bearbeiten")
    edit.form['dispatch_note'] = "Eine Bemerkung zur Abholung"
    assert "Scan-Auftrag geändert." in edit.form.submit().follow()

    view = client.get('/scan-jobs').click("05.01.2019")
    assert "Scan-Auftrag Nr. 1" in view
    assert "My Municipality" in view
    assert "05.01.2019" in view
    assert all([f">{number}<" in view for number in range(1, 7 + 1)])
    assert "Lieferung an das Steueramt Winterthur am 05.01.2019" in view
    assert "Eine Bemerkung zur Abholung" in view

    client.logout()
    client.login_admin()

    with freeze_time("2019-01-02"):
        edit = client.get('/scan-jobs/unrestricted')\
            .click("05.01.2019").click("Bearbeiten")
        edit.form['return_date'] = "2019-01-10"
        edit.form['return_boxes'] = "8"
        edit.form['return_tax_forms_current_year'] = "9"
        edit.form['return_tax_forms_last_year'] = "10"
        edit.form['return_tax_forms_older'] = "11"
        edit.form['return_single_documents'] = "12"
        edit.form['return_unscanned_tax_forms_current_year'] = "13"
        edit.form['return_unscanned_tax_forms_last_year'] = "14"
        edit.form['return_unscanned_tax_forms_older'] = "15"
        edit.form['return_unscanned_single_documents'] = "16"
        edit.form['return_note'] = "Bemerkung zur Rücksendung"
        assert "Scan-Auftrag geändert." in edit.form.submit().follow()

    view = client.get('/scan-jobs/unrestricted').click("05.01.2019")
    assert "Scan-Auftrag Nr. 1" in view
    assert "My Municipality" in view
    assert "05.01.2019" in view
    assert all([f">{number}<" in view for number in range(1, 16 + 1)])
    assert "Lieferung an das Steueramt Winterthur am 05.01.2019" in view
    assert "Rücksendung an My Municipality am 10.01.2019" in view
    assert "Bemerkung zur Abholung" in view
    assert "Bemerkung zur Rücksendung" in view

    # Check the date hints
    with freeze_time("2019-01-01"):
        edit = client.get('/scan-jobs/unrestricted')\
            .click("05.01.2019").click("Bearbeiten")
        dates = client.post(
            '/dispatch-dates',
            {
                'csrf_token': edit.form['csrf_token'].value,
                'municipality_id': edit.form['municipality_id'].value
            }
        )
        assert "05.01.2019" in dates

    # Delete scan job
    deleted = client.get('/scan-jobs/unrestricted')\
        .click("05.01.2019").click("Löschen")
    assert deleted.status_int == 200
    assert "05.01.2019" not in client.get('/scan-jobs')


def test_views_scan_jobs_filter(client):
    # Add municipality dates
    client.login_admin()

    upload = client.get('/municipalities').click("Daten importieren")
    upload.form['file'] = Upload(
        'test.csv',
        "Gemeinde-Nr,Vordefinierte Termine\n1,5.1.2019".encode('utf-8'),
        'text/csv'
    )
    assert "Gemeindedaten importiert." in upload.form.submit().follow()

    # Add scan jobs
    client.logout()
    client.login_member()
    with freeze_time("2019-01-01"):
        add = client.get('/scan-jobs').click(href='/add')
        add.form['type'].select('normal')
        add.form['dispatch_date_normal'].select("2019-01-05")
        assert "Scan-Auftrag hinzugefügt." in add.form.submit().follow()

        client.logout()
        client.login_editor()
        add = client.get('/scan-jobs').click(href='/add')
        add.form['type'].select('express')
        add.form['dispatch_date_express'] = "2019-01-04"
        assert "Scan-Auftrag hinzugefügt." in add.form.submit().follow()

        add.form['type'].select('express')
        add.form['dispatch_date_express'] = "2019-01-06"
        assert "Scan-Auftrag hinzugefügt." in add.form.submit().follow()

    # View scan jobs
    view = client.get('/scan-jobs')
    assert view.pyquery('table.scan-jobs td').text() == (
        '06.01.2019 3 express '
        '05.01.2019 1 normal '
        '04.01.2019 2 express'
    )

    view.form.get('type', index=0).checked = False
    view = view.form.submit()
    assert view.pyquery('table.scan-jobs td').text() == (
        '06.01.2019 3 express '
        '04.01.2019 2 express'
    )

    view = view.click("Lieferscheinnummer")
    assert view.pyquery('table.scan-jobs td').text() == (
        '04.01.2019 2 express '
        '06.01.2019 3 express'
    )

    client.logout()
    client.login_admin()
    view = client.get('/scan-jobs/unrestricted')
    assert view.pyquery('table.scan-jobs td').text() == (
        '06.01.2019 3 express My Municipality '
        '05.01.2019 1 normal My Municipality '
        '04.01.2019 2 express My Municipality'
    )


@patch.object(CoreRequest, 'assert_valid_csrf_token')
def test_views_scan_jobs_permissions(mock_method, client):
    client.login_admin()

    add = client.get('/municipalities').click(href='/add')
    add.form['name'] = "My Municipality"
    add.form['bfs_number'] = '1'
    add.form['payment_type'] = 'normal'
    assert "My Municipality" in add.form.submit().follow()

    with freeze_time("2019-01-01"):
        add = client.get('/scan-jobs/unrestricted').click(href='/add')
        add.form['type'].select("express")
        add.form['dispatch_date'] = "2019-01-05"
        assert "Scan-Auftrag hinzugefügt." in add.form.submit().maybe_follow()
        id = client.get('/scan-jobs/unrestricted').click("05.01.2019")\
            .request.url.split('/')[-1]

    client.logout()

    client.get('/scan-jobs', status=403)
    client.get('/scan-jobs/add', status=403)
    client.get(f'/scan-job/{id}', status=403)
    client.get(f'/scan-job/{id}/edit', status=403)
    client.get('/scan-jobs/unrestricted', status=403)
    client.get('/scan-jobs/add-unrestricted', status=403)
    client.get(f'/scan-job/{id}/edit-unrestricted', status=403)
    client.delete(f'/scan-job/{id}', status=403)

    client.login_member()
    client.get('/scan-jobs')
    client.get('/scan-jobs/add')
    client.get(f'/scan-job/{id}')
    client.get(f'/scan-job/{id}/edit')
    client.get('/scan-jobs/unrestricted', status=403)
    client.get('/scan-jobs/add-unrestricted', status=403)
    client.get(f'/scan-job/{id}/edit-unrestricted', status=403)
    client.delete(f'/scan-job/{id}', status=403)
    client.logout()

    client.login_editor()
    client.get('/scan-jobs')
    client.get('/scan-jobs/add')
    client.get(f'/scan-job/{id}')
    client.get(f'/scan-job/{id}/edit')
    client.get('/scan-jobs/unrestricted', status=403)
    client.get('/scan-jobs/add-unrestricted', status=403)
    client.get(f'/scan-job/{id}/edit-unrestricted', status=403)
    client.delete(f'/scan-job/{id}', status=403)
    client.logout()

    client.login_admin()
    client.get('/scan-jobs')
    client.get('/scan-jobs/add')
    client.get(f'/scan-job/{id}')
    client.get(f'/scan-job/{id}/edit')
    client.get('/scan-jobs/unrestricted')
    client.get('/scan-jobs/add-unrestricted')
    client.get(f'/scan-job/{id}/edit-unrestricted')
    client.delete(f'/scan-job/{id}')
    client.logout()
