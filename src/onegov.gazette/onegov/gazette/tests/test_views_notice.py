from freezegun import freeze_time
from io import BytesIO
from onegov.gazette.models import GazetteNotice
from onegov.gazette.tests.common import accept_notice
from onegov.gazette.tests.common import edit_notice
from onegov.gazette.tests.common import edit_notice_unrestricted
from onegov.gazette.tests.common import login_users
from onegov.gazette.tests.common import publish_issue
from onegov.gazette.tests.common import reject_notice
from onegov.gazette.tests.common import submit_notice
from PyPDF2 import PdfFileReader


def test_view_notice(gazette_app):
    # Check if the details of the notice is displayed correctly in the
    # display view (that is: organization, owner, group etc).

    admin, editor_1, editor_2, editor_3, publisher = login_users(gazette_app)

    with freeze_time("2017-11-01 11:00"):
        # create a notice for each editor
        for count, user in enumerate((editor_1, editor_2, editor_3)):
            manage = user.get('/notices/drafted/new-notice')
            manage.form['title'] = 'Titel {}'.format(count + 1)
            manage.form['organization'] = '200'
            manage.form['category'] = '11'
            manage.form['at_cost'].select('yes')
            manage.form['billing_address'] = 'someone\nstreet\r\nplace'
            manage.form['issues'] = ['2017-44', '2017-45']
            manage.form['text'] = "1. Oktober 2017"
            manage.form['author_place'] = 'Govikon'
            manage.form['author_name'] = 'State Chancellerist'
            manage.form['author_date'] = '2019-01-01'
            manage.form.submit()

        # check if the notices are displayed correctly
        for number, owner, group in (
            (1, 'First', True),
            (2, 'Second', True),
            (3, 'Third', False),
        ):
            for user in (editor_1, editor_2, editor_3, publisher):
                view = user.get(f'/notice/titel-{number}')
                assert f"Titel {number}" in view
                assert "1. Oktober 2017" in view
                assert "Govikon, 1. Januar 2019" in view
                assert "State Chancellerist" in view
                assert "Civic Community" in view
                assert "Education" in view
                assert "<dd>Ja</dd>" in view
                assert "someone<br>street<br>place" in view
                assert f"{owner} Editor" in view
                assert f"+4141511227{number}" in view
                assert f"<br>editor{number}@example.org" in view
                if group:
                    assert "TestGroup" in view
                else:
                    assert "TestGroup" not in view
                assert "Nr. 44, 03.11.2017" in view
                assert "Nr. 45, 10.11.2017" in view
                assert "in Arbeit" in view
                assert "erstellt" in view

        # Check if the publication numbers are displayed
        submit_notice(editor_1, 'titel-1')
        submit_notice(editor_2, 'titel-2')
        submit_notice(editor_3, 'titel-3')
        accept_notice(publisher, 'titel-1')
        accept_notice(publisher, 'titel-2')
        accept_notice(publisher, 'titel-3')
        publish_issue(publisher, '2017-44')
        publish_issue(publisher, '2017-45')

        for number in range(1, 4):
            for user in (editor_1, editor_2, editor_3, publisher):
                view = user.get('/notice/titel-{}'.format(number))
                assert "Nr. 44, 03.11.2017 / {}".format(number) in view
                assert "Nr. 45, 10.11.2017 / {}".format(number + 3) in view


def test_view_notice_actions(gazette_app):
    # Check if the actions are displayed correctly in the detail view

    admin, editor_1, editor_2, editor_3, publisher = login_users(gazette_app)

    with freeze_time("2017-11-01 11:00"):
        # create a notice for each editor
        for count, user in enumerate(
            (editor_1, editor_2, editor_3, publisher)
        ):
            manage = user.get('/notices/drafted/new-notice')
            manage.form['title'] = 'Titel {}'.format(count + 1)
            manage.form['organization'] = '200'
            manage.form['category'] = '11'
            manage.form['issues'] = ['2017-44']
            manage.form['text'] = "1. Oktober 2017"
            manage.form['author_place'] = 'Govikon'
            manage.form['author_name'] = 'State Chancellerist'
            manage.form['author_date'] = '2019-01-01'
            manage.form.submit()

        # check the actions
        actions = {
            'p': 'action-preview',
            't': 'action-attachments',
            'c': 'action-copy',
            'e': 'action-edit',
            'd': 'action-delete',
            's': 'action-submit',
            'a': 'action-accept',
            'r': 'action-reject'
        }

        def check(values):
            for user, slug, can in values:
                view = user.get('/notice/{}'.format(slug))
                cannot = [x for x in actions.keys() if x not in can]
                assert all((actions[action] in view for action in can))
                assert all((actions[action] not in view for action in cannot))

        # ... when drafted
        check((
            (admin, 'titel-1', 'pteds'),
            (admin, 'titel-2', 'pteds'),
            (admin, 'titel-3', 'pteds'),
            (admin, 'titel-4', 'pteds'),
            (publisher, 'titel-1', 'pteds'),
            (publisher, 'titel-2', 'pteds'),
            (publisher, 'titel-3', 'pteds'),
            (publisher, 'titel-4', 'pteds'),
            (editor_1, 'titel-1', 'peds'),
            (editor_1, 'titel-2', 'peds'),
            (editor_1, 'titel-3', 'p'),
            (editor_1, 'titel-4', 'p'),
            (editor_2, 'titel-1', 'peds'),
            (editor_2, 'titel-2', 'peds'),
            (editor_2, 'titel-3', 'p'),
            (editor_2, 'titel-4', 'p'),
            (editor_3, 'titel-1', 'p'),
            (editor_3, 'titel-2', 'p'),
            (editor_3, 'titel-3', 'peds'),
            (editor_3, 'titel-4', 'p'),
        ))

        # ... when submitted
        submit_notice(editor_1, 'titel-1')
        submit_notice(editor_2, 'titel-2')
        submit_notice(editor_3, 'titel-3')
        submit_notice(publisher, 'titel-4')

        check((
            (admin, 'titel-1', 'ptedar'),
            (admin, 'titel-2', 'ptedar'),
            (admin, 'titel-3', 'ptedar'),
            (admin, 'titel-4', 'ptedar'),
            (publisher, 'titel-1', 'ptear'),
            (publisher, 'titel-2', 'ptear'),
            (publisher, 'titel-3', 'ptear'),
            (publisher, 'titel-4', 'ptear'),
            (editor_1, 'titel-1', 'p'),
            (editor_1, 'titel-2', 'p'),
            (editor_1, 'titel-3', 'p'),
            (editor_1, 'titel-4', 'p'),
            (editor_2, 'titel-1', 'p'),
            (editor_2, 'titel-2', 'p'),
            (editor_2, 'titel-3', 'p'),
            (editor_2, 'titel-4', 'p'),
            (editor_3, 'titel-1', 'p'),
            (editor_3, 'titel-2', 'p'),
            (editor_3, 'titel-3', 'p'),
            (editor_3, 'titel-4', 'p'),
        ))

        # ... when rejected
        reject_notice(publisher, 'titel-1')
        reject_notice(publisher, 'titel-2')
        reject_notice(publisher, 'titel-3')
        reject_notice(publisher, 'titel-4')

        check((
            (admin, 'titel-1', 'pteds'),
            (admin, 'titel-2', 'pteds'),
            (admin, 'titel-3', 'pteds'),
            (admin, 'titel-4', 'pteds'),
            (publisher, 'titel-1', 'pteds'),
            (publisher, 'titel-2', 'pteds'),
            (publisher, 'titel-3', 'pteds'),
            (publisher, 'titel-4', 'pteds'),
            (editor_1, 'titel-1', 'peds'),
            (editor_1, 'titel-2', 'peds'),
            (editor_1, 'titel-3', 'p'),
            (editor_1, 'titel-4', 'p'),
            (editor_2, 'titel-1', 'peds'),
            (editor_2, 'titel-2', 'peds'),
            (editor_2, 'titel-3', 'p'),
            (editor_2, 'titel-4', 'p'),
            (editor_3, 'titel-1', 'p'),
            (editor_3, 'titel-2', 'p'),
            (editor_3, 'titel-3', 'peds'),
            (editor_3, 'titel-4', 'p'),
        ))

        # ... when accepted
        submit_notice(editor_1, 'titel-1')
        submit_notice(editor_2, 'titel-2')
        submit_notice(editor_3, 'titel-3')
        submit_notice(publisher, 'titel-4')
        accept_notice(publisher, 'titel-1')
        accept_notice(publisher, 'titel-2')
        accept_notice(publisher, 'titel-3')
        accept_notice(publisher, 'titel-4')

        check((
            (admin, 'titel-1', 'ptedc'),
            (admin, 'titel-2', 'ptedc'),
            (admin, 'titel-3', 'ptedc'),
            (admin, 'titel-4', 'ptedc'),
            (publisher, 'titel-1', 'pedc'),
            (publisher, 'titel-2', 'pedc'),
            (publisher, 'titel-3', 'pedc'),
            (publisher, 'titel-4', 'pedc'),
            (editor_1, 'titel-1', 'pc'),
            (editor_1, 'titel-2', 'pc'),
            (editor_1, 'titel-3', 'pc'),
            (editor_1, 'titel-4', 'pc'),
            (editor_2, 'titel-1', 'pc'),
            (editor_2, 'titel-2', 'pc'),
            (editor_2, 'titel-3', 'pc'),
            (editor_2, 'titel-4', 'pc'),
            (editor_3, 'titel-1', 'pc'),
            (editor_3, 'titel-2', 'pc'),
            (editor_3, 'titel-3', 'pc'),
            (editor_3, 'titel-4', 'pc'),
        ))

        # ... when published
        publish_issue(publisher, '2017-44')
        check((
            (admin, 'titel-1', 'ptec'),
            (admin, 'titel-2', 'ptec'),
            (admin, 'titel-3', 'ptec'),
            (admin, 'titel-4', 'ptec'),
            (publisher, 'titel-1', 'pec'),
            (publisher, 'titel-2', 'pec'),
            (publisher, 'titel-3', 'pec'),
            (publisher, 'titel-4', 'pec'),
            (editor_1, 'titel-1', 'pc'),
            (editor_1, 'titel-2', 'pc'),
            (editor_1, 'titel-3', 'pc'),
            (editor_1, 'titel-4', 'pc'),
            (editor_2, 'titel-1', 'pc'),
            (editor_2, 'titel-2', 'pc'),
            (editor_2, 'titel-3', 'pc'),
            (editor_2, 'titel-4', 'pc'),
            (editor_3, 'titel-1', 'pc'),
            (editor_3, 'titel-2', 'pc'),
            (editor_3, 'titel-3', 'pc'),
            (editor_3, 'titel-4', 'pc'),
        ))

        # ... when imported
        session = gazette_app.session()
        notice = session.query(GazetteNotice).filter_by(name='titel-1').one()
        notice.user = None
        notice.group = None
        notice.source = 'source'
        notice.state = 'imported'
        session.flush()
        import transaction
        transaction.commit()

        check((
            (admin, 'titel-1', 'pda'),
            (publisher, 'titel-1', 'pad'),
            (editor_1, 'titel-1', 'p'),
        ))


def test_view_notice_preview(gazette_app):
    admin, editor_1, editor_2, editor_3, publisher = login_users(gazette_app)

    with freeze_time("2017-11-01 11:00"):
        manage = editor_1.get('/notices/drafted/new-notice')
        manage.form['title'] = 'Titel'
        manage.form['organization'] = '200'
        manage.form['category'] = '11'
        manage.form['issues'] = ['2017-44', '2017-45']
        manage.form['text'] = "1. Oktober 2017"
        manage.form['author_place'] = 'Govikon'
        manage.form['author_name'] = 'State Chancellerist'
        manage.form['author_date'] = '2019-01-01'
        manage.form.submit()

    view = editor_1.get('/notice/titel/preview')
    assert "Titel" in view
    assert "1. Oktober 2017" in view
    assert "Govikon, 1. Januar 2019" in view
    assert "State Chancellerist" in view
    assert "Civic Community" not in view
    assert "Education" not in view
    assert "TestGroup" not in view
    assert "Nr. 44, 03.11.2017" not in view
    assert "Nr. 45, 10.11.2017" not in view
    assert "in Arbeit" not in view
    assert "erstellt" not in view


def test_view_notice_pdf_preview(gazette_app):
    admin, editor_1, editor_2, editor_3, publisher = login_users(gazette_app)

    with freeze_time("2017-11-01 11:00"):
        manage = editor_1.get('/notices/drafted/new-notice')
        manage.form['title'] = 'Titel'
        manage.form['organization'] = '200'
        manage.form['category'] = '11'
        manage.form['issues'] = ['2017-44', '2017-45']
        manage.form['text'] = "1. Oktober 2017"
        manage.form['author_place'] = 'Govikon'
        manage.form['author_name'] = 'State Chancellerist'
        manage.form['author_date'] = '2019-01-01'
        manage.form.submit()

    with freeze_time("2018-01-01 12:00"):
        response = editor_1.get('/notice/titel/preview-pdf')
        assert response.headers['Content-Type'] == 'application/pdf'
        assert response.headers['Content-Disposition'] == \
            'inline; filename=amtsblatt-govikon-titel.pdf'

        reader = PdfFileReader(BytesIO(response.body))
        assert [page.extractText() for page in reader.pages] == [
            '© 2018 Govikon\n1\nxxx\nTitel\n1. Oktober 2017\n'
            'Govikon, 1. Januar 2019\nState Chancellerist\n'
        ]


def test_view_notice_delete(gazette_app):
    admin, editor_1, editor_2, editor_3, publisher = login_users(gazette_app)

    with freeze_time("2017-11-01 11:00"):
        # delete a drafted notice
        for user in (editor_1, publisher):
            manage = editor_1.get('/notices/drafted/new-notice')
            manage.form['title'] = "Erneuerungswahlen"
            manage.form['organization'] = '200'
            manage.form['category'] = '11'
            manage.form['issues'] = ['2017-44', '2017-45']
            manage.form['text'] = "1. Oktober 2017"
            manage.form['author_place'] = 'Govikon'
            manage.form['author_name'] = 'State Chancellerist'
            manage.form['author_date'] = '2019-01-01'
            manage.form.submit()

            manage = user.get('/notice/erneuerungswahlen/delete')
            manage = manage.form.submit().maybe_follow()
            assert "Meldung gelöscht." in manage

        # delete a submitted notice
        for user in (editor_1, publisher):
            manage = editor_1.get('/notices/drafted/new-notice')
            manage.form['title'] = "Erneuerungswahlen"
            manage.form['organization'] = '200'
            manage.form['category'] = '11'
            manage.form['issues'] = ['2017-44', '2017-45']
            manage.form['text'] = "1. Oktober 2017"
            manage.form['author_place'] = 'Govikon'
            manage.form['author_name'] = 'State Chancellerist'
            manage.form['author_date'] = '2019-01-01'
            manage.form.submit()

            submit_notice(user, 'erneuerungswahlen')

            manage = user.get('/notice/erneuerungswahlen/delete')
            assert manage.forms == {}

            manage = admin.get('/notice/erneuerungswahlen/delete')
            manage.form.submit().maybe_follow()

        # delete a rejected notice
        for user in (editor_1, publisher):
            manage = editor_1.get('/notices/drafted/new-notice')
            manage.form['title'] = "Erneuerungswahlen"
            manage.form['organization'] = '200'
            manage.form['category'] = '11'
            manage.form['issues'] = ['2017-44', '2017-45']
            manage.form['text'] = "1. Oktober 2017"
            manage.form['author_place'] = 'Govikon'
            manage.form['author_name'] = 'State Chancellerist'
            manage.form['author_date'] = '2019-01-01'
            manage.form.submit()

            submit_notice(user, 'erneuerungswahlen')
            reject_notice(publisher, 'erneuerungswahlen')

            manage = user.get('/notice/erneuerungswahlen/delete')
            manage = manage.form.submit().maybe_follow()
            assert "Meldung gelöscht." in manage

        # delete an accepted notice
        manage = editor_1.get('/notices/drafted/new-notice')
        manage.form['title'] = "Erneuerungswahlen"
        manage.form['organization'] = '200'
        manage.form['category'] = '11'
        manage.form['issues'] = ['2017-44', '2017-45']
        manage.form['text'] = "1. Oktober 2017"
        manage.form['author_place'] = 'Govikon'
        manage.form['author_name'] = 'State Chancellerist'
        manage.form['author_date'] = '2019-01-01'
        manage.form.submit()

        submit_notice(editor_1, 'erneuerungswahlen')
        accept_notice(publisher, 'erneuerungswahlen')

        manage = editor_1.get('/notice/erneuerungswahlen/delete')
        assert manage.forms == {}

        manage = publisher.get('/notice/erneuerungswahlen/delete')
        assert "Diese Meldung wurde bereits angenommen!" in manage
        manage.form.submit().maybe_follow()

        # delete a published notice
        manage = editor_1.get('/notices/drafted/new-notice')
        manage.form['title'] = "Erneuerungswahlen"
        manage.form['organization'] = '200'
        manage.form['category'] = '11'
        manage.form['issues'] = ['2017-44', '2017-45']
        manage.form['text'] = "1. Oktober 2017"
        manage.form['author_place'] = 'Govikon'
        manage.form['author_name'] = 'State Chancellerist'
        manage.form['author_date'] = '2019-01-01'
        manage.form.submit()

        submit_notice(editor_1, 'erneuerungswahlen')
        accept_notice(publisher, 'erneuerungswahlen')
        publish_issue(publisher, '2017-44')

        for user in (admin, editor_1, publisher):
            manage = user.get('/notice/erneuerungswahlen/delete')
            assert manage.forms == {}


def test_view_notice_changelog(gazette_app):
    admin, editor_1, editor_2, editor_3, publisher = login_users(gazette_app)

    with freeze_time("2017-11-01 10:00"):
        manage = editor_1.get('/notices/drafted/new-notice')
        manage.form['title'] = "Erneuerungswahlen"
        manage.form['organization'] = '200'
        manage.form['category'] = '11'
        manage.form['issues'] = ['2017-44', '2017-45']
        manage.form['text'] = "1. Oktober 2017"
        manage.form['author_place'] = 'Govikon'
        manage.form['author_name'] = 'State Chancellerist'
        manage.form['author_date'] = '2019-01-01'
        manage.form.submit()

    with freeze_time("2017-11-01 11:02"):
        submit_notice(editor_1, 'erneuerungswahlen')

    with freeze_time("2017-11-01 11:30"):
        reject_notice(publisher, 'erneuerungswahlen')

    with freeze_time("2017-11-01 11:45"):
        edit_notice(editor_2, 'erneuerungswahlen', organization='300')

    with freeze_time("2017-11-01 11:48"):
        submit_notice(editor_2, 'erneuerungswahlen')

    with freeze_time("2017-11-01 15:00"):
        accept_notice(publisher, 'erneuerungswahlen')

    with freeze_time("2017-11-01 16:00"):
        publish_issue(publisher, '2017-44')

    view = editor_1.get('/notice/erneuerungswahlen')

    changes = [
        ''.join(i.strip() for i in td.itertext())
        for td in view.pyquery('table.changes td')
    ]
    changes = sorted([
        (
            changes[4 * i + 0],
            changes[4 * i + 1],
            changes[4 * i + 2],
            changes[4 * i + 3]
        )
        for i in range(len(changes) // 4)
    ])

    assert changes == [
        ('01.11.2017 11:00', 'First Editor', 'TestGroup', 'erstellt'),
        ('01.11.2017 12:02', 'First Editor', 'TestGroup',
         'eingereicht'),
        ('01.11.2017 12:30', 'Publisher', '', 'zurückgewiesenXYZ'),
        ('01.11.2017 12:45', 'Second Editor', 'TestGroup', 'bearbeitet'),
        ('01.11.2017 12:48', 'Second Editor', 'TestGroup',
         'eingereicht'),
        ('01.11.2017 16:00', 'Publisher', '', 'Druck beauftragt'),
        ('01.11.2017 16:00', 'Publisher', '', 'angenommen'),
        ('01.11.2017 17:00', 'Publisher', '', 'veröffentlicht')
    ]


def test_view_notice_copy(gazette_app):
    admin, editor_1, editor_2, editor_3, publisher = login_users(gazette_app)

    with freeze_time("2017-10-01 12:00"):
        manage = editor_1.get('/notices/drafted/new-notice')
        manage.form['title'] = "Erneuerungswahlen"
        manage.form['organization'] = '200'
        manage.form['category'] = '11'
        manage.form['issues'] = ['2017-40']
        manage.form['text'] = "1. Oktober 2017"
        manage.form['author_place'] = 'Govikon'
        manage.form['author_name'] = 'State Chancellerist'
        manage.form['author_date'] = '2019-01-01'
        manage.form.submit()

        submit_notice(editor_1, 'erneuerungswahlen')
        accept_notice(publisher, 'erneuerungswahlen')

    with freeze_time("2017-10-01 12:00"):
        edit_notice_unrestricted(publisher, 'erneuerungswahlen', note='NOTE!')

    with freeze_time("2018-01-01 12:00"):
        for user in (editor_1, editor_2, editor_3, publisher):
            manage = user.get('/notice/erneuerungswahlen').click("Kopieren")
            assert manage.form['title'].value == "Erneuerungswahlen"
            assert manage.form['organization'].value == '200'
            assert manage.form['category'].value == '11'
            assert manage.form['text'].value == "1. Oktober 2017"
            assert manage.form['issues'].value is None

            manage.form['issues'] = ['2018-1']
            manage = manage.form.submit().maybe_follow()

            assert "Erneuerungswahlen" in user.get('/dashboard')
            assert "Erneuerungswahlen" in user.get('/notices/drafted')

        "NOTE!" in publisher.get('/notice/erneuerungswahlen-1')
        "NOTE!" in publisher.get('/notice/erneuerungswahlen-2')
        "NOTE!" in publisher.get('/notice/erneuerungswahlen-3')
        "NOTE!" in publisher.get('/notice/erneuerungswahlen-4')
