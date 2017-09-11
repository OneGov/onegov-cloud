from freezegun import freeze_time
from onegov.gazette.tests import login_admin
from onegov.gazette.tests import login_editor_1
from onegov.gazette.tests import login_editor_2
from onegov.gazette.tests import login_editor_3
from onegov.gazette.tests import login_publisher
from webtest import TestApp as Client


def login_users(gazette_app):
    editor_1 = Client(gazette_app)
    login_editor_1(editor_1)

    editor_2 = Client(gazette_app)
    login_editor_2(editor_2)

    editor_3 = Client(gazette_app)
    login_editor_3(editor_3)

    publisher = Client(gazette_app)
    login_publisher(publisher)

    return editor_1, editor_2, editor_3, publisher


def submit_notice(user, slug, unable=False, forbidden=False):
    url = '/notice/{}/submit'.format(slug)
    if unable:
        assert not user.get(url).forms
    elif forbidden:
        assert user.get(url, status=403)
    else:
        manage = user.get(url)
        manage = manage.form.submit()
        assert "Meldung eingereicht" in manage.maybe_follow()


def accept_notice(user, slug, unable=False, forbidden=False):
    url = '/notice/{}/accept'.format(slug)
    if unable:
        assert not user.get(url).forms
    elif forbidden:
        assert user.get(url, status=403)
    else:
        manage = user.get(url)
        manage = manage.form.submit()
        assert "Meldung angenommen" in manage.maybe_follow()


def reject_notice(user, slug, unable=False, forbidden=False):
    url = '/notice/{}/reject'.format(slug)
    if unable:
        assert not user.get(url).forms
    elif forbidden:
        assert user.get(url, status=403)
    else:
        manage = user.get(url)
        manage.form['comment'] = 'XYZ'
        manage = manage.form.submit()
        assert "Meldung zurückgewiesen" in manage.maybe_follow()


def edit_notice(user, slug, unable=False, forbidden=False, **kwargs):
    url = '/notice/{}/edit'.format(slug)
    if unable:
        assert not user.get(url).forms
    elif forbidden:
        assert user.get(url, status=403)
    else:
        manage = user.get(url)
        for key, value in kwargs.items():
            manage.form[key] = value
        manage = manage.form.submit().maybe_follow()


def test_view_notice(gazette_app):
    # Check if the details of the notice is displayed correctly in the
    # display view (that is: organization, owner, group etc).

    editor_1, editor_2, editor_3, publisher = login_users(gazette_app)

    with freeze_time("2017-11-01 12:00"):
        # create a notice for each editor
        for count, user in enumerate((editor_1, editor_2, editor_3)):
            manage = user.get('/notices/drafted/new-notice')
            manage.form['title'] = 'Titel {}'.format(count + 1)
            manage.form['organization'] = '200'
            manage.form['category'] = '11'
            manage.form['issues'] = ['2017-44', '2017-45']
            manage.form['text'] = "1. Oktober 2017"
            manage.form.submit()

        # check if the notices are displayed correctly
        for slug, title, owner, group in (
            ('titel-1', 'Titel 1', 'editor1@example.org', True),
            ('titel-2', 'Titel 2', 'editor2@example.org', True),
            ('titel-3', 'Titel 3', 'editor3@example.org', False),
        ):
            for user in (editor_1, editor_2, editor_3, publisher):
                view = user.get('/notice/{}'.format(slug))
                assert title in view
                assert "1. Oktober 2017" in view
                assert "Civic Community" in view
                assert "Education" in view
                assert owner in view
                if group:
                    assert "TestGroup" in view
                else:
                    assert "TestGroup" not in view
                assert "Nr. 44, 03.11.2017" in view
                assert "Nr. 45, 10.11.2017" in view
                assert "in Arbeit" in view
                assert "erstellt" in view


def test_view_notice_actions(gazette_app):
    # Check if the actions are displayed correctly in the detail view

    editor_1, editor_2, editor_3, publisher = login_users(gazette_app)

    with freeze_time("2017-11-01 12:00"):
        # create a notice for each editor
        for count, user in enumerate(
            (editor_1, editor_2, editor_3, publisher)
        ):
            manage = user.get('/notices/drafted/new-notice')
            manage.form['title'] = 'Titel {}'.format(count + 1)
            manage.form['organization'] = '200'
            manage.form['category'] = '11'
            manage.form['issues'] = ['2017-44', '2017-45']
            manage.form['text'] = "1. Oktober 2017"
            manage.form.submit()

        # check the actions
        actions = {
            'p': 'action-preview',
            'c': 'action-copy',
            'e': 'action-edit',
            'd': 'action-delete',
            's': 'action-submit',
            'a': 'action-accept',
            'r': 'action-reject',
        }

        def check(values):
            for user, slug, can in values:
                view = user.get('/notice/{}'.format(slug))
                cannot = [x for x in actions.keys() if x not in can]
                assert all((actions[action] in view for action in can))
                assert all((actions[action] not in view for action in cannot))

        # ... when drafted
        check((
            (publisher, 'titel-1', 'p'),
            (publisher, 'titel-2', 'p'),
            (publisher, 'titel-3', 'p'),
            (publisher, 'titel-4', 'peds'),
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
            (publisher, 'titel-1', 'pear'),
            (publisher, 'titel-2', 'pear'),
            (publisher, 'titel-3', 'pear'),
            (publisher, 'titel-4', 'pear'),
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
            (publisher, 'titel-1', 'p'),
            (publisher, 'titel-2', 'p'),
            (publisher, 'titel-3', 'p'),
            (publisher, 'titel-4', 'peds'),
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
            (publisher, 'titel-1', 'pc'),
            (publisher, 'titel-2', 'pc'),
            (publisher, 'titel-3', 'pc'),
            (publisher, 'titel-4', 'pc'),
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


def test_view_notice_preview(gazette_app):
    editor = Client(gazette_app)
    login_editor_1(editor)

    with freeze_time("2017-11-01 12:00"):
        manage = editor.get('/notices/drafted/new-notice')
        manage.form['title'] = 'Titel'
        manage.form['organization'] = '200'
        manage.form['category'] = '11'
        manage.form['issues'] = ['2017-44', '2017-45']
        manage.form['text'] = "1. Oktober 2017"
        manage.form.submit()

    view = editor.get('/notice/titel/preview')
    assert "Titel" in view
    assert "1. Oktober 2017" in view
    assert "Civic Community" not in view
    assert "Education" not in view
    assert "TestGroup" not in view
    assert "Nr. 44, 03.11.2017" not in view
    assert "Nr. 45, 10.11.2017" not in view
    assert "in Arbeit" not in view
    assert "erstellt" not in view


def test_view_notice_submit(gazette_app):
    editor_1, editor_2, editor_3, publisher = login_users(gazette_app)

    with freeze_time("2017-11-01 12:00"):
        # create a notice for each editor
        for count, user in enumerate((editor_1, editor_2, editor_3)):
            manage = user.get('/notices/drafted/new-notice')
            manage.form['title'] = 'Titel {}'.format(count + 1)
            manage.form['organization'] = '200'
            manage.form['category'] = '11'
            manage.form['issues'] = ['2017-44', '2017-45']
            manage.form['text'] = "1. Oktober 2017"
            manage.form.submit()

    # check invalid actions
    for action in ('reject', 'accept'):
        assert not publisher.get('/notice/titel-1/{}'.format(action)).forms
        assert not publisher.get('/notice/titel-2/{}'.format(action)).forms
        assert not publisher.get('/notice/titel-3/{}'.format(action)).forms
        for user in (editor_1, editor_2, editor_3):
            user.get('/notice/titel-1/{}'.format(action), status=403)
            user.get('/notice/titel-2/{}'.format(action), status=403)
            user.get('/notice/titel-3/{}'.format(action), status=403)

    # check if the notices can be submitted
    for user, slug, forbidden in (
        (editor_1, 'titel-3', True),
        (editor_3, 'titel-1', True),
        (editor_1, 'titel-1', False),
        (editor_1, 'titel-2', False),
        (editor_3, 'titel-3', False),
    ):
        submit_notice(user, slug, forbidden=forbidden)


def test_view_notice_reject(gazette_app):
    editor_1, editor_2, editor_3, publisher = login_users(gazette_app)

    with freeze_time("2017-11-01 12:00"):
        # create a notice for each editor
        for count, user in enumerate((editor_1, editor_2, editor_3)):
            manage = user.get('/notices/drafted/new-notice')
            manage.form['title'] = 'Titel {}'.format(count + 1)
            manage.form['organization'] = '200'
            manage.form['category'] = '11'
            manage.form['issues'] = ['2017-44', '2017-45']
            manage.form['text'] = "1. Oktober 2017"
            manage.form.submit()
            submit_notice(user, 'titel-{}'.format(count + 1))

    # check wrong actions
    submit_notice(publisher, 'titel-1', unable=True)
    submit_notice(publisher, 'titel-2', unable=True)
    submit_notice(publisher, 'titel-3', unable=True)
    submit_notice(editor_1, 'titel-1', unable=True)
    submit_notice(editor_1, 'titel-2', unable=True)
    submit_notice(editor_1, 'titel-3', forbidden=True)
    submit_notice(editor_2, 'titel-1', unable=True)
    submit_notice(editor_2, 'titel-2', unable=True)
    submit_notice(editor_2, 'titel-3', forbidden=True)
    submit_notice(editor_3, 'titel-1', forbidden=True)
    submit_notice(editor_3, 'titel-2', forbidden=True)
    submit_notice(editor_3, 'titel-3', unable=True)

    # check if the notices can be rejected
    for user, slug, forbidden in (
        (editor_1, 'titel-1', True),
        (editor_1, 'titel-2', True),
        (editor_1, 'titel-3', True),
        (editor_3, 'titel-3', True),
        (publisher, 'titel-1', False),
        (publisher, 'titel-2', False),
        (publisher, 'titel-3', False),
    ):
        reject_notice(user, slug, forbidden=forbidden)


def test_view_notice_accept(gazette_app):
    editor_1, editor_2, editor_3, publisher = login_users(gazette_app)

    with freeze_time("2017-11-01 12:00"):
        # create a notice for each editor
        for count, user in enumerate((editor_1, editor_2, editor_3)):
            manage = user.get('/notices/drafted/new-notice')
            manage.form['title'] = 'Titel {}'.format(count + 1)
            manage.form['organization'] = '200'
            manage.form['category'] = '11'
            manage.form['issues'] = ['2017-44', '2017-45']
            manage.form['text'] = "1. Oktober 2017"
            manage.form.submit()
            submit_notice(user, 'titel-{}'.format(count + 1))

    # check wrong actions
    submit_notice(publisher, 'titel-1', unable=True)
    submit_notice(publisher, 'titel-2', unable=True)
    submit_notice(publisher, 'titel-3', unable=True)
    submit_notice(editor_1, 'titel-1', unable=True)
    submit_notice(editor_1, 'titel-2', unable=True)
    submit_notice(editor_1, 'titel-3', forbidden=True)
    submit_notice(editor_2, 'titel-1', unable=True)
    submit_notice(editor_2, 'titel-2', unable=True)
    submit_notice(editor_2, 'titel-3', forbidden=True)
    submit_notice(editor_3, 'titel-1', forbidden=True)
    submit_notice(editor_3, 'titel-2', forbidden=True)
    submit_notice(editor_3, 'titel-3', unable=True)

    # check if the notices can be accepted
    for user, slug, forbidden in (
        (editor_1, 'titel-1', True),
        (editor_1, 'titel-2', True),
        (editor_1, 'titel-3', True),
        (editor_3, 'titel-3', True),
        (publisher, 'titel-1', False),
        (publisher, 'titel-2', False),
        # (publisher, 'titel-3', False),
    ):
        accept_notice(user, slug, forbidden=forbidden)

    assert len(gazette_app.smtp.outbox) == 2
    for message in gazette_app.smtp.outbox:
        assert message['Reply-To'] == 'mails@govikon.ch'
        payload = message.get_payload(1).get_payload(decode=True)
        payload = payload.decode('utf-8')
        assert "Publikation für den amtlichen Teil" in payload

    principal = gazette_app.principal
    principal.publish_from = 'publisher@govikon.ch'
    gazette_app.cache.set('principal', principal)

    accept_notice(publisher, 'titel-3')

    assert len(gazette_app.smtp.outbox) == 3
    message = gazette_app.smtp.outbox[2]
    assert message['Reply-To'] == 'publisher@govikon.ch'
    payload = message.get_payload(1).get_payload(decode=True)
    payload = payload.decode('utf-8')
    assert "Publikation für den amtlichen Teil" in payload


def test_view_notice_delete(gazette_app):
    with freeze_time("2017-11-01 12:00"):
        editor = Client(gazette_app)
        login_editor_1(editor)

        publisher = Client(gazette_app)
        login_publisher(publisher)

        admin = Client(gazette_app)
        login_admin(admin)

        # delete a drafted notice
        for user in (editor, publisher):
            manage = editor.get('/notices/drafted/new-notice')
            manage.form['title'] = "Erneuerungswahlen"
            manage.form['organization'] = '200'
            manage.form['category'] = '11'
            manage.form['issues'] = ['2017-44', '2017-45']
            manage.form['text'] = "1. Oktober 2017"
            manage.form.submit()

            manage = user.get('/notice/erneuerungswahlen/delete')
            manage = manage.form.submit().maybe_follow()
            assert "Meldung gelöscht." in manage

        # delete a submitted notice
        for user in (editor, publisher):
            manage = editor.get('/notices/drafted/new-notice')
            manage.form['title'] = "Erneuerungswahlen"
            manage.form['organization'] = '200'
            manage.form['category'] = '11'
            manage.form['issues'] = ['2017-44', '2017-45']
            manage.form['text'] = "1. Oktober 2017"
            manage.form.submit()

            submit_notice(user, 'erneuerungswahlen')

            manage = user.get('/notice/erneuerungswahlen/delete')
            assert manage.forms == {}

            manage = admin.get('/notice/erneuerungswahlen/delete')
            manage.form.submit().maybe_follow()

        # delete a rejected notice
        for user in (editor, publisher):
            manage = editor.get('/notices/drafted/new-notice')
            manage.form['title'] = "Erneuerungswahlen"
            manage.form['organization'] = '200'
            manage.form['category'] = '11'
            manage.form['issues'] = ['2017-44', '2017-45']
            manage.form['text'] = "1. Oktober 2017"
            manage.form.submit()

            submit_notice(user, 'erneuerungswahlen')
            reject_notice(publisher, 'erneuerungswahlen')

            manage = user.get('/notice/erneuerungswahlen/delete')
            manage = manage.form.submit().maybe_follow()
            assert "Meldung gelöscht." in manage

        # delete an accepted notice
        for user in (editor, publisher):
            manage = editor.get('/notices/drafted/new-notice')
            manage.form['title'] = "Erneuerungswahlen"
            manage.form['organization'] = '200'
            manage.form['category'] = '11'
            manage.form['issues'] = ['2017-44', '2017-45']
            manage.form['text'] = "1. Oktober 2017"
            manage.form.submit()

            submit_notice(editor, 'erneuerungswahlen')
            accept_notice(publisher, 'erneuerungswahlen')

            manage = user.get('/notice/erneuerungswahlen/delete')
            assert manage.forms == {}

            manage = admin.get('/notice/erneuerungswahlen/delete')
            manage.form.submit().maybe_follow()


def test_view_notice_changelog(gazette_app):
    editor_1 = Client(gazette_app)
    login_editor_1(editor_1)

    editor_2 = Client(gazette_app)
    login_editor_1(editor_2)

    publisher = Client(gazette_app)
    login_publisher(publisher)

    with freeze_time("2017-11-01 12:00"):
        manage = editor_1.get('/notices/drafted/new-notice')
        manage.form['title'] = "Erneuerungswahlen"
        manage.form['organization'] = '200'
        manage.form['category'] = '11'
        manage.form['issues'] = ['2017-44', '2017-45']
        manage.form['text'] = "1. Oktober 2017"
        manage.form.submit()

    with freeze_time("2017-11-01 12:02"):
        submit_notice(editor_1, 'erneuerungswahlen')

    with freeze_time("2017-11-01 12:30"):
        reject_notice(publisher, 'erneuerungswahlen')

    with freeze_time("2017-11-01 14:00"):
        edit_notice(editor_2, 'erneuerungswahlen', organization='300')

    with freeze_time("2017-11-01 14:02"):
        submit_notice(editor_2, 'erneuerungswahlen')

    with freeze_time("2017-11-01 15:00"):
        accept_notice(publisher, 'erneuerungswahlen')

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
        ('01.11.2017 13:00', 'editor1@example.org', 'TestGroup', 'erstellt'),
        ('01.11.2017 13:02', 'editor1@example.org', 'TestGroup',
         'eingereicht'),
        ('01.11.2017 13:30', 'publisher@example.org', '', 'zurückgewiesenXYZ'),
        ('01.11.2017 15:00', 'editor1@example.org', 'TestGroup', 'bearbeitet'),
        ('01.11.2017 15:02', 'editor1@example.org', 'TestGroup',
         'eingereicht'),
        ('01.11.2017 16:00', 'publisher@example.org', '', 'E-Mail gesendet'),
        ('01.11.2017 16:00', 'publisher@example.org', '', 'angenommen'),
    ]


def test_view_notice_edit(gazette_app):
    editor_1, editor_2, editor_3, publisher = login_users(gazette_app)

    with freeze_time("2017-11-01 12:00"):
        manage = editor_1.get('/notices/drafted/new-notice')
        manage.form['title'] = "Notice"
        manage.form['organization'] = '200'
        manage.form['category'] = '11'
        manage.form['issues'] = ['2017-44', '2017-45']
        manage.form['text'] = "1. Oktober 2017"
        manage.form.submit()

        edit_notice(
            editor_1, 'notice',
            title="Kantonsratswahl",
            organization='300',
            category='12',
            issues=['2017-46'],
            text="1. Dezember 2017",
        )
        view = editor_1.get('/notice/notice')
        assert "Kantonsratswahl" in view
        assert "Municipality" in view
        assert "Submissions" in view
        assert "Nr. 46, 17.11.2017" in view
        assert "1. Dezember 2017" in view

    # drafed
    for user, title, forbidden in (
        (editor_1, 'XXX1', False),
        (editor_2, 'XXX2', False),
        (editor_3, 'XXX3', True),
        (publisher, 'XXX4', False),
    ):
        edit_notice(user, 'notice', title=title, forbidden=forbidden)
        if not forbidden:
            assert title in editor_1.get('/notice/notice')

    # submitted
    submit_notice(editor_1, 'notice')
    for user, title, forbidden in (
        (editor_1, 'YYY1', False),
        (editor_2, 'YYY2', False),
        (editor_3, 'YYY3', True),
        (publisher, 'YYY4', False),
    ):
        edit_notice(user, 'notice', title=title, forbidden=forbidden)
        if not forbidden:
            assert title in editor_1.get('/notice/notice')

    # rejected
    reject_notice(publisher, 'notice')
    for user, title, forbidden in (
        (editor_1, 'YYY1', False),
        (editor_2, 'YYY2', False),
        (editor_3, 'YYY3', True),
        (publisher, 'YYY4', False),
    ):
        edit_notice(user, 'notice', title=title, forbidden=forbidden)
        if not forbidden:
            assert title in editor_1.get('/notice/notice')

    # accepted
    submit_notice(editor_1, 'notice')
    accept_notice(publisher, 'notice')
    edit_notice(editor_1, 'notice', unable=True)
    edit_notice(editor_2, 'notice', unable=True)
    edit_notice(editor_3, 'notice', forbidden=True)
    edit_notice(publisher, 'notice', unable=True)


def test_view_notice_copy(gazette_app):
    editor_1 = Client(gazette_app)
    login_editor_1(editor_1)

    editor_2 = Client(gazette_app)
    login_editor_1(editor_2)

    editor_3 = Client(gazette_app)
    login_editor_1(editor_3)

    publisher = Client(gazette_app)
    login_publisher(publisher)

    with freeze_time("2017-10-01 12:00"):
        manage = editor_1.get('/notices/drafted/new-notice')
        manage.form['title'] = "Erneuerungswahlen"
        manage.form['organization'] = '200'
        manage.form['category'] = '11'
        manage.form['issues'] = ['2017-40']
        manage.form['text'] = "1. Oktober 2017"
        manage.form.submit()

        submit_notice(editor_1, 'erneuerungswahlen')
        accept_notice(publisher, 'erneuerungswahlen')

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
