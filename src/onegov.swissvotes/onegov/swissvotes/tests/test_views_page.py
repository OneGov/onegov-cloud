from onegov.core.utils import module_path
from pytest import mark
from webtest import TestApp as Client
from webtest.forms import Upload


def test_view_page(swissvotes_app):
    client = Client(swissvotes_app)

    home = client.get('/').maybe_follow()
    home.click('imprint')
    home.click('disclaimer')
    home.click('data-protection')

    login = client.get('/auth/login')
    login.form['username'] = 'admin@example.org'
    login.form['password'] = 'hunter2'
    login.form.submit()

    client.get(f'/locale/en_US').follow()
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

    client.get(f'/locale/de_CH').follow()
    client.get('/page/about').click("Seite löschen").form.submit()
    client.get('/page/about', status=404)


@mark.parametrize("pdf_1, pdf_2", [(
    module_path('onegov.swissvotes', 'tests/fixtures/example_1.pdf'),
    module_path('onegov.swissvotes', 'tests/fixtures/example_2.pdf')
)])
def test_view_page_attachments(swissvotes_app, temporary_path, pdf_1, pdf_2):

    client = Client(swissvotes_app)

    login = client.get('/auth/login')
    login.form['username'] = 'admin@example.org'
    login.form['password'] = 'hunter2'
    login.form.submit()

    client.get(f'/locale/en_US').follow()
    add = client.get('/').maybe_follow().click(href='add')
    add.form['title'] = "About"
    add.form['content'] = "About the project"
    add.form.submit()

    manage = client.get('/page/about').click("Manage attachments")
    assert "No attachments." in manage

    # Try to upload an invalid file
    manage.form['file'] = Upload(
        'fake.pdf', 'PDF'.encode('utf-8'), 'application/pdf'
    )
    manage.form.submit(status=415)

    # Upload two attachment (en_US, de_CH)
    with open(pdf_1, 'rb') as file:
        content_1 = file.read()
    manage.form['file'] = Upload('1.pdf', content_1, 'application/pdf')
    manage = manage.form.submit().maybe_follow()
    assert "Attachment added" in manage
    assert "1.pdf" in manage
    assert manage.click('1.pdf').content_type == 'application/pdf'

    client.get(f'/locale/de_CH').follow()
    manage = client.get('/page/about').click("Anhänge verwalten")

    with open(pdf_2, 'rb') as file:
        content_2 = file.read()
    manage.form['file'] = Upload('2.pdf', content_2, 'application/pdf')
    manage = manage.form.submit().maybe_follow()
    assert "Anhang hinzugefügt" in manage
    assert "1.pdf" not in manage
    assert "2.pdf" in manage
    assert manage.click('2.pdf').content_type == 'application/pdf'

    # Check visibility
    view = client.get('/page/about')
    assert "1.pdf" not in view
    assert "2.pdf" in view

    client.get(f'/locale/en_US').follow()
    view = client.get('/page/about')
    assert "1.pdf" in view
    assert "2.pdf" not in view

    # Delete attachments
    client.get('/page/about').click("Manage attachments")\
        .click("Delete").form.submit()

    client.get(f'/locale/de_CH').follow()
    client.get('/page/about').click("Anhänge verwalten")\
        .click("Löschen").form.submit()

    view = client.get('/page/about')
    assert "1.pdf" not in view
    assert "2.pdf" not in view
