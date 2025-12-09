from __future__ import annotations

import os
import pytest
import re

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tests.shared.client import ExtendedResponse
    from .conftest import Client


def test_directory_prev_next(client: Client) -> None:
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


def test_newline_in_directory_header(client: Client) -> None:
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


def test_change_directory_url(client: Client) -> None:
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


def test_directory_entry_subscription(client: Client) -> None:
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
    confirm = re.search(r'Anmeldung bestätigen\]\(([^\)]+)', message).group(1)  # type: ignore[union-attr]
    message_2 = client.get_email(1)['TextBody']
    confirm_2 = re.search(  # type: ignore[union-attr]
        r'Anmeldung bestätigen\]\(([^\)]+)', message_2).group(1)
    message_3 = client.get_email(2)['TextBody']
    confirm_3 = re.search(  # type: ignore[union-attr]
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

    unsubscribe = re.search(r'abzumelden.\]\(([^\)]+)', message).group(1)  # type: ignore[union-attr]
    page = client.get(unsubscribe).follow().follow()
    assert "wurde erfolgreich abgemeldet" in page


@pytest.mark.parametrize(
    'index,content_labels,hide_labels', [
    ('A', 'Question\nAnswer', ''),
    ('B', 'Question\nAnswer', 'Question'),
    ('C', 'Question\nAnswer', 'Answer'),
    ('D', 'Question\nAnswer', 'Question\nAnswer'),
])
def test_create_directory_accordion_layout(
    index,
    content_labels,
    hide_labels,
    client: Client
) -> None:
    question_label = '<strong>Question</strong>:'
    answer_label = '<strong>Answer</strong>:'

    print('*** tschupre index:', index)
    print('*** tschupre content_labels:', content_labels)
    print('*** tschupre hide_labels:', hide_labels)

    def create_directory(
        client: Client,
        title: str,
        hide_labels: str
    ) -> ExtendedResponse:
        page = (client.get('/directories').click('Verzeichnis'))
        page.form['title'] = title + f' {index}'
        page.form['structure'] = "Question *= ___\nAnswer *= ___"
        page.form['title_format'] = '[Question]'
        page.form['layout'] = 'accordion'
        page.form['content_fields'] = content_labels
        page.form['content_hide_labels'] = hide_labels
        return page.form.submit().follow()

    client.login_admin()
    title = "Questions and Answers about smurfs"

    faq_dir = create_directory(client, title, hide_labels)
    assert title in faq_dir

    question = "Are smurfs real?"
    answer = "Yes, they are."
    q1 = faq_dir.click('Eintrag')
    q1.form['question'] = question
    q1.form['answer'] = answer
    q1.form.submit().follow()

    page = client.get(
        f'/directories/questions-and-answers-about-smurfs-{index.lower()}')
    # for ul in page.pyquery('ul'):
    #     for li in ul.findall('li'):
    #         print('*** tschupre li text:', li.text)
    assert question in page
    assert answer in page
    if 'Question' in hide_labels:
        assert question_label not in page
    else:
        assert question_label in page
    if 'Answer' in hide_labels:
        assert answer_label not in page
    else:
        assert answer_label in page

    question = "Who is the boss of the smurfs?"
    q2 = faq_dir.click('Eintrag')
    q2.form['question'] = question
    q2.form['answer'] = 'Papa Schlumpf'
    q2.form.submit().follow()
    page = client.get(
        f'/directories/questions-and-answers-about-smurfs-{index.lower()}')
    assert question in page
    assert answer in page
    if 'Question' in hide_labels:
        assert question_label not in page
    else:
        assert question_label in page
    if 'Answer' in hide_labels:
        assert answer_label not in page
    else:
        assert answer_label in page
