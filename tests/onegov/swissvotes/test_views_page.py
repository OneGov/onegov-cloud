from __future__ import annotations

import pytest

from onegov.swissvotes.models import TranslatablePage
from transaction import commit
from webtest import TestApp as Client
from webtest.forms import Upload


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.swissvotes.models import TranslatablePageFile
    from .conftest import TestApp



def test_view_page(swissvotes_app: TestApp) -> None:
    client = Client(swissvotes_app)

    home = client.get('/').maybe_follow()
    home.click('imprint')
    home.click('disclaimer')
    home.click('data-protection')

    login = client.get('/auth/login')
    login.form['username'] = 'admin@example.org'
    login.form['password'] = 'hunter2'
    login.form.submit()

    client.get('/locale/en_US').follow()
    add = client.get('/').maybe_follow().click(href='add')
    add.form['title'] = "About"
    add.form['content'] = "About the project"
    add.form.submit()

    for locale, title, content in (
        ('de_CH', "Über das Projekt", "Platzhalterttext"),
        ('fr_CH', "À propos du projet", "Texte de remplacement"),
        ('en_US', "About the project", "Placeholder text"),
    ):
        client.get(f'/locale/{locale}').follow()
        page = client.get('/page/about/edit')
        page.form['title'] = title
        page.form['content'] = content
        page.form.submit()

    for locale, title, content in (
        ('de_CH', "Über das Projekt", "Platzhalterttext"),
        ('fr_CH', "À propos du projet", "Texte de remplacement"),
        ('en_US', "About the project", "Placeholder text")
    ):
        client.get(f'/locale/{locale}').follow()
        page = client.get('/page/about')
        assert title in page
        assert content in page

    client.get('/locale/de_CH').follow()
    client.get('/page/about').click("Seite löschen").form.submit()
    client.get('/page/about', status=404)


def test_view_page_attachments(
    swissvotes_app: TestApp,
    page_attachments: dict[str, dict[str, TranslatablePageFile]]
) -> None:

    client = Client(swissvotes_app)

    login = client.get('/auth/login')
    login.form['username'] = 'admin@example.org'
    login.form['password'] = 'hunter2'
    login.form.submit()

    client.get('/locale/en_US').follow()
    add = client.get('/').maybe_follow().click(href='add')
    add.form['title'] = "About"
    add.form['content'] = "About the project"
    add.form.submit()

    manage = client.get('/page/about').click("Manage attachments")
    assert "No attachments." in manage

    # Upload two attachment (en_US, de_CH)
    manage.form['file'] = [Upload(
        '1.pdf',
        page_attachments['en_US']['CODEBOOK'].reference.file.read(),
        'application/pdf'
    )]
    manage = manage.form.submit().maybe_follow()
    assert manage.status_code == 200

    manage = client.get('/page/about').click("Manage attachments")
    assert "1.pdf" in manage
    assert manage.click('1.pdf').content_type == 'application/pdf'

    client.get('/locale/de_CH').follow()
    manage = client.get('/page/about').click("Anhänge verwalten")

    manage.form['file'] = [Upload(
        '2.pdf',
        page_attachments['de_CH']['CODEBOOK'].reference.file.read(),
        'application/pdf'
    )]
    manage = manage.form.submit().maybe_follow()
    assert manage.status_code == 200

    manage = client.get('/page/about').click("Anhänge verwalten")
    assert "1.pdf" not in manage
    assert "2.pdf" in manage
    assert manage.click('2.pdf').content_type == 'application/pdf'

    # Check visibility
    view = client.get('/page/about')
    assert "1.pdf" not in view
    assert "2.pdf" in view

    client.get('/locale/en_US').follow()
    view = client.get('/page/about')
    assert "1.pdf" in view
    assert "2.pdf" not in view

    # Delete attachments
    client.get('/page/about').click("Manage attachments")\
        .click("Delete").form.submit()

    client.get('/locale/de_CH').follow()
    client.get('/page/about').click("Anhänge verwalten")\
        .click("Löschen").form.submit()

    view = client.get('/page/about')
    assert "1.pdf" not in view
    assert "2.pdf" not in view


@pytest.mark.parametrize('locale', ('de_CH', 'fr_CH', 'en_US'))
def test_view_page_static_attachment_links(
    swissvotes_app: TestApp,
    page_attachments: dict[str, dict[str, TranslatablePageFile]],
    page_attachment_urls: dict[str, dict[str, str]],
    locale: str
) -> None:

    client = Client(swissvotes_app)
    url = client.get('/').maybe_follow().click('imprint').request.url

    # No attachments yet
    for name in page_attachment_urls[locale].values():
        view = client.get(f'{url}/{name}', status=404)
        assert view.status_code == 404

    session = swissvotes_app.session()
    page = session.query(TranslatablePage).filter_by(title='imprint').one()
    page.files = list(page_attachments[locale].values())
    commit()

    for name in page_attachment_urls[locale].values():
        view = client.get(f'{url}/{name}')
        assert view.status_code in (200, 301, 302)


def test_view_page_slider_images(
    swissvotes_app: TestApp,
    slider_images: dict[str, TranslatablePageFile]
) -> None:

    client = Client(swissvotes_app)

    login = client.get('/auth/login')
    login.form['username'] = 'admin@example.org'
    login.form['password'] = 'hunter2'
    login.form.submit()

    client.get('/locale/en_US').follow()
    add = client.get('/').maybe_follow().click(href='add')
    add.form['title'] = 'About'
    add.form['content'] = 'About the project'
    add.form.submit()

    manage = client.get('/page/about').click('Manage slider images')
    assert 'No attachments.' in manage

    # Upload image
    manage.form['file'] = [Upload(
        '2.1-x.png',
        slider_images['2.1-x'].reference.file.read(),
        'image/png'
    )]
    assert manage.form.submit().maybe_follow().status_code == 200

    manage = client.get('/page/about').click('Manage slider images')
    assert '2.1-x.png' in manage
    assert manage.click('2.1-x.png').content_type == 'image/png'

    # Check visibility
    view = client.get('/page/about')
    assert 'data-orbit' in view
    assert '2.1-x.png' in view

    client.get('/locale/de_CH').follow()
    view = client.get('/page/about')
    assert 'data-orbit' in view
    assert '2.1-x.png' in view

    # Delete attachments
    client.get('/locale/de_CH').follow()
    client.get('/page/about').click('Slider-Bilder verwalten')\
        .click('Löschen').form.submit()

    view = client.get('/page/about')
    assert 'data-orbit' not in view
    assert '2.1-x.png' not in view
