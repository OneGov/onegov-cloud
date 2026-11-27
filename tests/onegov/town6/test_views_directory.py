import os
import pytest
import re
import transaction
from textwrap import dedent
from unittest.mock import patch, PropertyMock
from onegov.directory import DirectoryCollection, DirectoryConfiguration
from onegov.org.request import OrgRequest

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from onegov.org.models import ExtendedDirectory
    from tests.shared.client import ExtendedResponse
    from .conftest import Client


def test_directory_prev_next_all(client: Client) -> None:
    client.login_admin()

    page = client.get('/directories').click('^Verzeichnis$')
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

    # Each entry links back to the full directory listing
    assert 'Alle Einträge' in emily_page
    all_entries = emily_page.pyquery(
        '.more-entries .fa-chevron-up'
    ).closest('a')
    assert all_entries
    assert '/directories/trainers?' in all_entries.attr('href')

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
    page = page.click('^Verzeichnis$')
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

    page = client.get('/directories').click('^Verzeichnis$')
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
    page = client.get('/directories').click('^Verzeichnis$')
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

    page = client.get('/directories').click('^Verzeichnis$')
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
    ('A1', '', ''),
    ('A2', 'Question', ''),
    ('A3', 'Answer', ''),
    ('A4', 'Question\nAnswer', ''),

    ('B1', '', 'Question'),
    ('B2', 'Question', 'Question'),
    ('B3', 'Answer', 'Question'),
    ('B4', 'Question\nAnswer', 'Question'),

    ('C1', '', 'Answer'),
    ('C2', 'Question', 'Answer'),
    ('C3', 'Answer', 'Answer'),
    ('C4', 'Question\nAnswer', 'Answer'),

    ('D1', '', 'Question\nAnswer'),
    ('D2', 'Question', 'Question\nAnswer'),
    ('D3', 'Answer', 'Question\nAnswer'),
    ('D4', 'Question\nAnswer', 'Question\nAnswer'),
])
def test_create_directory_accordion_layout(
    index: str,
    content_labels: str,
    hide_labels: str,
    client: Client
) -> None:
    question_label = '<strong>Question</strong>:'
    answer_label = '<strong>Answer</strong>:'

    def create_directory(
        client: Client,
        title: str,
        hide_labels: str
    ) -> ExtendedResponse:
        page = (client.get('/directories').click('^Verzeichnis$'))
        page.form['title'] = title + f' {index}'
        page.form['structure'] = "Question *= ___\nAnswer *= ___"
        page.form['title_format'] = '[Question]'
        page.form['layout'] = 'accordion'
        page.form['content_fields'] = content_labels
        page.form['content_hide_labels'] = hide_labels
        return page.form.submit().follow()

    def test_labels() -> None:
        assert question in page  # question always appears as accordion title
        if 'Question' in content_labels:
            assert page.text.count(question) == 2
            if 'Question' in hide_labels:
                assert question_label not in page
                assert f'{question}' in page
            else:
                assert question_label in page
                # string field renders inline: label, then value, no <br>
                assert f'{question_label} {question}' in page
        else:
            assert page.text.count(question) == 1
            assert question_label not in page
            assert f'{question}' in page

        if 'Answer' in content_labels:
            assert answer in page
            if 'Answer' in hide_labels:
                assert answer_label not in page
                assert f'{answer_label} {answer}' not in page
            else:
                assert answer_label in page
                assert f'{answer_label} {answer}' in page
        else:
            assert answer not in page
            assert answer_label not in page

        # test edit link
        assert page.pyquery('.accordion .edit-link').attr('href')

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
    test_labels()

    question = "Who is the boss of the smurfs?"
    q2 = faq_dir.click('Eintrag')
    q2.form['question'] = question
    q2.form['answer'] = 'Papa Schlumpf'
    q2.form.submit().follow()
    page = client.get(
        f'/directories/questions-and-answers-about-smurfs-{index.lower()}')
    test_labels()


def test_accordion_layout_renders_field_types(client: Client) -> None:
    # radio/checkbox/textarea in accordion mode must render via
    # form.render_display (checkmarks, line breaks), not raw values
    client.login_admin()

    page = client.get('/directories').click('^Verzeichnis$')
    page.form['title'] = 'Recycling'
    page.form['structure'] = dedent("""
        Name *= ___
        Kosten *=
            (x) kostenlos
            ( ) kostenpflichtig
        Abgabestelle *=
            [ ] Ökihof
            [ ] Landfill
            [ ] Verbrennungsanlage
        Details = ...
    """)
    page.form['title_format'] = '[Name]'
    page.form['layout'] = 'accordion'
    page.form['content_fields'] = 'Name\nKosten\nAbgabestelle\nDetails'
    page.form.submit().follow()

    entry = client.get('/directories/recycling').click('Eintrag')
    entry.form['name'] = 'Aluminium'
    entry.form['kosten'] = 'kostenlos'
    entry.form['abgabestelle'] = ['Ökihof', 'Landfill']
    entry.form['details'] = 'Besuch https://example.org\nTelefon 041 499 66 88'
    entry.form.submit().follow()

    page = client.get('/directories/recycling')

    # radio: checkmark, label on its own line
    assert '<strong>Kosten</strong>: <br>✓ kostenlos' in page

    # checkbox: each selected value on its own line with a checkmark
    assert '<strong>Abgabestelle</strong>: <br>✓ Ökihof<br>✓ Landfill' in page

    # textarea: newlines become <br>, raw list/value never leaks
    assert '<strong>Details</strong>: <br>Besuch ' in page

    # links: urls, phone numbers and emails in free text get linkified
    assert '<a href="https://example.org" rel="nofollow">' in page
    assert '<a href="tel:+41414996688">041 499 66 88</a>' in page


def test_directory_entry_hash_shown_without_change_requests(
    client: Client
) -> None:
    client.login_admin()

    page = client.get('/directories').click('^Verzeichnis$')
    page.form['title'] = 'Clubs'
    page.form['structure'] = 'Name *= ___'
    page.form['title_format'] = '[Name]'
    page.form['enable_change_requests'] = False
    page = page.form.submit().follow()

    page = page.click('Eintrag', index=0)
    page.form['name'] = 'Chess Club'
    page = page.form.submit().follow()

    entry_url = '/directories/clubs/chess-club'

    # admin sees the hash panel
    page = client.get(entry_url)
    assert page.pyquery('.directory-entry-hash')

    # anonymous user does not see the hash (manager-only)
    anon = client.spawn()
    page = anon.get(entry_url)
    assert not page.pyquery('.directory-entry-hash')

    # mTAN-authenticated user sees the hash
    with patch.object(
        OrgRequest, 'active_mtan_session', new_callable=PropertyMock,
        return_value=True
    ):
        page = anon.get(entry_url)
        assert page.pyquery('.directory-entry-hash')


def test_directory_search_widget(client_with_fts: Client) -> None:
    client = client_with_fts
    client.login_admin()

    def create_directory(title: str, enable_search: bool) -> None:
        page = client.get('/directories').click('^Verzeichnis$')
        page.form['title'] = title
        page.form['structure'] = 'Name *= ___'
        page.form['title_format'] = '[Name]'
        page.form['enable_search'] = enable_search
        page = page.form.submit().follow()
        page = page.click('Eintrag', index=0)
        page.form['name'] = f'Pilatus {title}'
        page.form.submit().follow()

    create_directory('Clubs', enable_search=True)
    create_directory('Bars', enable_search=False)

    assert client.get('/directories/clubs').pyquery('#inline-search')
    assert not client.get('/directories/bars').pyquery('#inline-search')

    # the box stays hidden even when search is forced into the url
    assert not client.get(
        '/directories/bars?search=inline').pyquery('#inline-search')

    # ...and a forced search does not filter a disabled directory
    assert 'Pilatus Bars' in client.get(
        '/directories/bars?search=inline'
        '&search_query={"term"%3A"zzz"}')

    # results are limited to the searched directory
    page = client.get(
        '/directories/clubs?search=inline&search_query={"term"%3A"Pilatus"}')
    assert 'Pilatus Clubs' in page
    assert 'Pilatus Bars' not in page


def test_directory_search_preserves_filter(client_with_fts: Client) -> None:
    client = client_with_fts

    session = client.app.session()
    directories: DirectoryCollection[ExtendedDirectory]
    directories = DirectoryCollection(session, type='extended')
    directory = directories.add(
        title='Clubs',
        structure=dedent("""
            Name *= ___
            Choice =
                (x) yes
                ( ) no
        """),
        configuration=DirectoryConfiguration(
            title='[Name]', order=['Name'], searchable=['Name'],
            keywords=['Choice']),
    )
    directory.enable_search = True
    directory.add(values={'name': 'Pilatus', 'choice': 'yes'})
    directory.add(values={'name': 'Rigi', 'choice': 'yes'})
    directory.add(values={'name': 'Napf', 'choice': 'no'})
    transaction.commit()

    client.login_admin()

    # an active category filter is preserved as a hidden field, so submitting
    # a search keeps the filter instead of dropping it
    searched = client.get(
        '/directories/clubs?keywords=choice:yes'
        '&search=inline&search_query={"term"%3A"Pilatus"}')
    assert searched.pyquery(
        '#inline-search input[name="keywords"]')[0].attrib['value'] \
        == 'choice:yes'
    assert 'Pilatus' in searched
    assert 'Rigi' not in searched  # excluded by the search term
    assert 'Napf' not in searched  # excluded by the category filter

    # the reset target (filter kept, search dropped) keeps the filter active
    reset = client.get('/directories/clubs?keywords=choice:yes')
    assert 'Pilatus' in reset
    assert 'Rigi' in reset  # search cleared
    assert 'Napf' not in reset  # filter kept
