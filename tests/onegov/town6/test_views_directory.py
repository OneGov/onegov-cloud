

def test_directory_prev_next(client):
    client.login_admin()

    page = client.get('/directories').click('Verzeichnis')
    page.form['title'] = "Trainers"
    page.form['structure'] = """
        Name *= ___
    """
    page.form['title_format'] = '[Name]'
    page.form.submit()

    page = client.get('/directories/trainers').click("^Eintrag$")
    page.form['name'] = 'Emily Larlham'
    page.form.submit()

    page = client.get('/directories/trainers').click("^Eintrag$")
    page.form['name'] = 'Susan Light'
    page.form['access'] = 'private'
    page.form.submit()

    page = client.get('/directories/trainers').click("^Eintrag$")
    page.form['name'] = 'Zak George'
    page.form.submit()

    # Admins see all entries
    emily_page = client.get('/directories/trainers/emily-larlham')
    susan_page = client.get('/directories/trainers/susan-light')
    zak_page = client.get('/directories/trainers/zak-george')

    assert 'Susan Light' in emily_page
    assert 'Zak George' not in emily_page

    assert 'Emily Larlham' in susan_page
    assert 'Zak George' in susan_page

    assert 'Emily Larlham' not in zak_page
    assert 'Susan Light' in zak_page

    # Anonymous users only see public entries
    client = client.spawn()
    emily_page = client.get('/directories/trainers/emily-larlham')
    zak_page = client.get('/directories/trainers/zak-george')

    assert 'Susan Light' not in emily_page
    assert 'Zak George' in emily_page

    assert 'Emily Larlham' in zak_page
    assert 'Susan Light' not in zak_page


def test_newline_in_directory_header(client):

    client.login_admin()
    page = client.get('/directories')
    page = page.click('Verzeichnis')
    page.form['title'] = "Clubs"
    page.form['lead'] = 'this is a multiline\nlead'
    page.form['structure'] = """
        Name *= ___
    """
    page.form['title_format'] = '[Name]'
    page.form.submit()

    page = client.get('/directories/clubs')
    page = page.click('Eintrag', index=0)
    page.form['name'] = 'Soccer Club'
    page.form.submit()

    page = client.get('/directories/clubs')
    assert "this is a multiline<br>lead" in page


def test_change_directory_url(client):
    client.login_admin()

    page = client.get('/directories').click('Verzeichnis')
    page.form['title'] = "Trainers"
    page.form['structure'] = """
        Name *= ___
    """
    page.form['title_format'] = '[Name]'
    page.form.submit()
    page = client.get('/directories/trainers/')

    change_dir_url = page.click('URL ändern')
    change_dir_url.form['name'] = 'sr'
    sr = change_dir_url.form.submit().follow()

    assert sr.request.url.endswith('/sr')

    # now attempt to change url to a directory url which already exists
    page = client.get('/directories').click('Verzeichnis')
    page.form['title'] = "Clubs"
    page.form['structure'] = """
        Name *= ___
    """
    page.form['title_format'] = '[Name]'
    page.form.submit()

    page = client.get('/directories/clubs/')
    change_dir_url = page.click('URL ändern')
    change_dir_url.form['name'] = 'clubs'

    page = change_dir_url.form.submit().maybe_follow()
    assert 'Das Formular enthält Fehler' in page


def test_create_directory_accordion_layout(client):

    def create_directory(client, title):
        page = (client.get('/directories').
                click('Verzeichnis'))
        page.form['title'] = title
        page.form['structure'] = "Question *= ___\nAnswer *= ___"
        page.form['title_format'] = '[Question]'
        page.form['layout'] = 'accordion'
        return page.form.submit().follow()

    client.login_admin()
    title = "Questions and Answers about smurfs"

    faq_dir = create_directory(client, title)
    assert title in faq_dir

    question = "Are smurfs real?"
    answer = "Yes, they are."
    q1 = faq_dir.click('Eintrag')
    q1.form['question'] = question
    q1.form['answer'] = answer
    q1 = q1.form.submit().follow()
    assert question in q1
    assert answer not in q1

    question = "Who is the boss of the smurfs?"
    q2 = faq_dir.click('Eintrag')
    q2.form['question'] = question
    q2.form['answer'] = 'Papa Schlumpf'
    q2 = q2.form.submit().follow()
    assert question in q2
    assert answer not in q2
