from webtest import Upload


def test_view_files(client):
    assert client.get('/files', expect_errors=True).status_code == 403

    client.login_admin()

    files_page = client.get('/files')

    assert "Noch keine Dateien hochgeladen" in files_page

    files_page.form['file'] = [Upload('Test.txt', b'File content.')]
    files_page.form.submit()

    files_page = client.get('/files')
    assert "Noch keine Dateien hochgeladen" not in files_page
    assert 'Test.txt' in files_page
