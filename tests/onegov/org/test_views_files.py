from __future__ import annotations

from webtest import Upload


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .conftest import Client


def test_view_files(client: Client) -> None:
    assert client.get('/files', expect_errors=True).status_code == 403

    client.login_admin()

    files_page = client.get('/files')

    assert "Noch keine Dateien hochgeladen" in files_page

    files_page.form['file'] = [Upload('Test.txt', b'File content.')]
    files_page.form.submit()

    files_page = client.get('/files')
    assert "Noch keine Dateien hochgeladen" not in files_page
    assert 'Test.txt' in files_page
