from webtest import TestApp as Client


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
