from onegov.core.request import CoreRequest
from onegov.core.utils import module_path
from pytest import mark
from unittest.mock import patch
from webtest.forms import Upload


@mark.parametrize("pdf_1, pdf_2", [(
    module_path('onegov.wtfs', 'tests/fixtures/example_1.pdf'),
    module_path('onegov.wtfs', 'tests/fixtures/example_2.pdf')
)])
def test_views_user_manual(client, pdf_1, pdf_2):
    with open(pdf_1, 'rb') as file:
        pdf_1 = file.read()
    with open(pdf_2, 'rb') as file:
        pdf_2 = file.read()

    client.login_admin()

    view = client.get('/user-manual')
    client.get('http://localhost/user-manual/pdf', status=503)
    assert "Noch kein Benutzerhandbuch vorhanden." in view

    add = view.click("Bearbeiten")
    add.form['pdf'] = Upload(f'Handbuch.pdf', pdf_1, 'application/pdf')
    added = add.form.submit().follow()
    assert "Benutzerhandbuch geändert." in added
    assert "Benutzerhandbuch (PDF, 8.1 kB)." in added
    assert client.get('http://localhost/user-manual/pdf').body == pdf_1

    # Edit
    edited = view.click("Bearbeiten")
    assert "user_manual.pdf (8.1 kB)" in str(edited.form.html)
    edited.form.get('pdf', 0).select('replace')
    edited.form.get('pdf', 1).value = Upload(f'xx', pdf_2, 'application/pdf')
    editeded = edited.form.submit().follow()
    assert "Benutzerhandbuch geändert." in editeded
    assert "Benutzerhandbuch (PDF, 9.1 kB)." in editeded
    assert client.get('http://localhost/user-manual/pdf').body == pdf_2

    # Delete
    edited = view.click("Bearbeiten")
    assert "user_manual.pdf (9.1 kB)" in str(edited.form.html)
    edited.form.get('pdf', 0).select('delete')
    editeded = edited.form.submit().follow()
    assert "Benutzerhandbuch geändert." in editeded
    assert "Benutzerhandbuch (PDF, 9.1 kB)." not in editeded
    assert client.get('http://localhost/user-manual/pdf', status=503)


@patch.object(CoreRequest, 'assert_valid_csrf_token')
def test_views_user_manual_permissions(mock_method, client):
    client.get('/user-manual', status=403)
    client.get('/user-manual/edit', status=403)

    client.login_member()
    client.get('/user-manual')
    client.get('/user-manual/edit', status=403)
    client.logout()

    client.login_editor()
    client.get('/user-manual')
    client.get('/user-manual/edit', status=403)
    client.logout()

    client.login_admin()
    client.get('/user-manual')
    client.get('/user-manual/edit')
    client.logout()
