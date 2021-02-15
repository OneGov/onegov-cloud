import re

from webtest import Upload

from tests.shared.utils import create_image


def test_manage_album(client):
    client.login_editor()

    albums = client.get('/photoalbums')
    assert "Noch keine Fotoalben" in albums

    new = albums.click('Fotoalbum')
    new.form['title'] = "Comicon 2016"
    new.form.submit()

    albums = client.get('/photoalbums')
    assert "Comicon 2016" in albums

    album = albums.click("Comicon 2016")
    assert "Comicon 2016" in album
    assert "noch keine Bilder" in album

    images = albums.click("Bilder verwalten")
    images.form['file'] = Upload('test.jpg', create_image().read())
    images.form.submit()

    select = album.click("Bilder auswählen")
    select.form[tuple(select.form.fields.keys())[1]] = True
    select.form.submit()

    album = albums.click("Comicon 2016")
    assert "noch keine Bilder" not in album

    images = albums.click("Bilder verwalten")

    url = re.search(r'data-note-update-url="([^"]+)"', images.text).group(1)
    client.post(url, {'note': "This is an alt text"})

    album = albums.click("Comicon 2016")
    assert "This is an alt text" in album
