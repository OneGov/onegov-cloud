import os
import re


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


def test_directory_entry_subscription(client):
    client.login_admin()

    assert len(os.listdir(client.app.maildir)) == 0

    page = client.get('/directories').click('Verzeichnis')
    page.form['title'] = "Trainers"
    page.form['structure'] = """
        Name *= ___
    """
    page.form['title_format'] = '[Name]'
    page.form['enable_update_notifications'] = True
    page = page.form.submit().follow()

    page = page.click('Benachrichtigungen bei neuen Einträgen erhalten')
    page.form['address'] = 'bliss@gmail.com'
    page = page.form.submit().follow()

    page = page.click('Benachrichtigungen bei neuen Einträgen erhalten')
    page.form['address'] = 'dream@gmail.com'
    page = page.form.submit().follow()

    page = page.click('Benachrichtigungen bei neuen Einträgen erhalten')
    page.form['address'] = 'brave@gmail.com'
    page.form.submit().follow()

    assert len(os.listdir(client.app.maildir)) == 3
    message = client.get_email(0)['TextBody']
    confirm = re.search(r'Anmeldung bestätigen\]\(([^\)]+)', message).group(1)
    message_2 = client.get_email(1)['TextBody']
    confirm_2 = re.search(
        r'Anmeldung bestätigen\]\(([^\)]+)', message_2).group(1)
    message_3 = client.get_email(2)['TextBody']
    confirm_3 = re.search(
        r'Anmeldung bestätigen\]\(([^\)]+)', message_3).group(1)

    illegal_confirm = confirm.split('/confirm')[0] + 'x/confirm'
    assert "falsches Token" in client.get(illegal_confirm).follow().follow()

    page = client.get(confirm).follow().follow()
    page = client.get(confirm).follow().follow()
    assert "bliss@gmail.com wurde erfolgreich" in page

    page = client.get(confirm_2).follow().follow()
    assert "dream@gmail.com wurde erfolgreich" in page

    page = client.get(confirm_3).follow().follow()
    assert "brave@gmail.com wurde erfolgreich" in page

    page = client.get('/directories/trainers/+recipients')
    assert 'Zur Zeit sind 3 Abonnenten registriert' in page
    assert 'bliss@gmail.com' in page
    assert 'dream@gmail.com' in page
    assert 'brave@gmail.com' in page

    page = client.get('/directories/trainers').click("^Eintrag$")
    page.form['name'] = 'Emily Larlham'
    page.form.submit()

    assert len(os.listdir(client.app.maildir)) == 4
    message = client.get_email(3)['TextBody']
    assert 'Emily Larlham' in message

    unsubscribe = re.search(r'abzumelden.\]\(([^\)]+)', message).group(1)
    page = client.get(unsubscribe).follow().follow()
    assert "wurde erfolgreich abgemeldet" in page


def test_create_directory_accordion_layout(client):

    def create_directory(client, title, structure):
        page = (client.get('/directories').click('Verzeichnis'))
        page.form['title'] = title
        page.form['structure'] = structure
        page.form['title_format'] = '[Question]'
        page.form['content_fields'] = 'Question\nAnswer'
        page.form['layout'] = 'accordion'
        return page.form.submit().follow()

    def edit_directory(client, dir_url_name, structure):
        page = client.get(f'/directories/{dir_url_name}')
        page = page.click('Konfigurieren')
        page.form['structure'] = structure
        return page.form.submit().form.submit().follow()

    def create_directory_entry(directory, question, answer):
        page = directory.click('Eintrag')
        page.form['question'] = question
        page.form['answer'] = answer
        return page.form.submit().follow()

    client.login_admin()

    title = "Questions and Answers about smurfs"
    structure = "Question *= ___\nAnswer *= ___"
    faq_dir = create_directory(client, title, structure)
    assert title in faq_dir

    question_1 = "Are smurfs real?"
    answer_1 = "Yes, they are."
    page = create_directory_entry(faq_dir, question_1, answer_1)
    assert question_1 in page
    assert answer_1 in page

    question_2 = "Who is the boss of the smurfs?"
    answer_2 = "Papa Smurf"
    page = create_directory_entry(faq_dir, question_2, answer_2)
    assert question_2 in page
    assert answer_2 in page

    question_3 = "How many smurfs are there?"
    answer_3 = '- Papa Smurf\n- Smurfette\n- Brainy Smurf\n- Grouchy Smurf'
    q3 = create_directory_entry(faq_dir, question_3, answer_3)
    assert question_3 in q3
    for smurf in answer_3.split('\n'):
        assert smurf in q3

    page = client.get('/directories/questions-and-answers-about-smurfs')
    assert question_1 in page
    assert answer_1 in page
    assert question_2 in page
    assert answer_2 in page
    assert question_3 in page
    for smurf in answer_3.split('\n'):
        assert smurf in page

    # with multiline answers
    structure = "Question *= ___\nAnswer *= ...[10]"
    page = edit_directory(
        client, 'questions-and-answers-about-smurfs', structure)
    assert question_1 in page
    assert answer_1 in page
    assert question_2 in page
    assert answer_2 in page
    assert question_3 in page
    for smurf in answer_3.split('\n'):
        assert smurf in page

    # with markdown answers
    structure = "Question *= ___\nAnswer *= <markdown>"
    page = edit_directory(
        client, 'questions-and-answers-about-smurfs', structure)
    assert question_1 in page
    assert answer_1 in page
    assert question_2 in page
    assert answer_2 in page
    assert question_3 in page
    for smurf in answer_3.replace('- ', '').split('\n'):
        assert smurf in page
        # ensure markdown rendered each smurf in separate li tag
        assert f'<li>{smurf}</li>' in page
