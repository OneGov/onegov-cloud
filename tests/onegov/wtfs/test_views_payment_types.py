from onegov.core.request import CoreRequest
from unittest.mock import patch


def test_views_payment_types(client):
    client.login_admin()

    edit = client.get('/payment-types')
    assert edit.form['normal'].value == '7.0'
    assert edit.form['spezial'].value == '8.5'

    edit.form['normal'] = 8
    edit.form['spezial'] = 9.9
    edited = edit.form.submit().follow()
    assert "geändert." in edited

    view = client.get('/payment-types')
    assert view.form['normal'].value == '8.0'
    assert view.form['spezial'].value == '9.9'


@patch.object(CoreRequest, 'assert_valid_csrf_token')
def test_views_payment_types_permissions(mock_method, client):
    client.get('/payment-types', status=403)

    client.login_member()
    client.get('/payment-types', status=403)
    client.logout()

    client.login_editor()
    client.get('/payment-types', status=403)
    client.logout()

    client.login_admin()
    client.get('/payment-types')
    client.logout()
