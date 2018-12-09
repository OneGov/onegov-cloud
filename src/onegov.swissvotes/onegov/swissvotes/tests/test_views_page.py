from webtest import TestApp as Client


def test_view_page(swissvotes_app):
    client = Client(swissvotes_app)

    for locale, text in (
        ('de_CH', "Über uns"),
        ('fr_CH', "À propos de nous"),
        ('en_US', "About")
    ):
        client.get(f'/locale/{locale}').follow()
        assert text in client.get('/page/about')

    login = client.get('/auth/login')
    login.form['username'] = 'admin@example.org'
    login.form['password'] = 'hunter2'
    login.form.submit()

    for locale, title, content in (
        ('de_CH', "Über das Projekt", "Platzhalterttext"),
        ('fr_CH', "À propos du projet", "Texte de remplacement"),
        ('en_US', "About the project", "Placeholder text")
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
