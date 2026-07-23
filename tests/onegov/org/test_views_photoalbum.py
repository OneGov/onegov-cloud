from __future__ import annotations

import re
import transaction

from markupsafe import Markup
from onegov.core.html import sanitize_html
from onegov.org.layout import Layout
from onegov.org.models import ImageFileCollection, ImageSetCollection
from onegov.page import PageCollection

from tests.shared.utils import create_image
from webtest import Upload

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .conftest import Client


def test_photoalbum_json(client: Client) -> None:
    response = client.get('/photoalbums/json', expect_errors=True)
    assert response.status_code == 403

    client.login_editor()

    transaction.begin()
    albums = ImageSetCollection(client.app.session())
    zulu = albums.add(title='Zulu Album')
    alpha = albums.add(title='Alpha Album')
    zulu_id = zulu.id
    alpha_id = alpha.id
    transaction.commit()

    assert client.get('/photoalbums/json').json == [
        {
            'name': 'Alpha Album',
            'url': f'http://localhost/photoalbum/{alpha_id}',
        },
        {
            'name': 'Zulu Album',
            'url': f'http://localhost/photoalbum/{zulu_id}',
        },
    ]


def test_photoalbum_rich_text_block(client: Client) -> None:
    client.login_editor()

    transaction.begin()
    album = ImageSetCollection(client.app.session()).add(title='Sommerfest')
    image = ImageFileCollection(client.app.session()).add(
        'sommerfest.png',
        create_image().read(),
        note='Sommerfest Bild',
    )
    album.files = [image]
    album_id = album.id
    private_album = ImageSetCollection(client.app.session()).add(
        title='Internes Album',
        meta={'access': 'private'},
    )
    private_album_id = private_album.id
    marker = sanitize_html(
        '<p>Vor dem Album</p>'
        '<p class="has-hashtag onegov-photoalbum-block">'
        f'<a href="/photoalbum/{album_id}">Sommerfest</a>'
        '</p>'
        '<p class="onegov-photoalbum-block">'
        f'<a href="/photoalbum/{private_album_id}">Internes Album</a>'
        '</p>'
        '<p class="onegov-photoalbum-block-extra">'
        f'<a href="/photoalbum/{album_id}">Nur ein ähnlicher Klassenname</a>'
        '</p>'
        '<p>Nach dem Album</p>'
    )
    assert 'onegov-photoalbum-block' in marker

    pages = PageCollection(client.app.session())
    parent = pages.by_path('organisation')
    assert parent is not None
    pages.add(
        parent=parent,
        title='Album im Text',
        name='album-im-text',
        type='topic',
        content={'text': marker},
        meta={'trait': 'page', 'access': 'public'},
    )
    pages.add(
        parent=parent,
        title='Nur privates Album',
        name='nur-privates-album',
        type='topic',
        content={
            'text': sanitize_html(
                '<p class="onegov-photoalbum-block">'
                f'<a href="/photoalbum/{private_album_id}">Internes Album</a>'
                '</p>'
            )
        },
        meta={'trait': 'page', 'access': 'public'},
    )
    transaction.commit()

    page = client.get('/topics/organisation/album-im-text')

    before = page.text.index('Vor dem Album')
    gallery = page.text.index('Sommerfest Bild')
    after = page.text.index('Nach dem Album')
    assert before < gallery < after
    assert page.pyquery(
        '.grid-imageset.photoswipe img[alt="Sommerfest Bild"]'
    )

    public_page = client.spawn().get('/topics/organisation/album-im-text')
    assert 'Sommerfest Bild' in public_page
    assert 'Nur ein ähnlicher Klassenname' in public_page
    assert 'Internes Album' not in public_page
    assert private_album_id not in public_page

    private_only = client.spawn().get(
        '/topics/organisation/nur-privates-album'
    )
    assert 'Internes Album' not in private_only
    assert private_album_id not in private_only


def test_photoalbum_plain_text_is_escaped() -> None:
    layout = Layout.__new__(Layout)
    blocks = layout.photo_album_blocks(
        '<script>alert(1)</script>'
        '<p class="onegov-photoalbum-block">Album</p>'
    )

    assert blocks == [(
        '&lt;script&gt;alert(1)&lt;/script&gt;'
        '&lt;p class=&#34;onegov-photoalbum-block&#34;&gt;Album&lt;/p&gt;',
        None,
    )]


def test_photoalbum_rich_text_details_start_closed() -> None:
    layout = Layout.__new__(Layout)
    blocks = layout.photo_album_blocks(Markup(
        '<details class="faq" data-kind="question" open="open">'
        '<summary>Question</summary>'
        '<p>Answer</p></details>'
    ))

    assert blocks == [(
        '<details class="faq" data-kind="question">'
        '<summary>Question</summary><p>Answer</p></details>',
        None,
    )]


def test_manage_album(client: Client) -> None:
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
    images.form['file'] = [Upload('test.jpg', create_image().read())]
    images.form.submit()

    select = album.click("Bilder auswählen")
    select.form[tuple(select.form.fields.keys())[1]] = True
    select.form.submit()

    album = albums.click("Comicon 2016")
    assert "noch keine Bilder" not in album

    images = albums.click("Bilder verwalten")

    url = re.search(r'data-note-update-url="([^"]+)"', images.text).group(1)  # type: ignore[union-attr]
    client.post(url, {'note': "This is an alt text"})

    album = albums.click("Comicon 2016")
    assert "This is an alt text" in album

    # switch to grid mode
    settings = album.click("Bearbeiten")
    settings.form['view'] = 'grid'
    settings.form.submit()

    album = albums.click("Comicon 2016")
    assert "This is an alt text" in album


def test_image_selection(client: Client) -> None:
    client.login_admin()

    number_of_images = 3

    albums = client.get('/photoalbums')
    new = albums.click('Fotoalbum')
    new.form['title'] = 'Vacation Destinations 2026'
    new.form.submit()

    album = client.get('/photoalbums').click('Vacation Destinations 2026')
    for idx in range(number_of_images):
        select = albums.click("Bilder verwalten")
        select.form['file'] = [
            Upload(f'image_{idx}.jpg', create_image().read())]
        select.form.submit()

    # select all images
    select = album.click('Bilder auswählen')
    select.form[tuple(select.form.fields.keys())[1]] = True
    select.form[tuple(select.form.fields.keys())[2]] = True
    select.form[tuple(select.form.fields.keys())[3]] = True
    select.form.submit()

    collection = ImageFileCollection(client.app.session()).query()
    assert collection.count() == number_of_images
    images = {(img.id, img.name) for img in collection.all()}
    album = client.get('/photoalbums').click('Vacation Destinations 2026')
    for img in images:
        assert img[0] in album, '{} not found in album'.format(img)

    # switch to grid mode
    settings = album.click('Bearbeiten')
    settings.form['view'] = 'grid'
    settings.form.submit()

    album = client.get('/photoalbums').click('Vacation Destinations 2026')
    for img in images:
        assert img[0] in album, '{} not found in album'.format(img)
