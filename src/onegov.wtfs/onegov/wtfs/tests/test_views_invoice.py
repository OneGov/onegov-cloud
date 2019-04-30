from freezegun import freeze_time
from onegov.core.request import CoreRequest
from unittest.mock import patch
from webtest.forms import Upload


def test_views_invoices(client):
    # Add a municipality with dates
    client.login_admin()

    add = client.get('/municipalities').click(href='/add')
    add.form['name'] = "Adlikon"
    add.form['bfs_number'] = '1'
    add.form['gpn_number'] = '11223344'
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
        add.form['dispatch_tax_forms_older'] = "30"
        add.form['dispatch_tax_forms_last_year'] = "20"
        add.form['dispatch_tax_forms_current_year'] = "10"
        assert "Scan-Auftrag hinzugefügt." in add.form.submit().maybe_follow()

        edit = client.get('/scan-jobs/unrestricted')\
            .click("05.01.2019").click("Bearbeiten")
        edit.form['return_date'] = "2019-01-10"
        edit.form['return_unscanned_tax_forms_older'] = "3"
        edit.form['return_unscanned_tax_forms_last_year'] = "2"
        edit.form['return_unscanned_tax_forms_current_year'] = "1"

        assert "Scan-Auftrag geändert." in edit.form.submit().maybe_follow()

    with freeze_time("2019-01-02"):
        create = client.get('/invoice')
        create.form['from_date'] = "2019-01-01"
        create.form['to_date'] = "2019-01-07"
        create.form['cs2_user'] = "123"
        create.form['subject'] = "Rechnungen"
        create.form['municipality_id'].select(text="Adlikon (1)")
        create.form['accounting_unit'] = "456"
        create.form['revenue_account'] = "789"
        created = create.form.submit()
        assert created.headers['Content-Type'] == 'text/csv; charset=UTF-8'
        assert created.headers['Content-Disposition'] == (
            'inline; filename=rechnungen.csv'
        )

        invoice = created.text
        assert "11223344" in invoice
        assert "Rechnungen" in invoice
        assert "123" in invoice
        assert "456" in invoice
        assert "789" in invoice
        assert "2019-01-02" in invoice
        assert "-00000000000006000" in invoice
        assert "+00000000070000000" in invoice


@patch.object(CoreRequest, 'assert_valid_csrf_token')
def test_views_invoice_permissions(mock_method, client):
    client.get('/invoice', status=403)

    client.login_member()
    client.get('/invoice', status=403)
    client.logout()

    client.login_editor()
    client.get('/invoice', status=403)
    client.logout()

    client.login_admin()
    client.get('/invoice')
    client.logout()
