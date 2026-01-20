from __future__ import annotations

from tests.shared.utils import create_image, get_meta
from webtest import Upload


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .conftest import Client


def test_view_images(client: Client) -> None:
    assert client.get('/images', expect_errors=True).status_code == 403

    client.login_admin()

    images_page = client.get('/images')

    assert "Noch keine Bilder hochgeladen" in images_page

    images_page.form['file'] = [Upload('Test.txt', b'File content')]
    assert images_page.form.submit(expect_errors=True).status_code == 415

    images_page.form['file'] = [Upload('Test.jpg', create_image().read())]
    images_page.form.submit()

    images_page = client.get('/images')
    assert "Noch keine Bilder hochgeladen" not in images_page

    img_url = images_page.pyquery('.image-box a').attr('href')

    # Test Open Graph meta properties
    social_media = client.get('/social-media-settings')

    social_media.form['og_logo_default'] = img_url
    social_media.form.submit().follow()

    home = client.get('/')
    assert get_meta(home, 'og:image:alt') == 'Test.jpg'
    assert get_meta(home, 'og:image')
