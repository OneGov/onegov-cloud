from freezegun import freeze_time
from onegov.gazette.models import Category
from onegov.gazette.models import Organization
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


def submit_notice(user, slug, unable=False, forbidden=False, redirected=False):
    url = '/notice/{}/submit'.format(slug)
    if unable:
        assert not user.get(url).forms
    elif forbidden:
        assert user.get(url, status=403)
    elif redirected:
        assert '/edit' in user.get(url, status=302).location
    else:
        manage = user.get(url)
        manage = manage.form.submit()
        assert "Meldung eingereicht" in manage.maybe_follow()


def accept_notice(user, slug, unable=False, forbidden=False, redirected=False):
    url = '/notice/{}/accept'.format(slug)
    if unable:
        assert not user.get(url).forms
    elif forbidden:
        assert user.get(url, status=403)
    elif redirected:
        assert '/edit' in user.get(url, status=302).location
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


def publish_notice(user, slug, unable=False, forbidden=False):
    url = '/notice/{}/publish'.format(slug)
    if unable:
        assert not user.get(url).forms
    elif forbidden:
        assert user.get(url, status=403)
    else:
        manage = user.get(url)
        manage = manage.form.submit()
        assert "Meldung veröffentlicht" in manage.maybe_follow()


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
        manage = manage.form.submit()
        assert "Meldung geändert" in manage.maybe_follow()


def edit_notice_unrestricted(user, slug, unable=False, forbidden=False,
                             **kwargs):
    url = '/notice/{}/edit_unrestricted'.format(slug)
    if unable:
        assert not user.get(url).forms
    elif forbidden:
        assert user.get(url, status=403)
    else:
        manage = user.get(url)
        for key, value in kwargs.items():
            manage.form[key] = value
        manage = manage.form.submit()
        assert "Meldung geändert" in manage.maybe_follow()


def change_category(gazette_app, name, **kwargs):
    admin = Client(gazette_app)
    login_admin(admin)

    session = gazette_app.session()
    category = session.query(Category.id).filter_by(name=name).one()[0]
    manage = admin.get('/category/{}/edit'.format(category))
    for key, value in kwargs.items():
        manage.form[key] = value
    manage.form.submit()


def change_organization(gazette_app, name, **kwargs):
    admin = Client(gazette_app)
    login_admin(admin)

    session = gazette_app.session()
    org = session.query(Organization.id).filter_by(name=name).one()[0]
    manage = admin.get('/organization/{}/edit'.format(org))
    for key, value in kwargs.items():
        manage.form[key] = value
    manage.form.submit()


def test_view_notice1(gazette_app):
    # Check if the details of the notice is displayed correctly in the
    # display view (that is: organization, owner, group etc).

    editor_1, editor_2, editor_3, publisher = login_users(gazette_app)

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
            manage.form.submit()

        # check if the notices are displayed correctly
        for slug, title, owner, group in (
            ('titel-1', 'Titel 1', 'First Editor', True),
            ('titel-2', 'Titel 2', 'Second Editor', True),
            ('titel-3', 'Titel 3', 'Third Editor', False),
        ):
            for user in (editor_1, editor_2, editor_3, publisher):
                view = user.get('/notice/{}'.format(slug))
                assert title in view
                assert "1. Oktober 2017" in view
                assert "Civic Community" in view
                assert "Education" in view
                assert "<dd>Ja</dd>" in view
                assert "someone<br>street<br>place" in view
                assert owner in view
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
        publish_notice(publisher, 'titel-1')
        publish_notice(publisher, 'titel-2')
        publish_notice(publisher, 'titel-3')

        for number in range(3):
            for user in (editor_1, editor_2, editor_3, publisher):
                view = user.get('/notice/titel-{}'.format(number + 1))
                assert "Nr. 44, 03.11.2017 / {}".format(2 * number + 1) in view
                assert "Nr. 45, 10.11.2017 / {}".format(2 * number + 2) in view


def test_view_notice_actions(gazette_app):
    # Check if the actions are displayed correctly in the detail view

    editor_1, editor_2, editor_3, publisher = login_users(gazette_app)
    admin = Client(gazette_app)
    login_admin(admin)

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
            'x': 'action-publish'
        }

        def check(values):
            for user, slug, can in values:
                view = user.get('/notice/{}'.format(slug))
                cannot = [x for x in actions.keys() if x not in can]
                assert all((actions[action] in view for action in can))
                assert all((actions[action] not in view for action in cannot))

        # ... when drafted
        check((
            (admin, 'titel-1', 'peds'),
            (admin, 'titel-2', 'peds'),
            (admin, 'titel-3', 'peds'),
            (admin, 'titel-4', 'peds'),
            (publisher, 'titel-1', 'peds'),
            (publisher, 'titel-2', 'peds'),
            (publisher, 'titel-3', 'peds'),
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
            (admin, 'titel-1', 'pedar'),
            (admin, 'titel-2', 'pedar'),
            (admin, 'titel-3', 'pedar'),
            (admin, 'titel-4', 'pedar'),
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
            (admin, 'titel-1', 'peds'),
            (admin, 'titel-2', 'peds'),
            (admin, 'titel-3', 'peds'),
            (admin, 'titel-4', 'peds'),
            (publisher, 'titel-1', 'peds'),
            (publisher, 'titel-2', 'peds'),
            (publisher, 'titel-3', 'peds'),
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
            (admin, 'titel-1', 'pedcx'),
            (admin, 'titel-2', 'pedcx'),
            (admin, 'titel-3', 'pedcx'),
            (admin, 'titel-4', 'pedcx'),
            (publisher, 'titel-1', 'pcx'),
            (publisher, 'titel-2', 'pcx'),
            (publisher, 'titel-3', 'pcx'),
            (publisher, 'titel-4', 'pcx'),
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
        publish_notice(publisher, 'titel-1')
        publish_notice(publisher, 'titel-2')
        publish_notice(publisher, 'titel-3')
        publish_notice(publisher, 'titel-4')
        check((
            (admin, 'titel-1', 'pec'),
            (admin, 'titel-2', 'pec'),
            (admin, 'titel-3', 'pec'),
            (admin, 'titel-4', 'pec'),
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

    with freeze_time("2017-11-01 11:00"):
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

    with freeze_time("2017-11-01 11:00"):
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

        # check if invalid permissions
        submit_notice(editor_1, 'titel-3', forbidden=True)
        submit_notice(editor_2, 'titel-3', forbidden=True)
        submit_notice(editor_3, 'titel-1', forbidden=True)
        submit_notice(editor_3, 'titel-2', forbidden=True)

    # check deadlines (2 gets submitted)
    with freeze_time("2017-11-08 13:00"):
        submit_notice(editor_1, 'titel-2', redirected=True)
        submit_notice(publisher, 'titel-2', redirected=True)
    with freeze_time("2017-11-01 13:00"):
        submit_notice(editor_1, 'titel-2', redirected=True)
        submit_notice(publisher, 'titel-2')

    # check invalid category (1 gets submitted)
    with freeze_time("2017-11-01 11:00"):
        change_category(gazette_app, '11', active=False)
        submit_notice(editor_1, 'titel-1', redirected=True)
        submit_notice(publisher, 'titel-1', redirected=True)

        change_category(gazette_app, '11', active=True)
        submit_notice(editor_1, 'titel-1')

    # check invalid organization (3 gets submitted)
    with freeze_time("2017-11-01 11:00"):
        change_organization(gazette_app, '200', active=False)
        submit_notice(editor_3, 'titel-3', redirected=True)
        submit_notice(publisher, 'titel-3', redirected=True)

        change_organization(gazette_app, '200', active=True)
        submit_notice(editor_3, 'titel-3')


def test_view_notice_reject(gazette_app):
    editor_1, editor_2, editor_3, publisher = login_users(gazette_app)

    with freeze_time("2017-11-01 11:00"):
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

    with freeze_time("2017-11-01 11:00"):
        # create a notice for each editor
        for count, user in enumerate((editor_1, editor_2, editor_3)):
            manage = user.get('/notices/drafted/new-notice')
            manage.form['title'] = 'Titel {}'.format(count + 1)
            manage.form['organization'] = '410'
            manage.form['category'] = '11'
            manage.form['at_cost'].select('yes')
            manage.form['billing_address'] = 'someone\nstreet\nplace'
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

    # check redirect for past issues
    with freeze_time("2017-11-04 11:00"):
        accept_notice(publisher, 'titel-1', redirected=True)

    # check redirect for invalid category
    with freeze_time("2017-11-04 11:00"):
        change_category(gazette_app, '11', active=False)
        accept_notice(publisher, 'titel-1', redirected=True)
        change_category(gazette_app, '11', active=True)

    # check redirect for invalid organization
    with freeze_time("2017-11-01 11:00"):
        change_organization(gazette_app, '410', active=False)
        accept_notice(publisher, 'titel-1', redirected=True)
        change_organization(gazette_app, '410', active=True)

    with freeze_time("2017-11-01 15:00"):
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

        message = gazette_app.smtp.outbox.pop()
        assert message['From'] == 'mails@govikon.ch'
        assert message['To'] == 'printer@onegov.org'
        assert message['Reply-To'] == 'mails@govikon.ch'
        assert '44  Titel 2' in message['Subject']
        payload = message.get_payload(1).get_payload(decode=True)
        payload = payload.decode('utf-8')
        assert '44  Titel 2' in payload
        assert "Kostenpflichtig 85% vom Normalpreis" in payload
        assert "someone<br>street<br>place" in payload

        message = gazette_app.smtp.outbox.pop()
        assert message['From'] == 'mails@govikon.ch'
        assert message['To'] == 'printer@onegov.org'
        assert message['Reply-To'] == 'mails@govikon.ch'
        assert '44  Titel 1' in message['Subject']
        payload = message.get_payload(1).get_payload(decode=True)
        payload = payload.decode('utf-8')
        assert '44  Titel 1' in payload

        principal = gazette_app.principal
        principal.publish_from = 'publisher@govikon.ch'
        gazette_app.cache.set('principal', principal)

        change_organization(gazette_app, '400', external_name='xxx')

        accept_notice(publisher, 'titel-3')

        message = gazette_app.smtp.outbox.pop()
        assert message['From'] == 'mails@govikon.ch'
        assert message['To'] == 'printer@onegov.org'
        assert message['Reply-To'] == 'publisher@govikon.ch'
        assert '44 xxx Titel 3' in message['Subject']
        payload = message.get_payload(1).get_payload(decode=True)
        payload = payload.decode('utf-8')
        assert '44 xxx Titel 3' in payload


def test_view_notice_publish(gazette_app):
    editor_1, editor_2, editor_3, publisher = login_users(gazette_app)

    with freeze_time("2017-11-01 11:00"):
        # create a notice for each editor
        for count, user in enumerate((editor_1, editor_2, editor_3)):
            manage = user.get('/notices/drafted/new-notice')
            manage.form['title'] = 'Titel {}'.format(count + 1)
            manage.form['organization'] = '410'
            manage.form['category'] = '11'
            manage.form['issues'] = ['2017-44', '2017-45']
            manage.form['text'] = "1. Oktober 2017"
            manage.form.submit()
            submit_notice(user, 'titel-{}'.format(count + 1))
            accept_notice(publisher, 'titel-{}'.format(count + 1))

    with freeze_time("2017-11-01 15:00"):
        # check if the notices can be published
        for user, slug, forbidden in (
            (editor_1, 'titel-1', True),
            (editor_1, 'titel-2', True),
            (editor_1, 'titel-3', True),
            (editor_3, 'titel-3', True),
            (publisher, 'titel-1', False),
            (publisher, 'titel-2', False),
            (publisher, 'titel-3', False),
        ):
            publish_notice(user, slug, forbidden=forbidden)


def test_view_notice_delete(gazette_app):
    with freeze_time("2017-11-01 11:00"):
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
            assert "Diese Meldung wurde bereits angenommen!" in manage
            manage.form.submit().maybe_follow()

        # delete a published notice
        manage = editor.get('/notices/drafted/new-notice')
        manage.form['title'] = "Erneuerungswahlen"
        manage.form['organization'] = '200'
        manage.form['category'] = '11'
        manage.form['issues'] = ['2017-44', '2017-45']
        manage.form['text'] = "1. Oktober 2017"
        manage.form.submit()

        submit_notice(editor, 'erneuerungswahlen')
        accept_notice(publisher, 'erneuerungswahlen')
        publish_notice(publisher, 'erneuerungswahlen')

        for user in (admin, editor, publisher):
            manage = user.get('/notice/erneuerungswahlen/delete')
            assert manage.forms == {}


def test_view_notice_changelog(gazette_app):
    editor_1 = Client(gazette_app)
    login_editor_1(editor_1)

    editor_2 = Client(gazette_app)
    login_editor_1(editor_2)

    publisher = Client(gazette_app)
    login_publisher(publisher)

    with freeze_time("2017-11-01 10:00"):
        manage = editor_1.get('/notices/drafted/new-notice')
        manage.form['title'] = "Erneuerungswahlen"
        manage.form['organization'] = '200'
        manage.form['category'] = '11'
        manage.form['issues'] = ['2017-44', '2017-45']
        manage.form['text'] = "1. Oktober 2017"
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
        publish_notice(publisher, 'erneuerungswahlen')

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
        ('01.11.2017 12:45', 'First Editor', 'TestGroup', 'bearbeitet'),
        ('01.11.2017 12:48', 'First Editor', 'TestGroup',
         'eingereicht'),
        ('01.11.2017 16:00', 'Publisher', '', 'Druck beauftragt'),
        ('01.11.2017 16:00', 'Publisher', '', 'angenommen'),
        ('01.11.2017 17:00', 'Publisher', '', 'veröffentlicht')
    ]


def test_view_notice_edit(gazette_app):
    editor_1, editor_2, editor_3, publisher = login_users(gazette_app)

    with freeze_time("2017-11-01 11:00"):
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

        # drafted
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

    publish_notice(publisher, 'notice')
    edit_notice(editor_1, 'notice', unable=True)
    edit_notice(editor_2, 'notice', unable=True)
    edit_notice(editor_3, 'notice', forbidden=True)
    edit_notice(publisher, 'notice', unable=True)


def test_view_notice_edit_deadlines(gazette_app):
    editor_1, editor_2, editor_3, publisher = login_users(gazette_app)

    with freeze_time("2017-11-01 11:00"):
        manage = editor_1.get('/notices/drafted/new-notice')
        manage.form['title'] = "Notice"
        manage.form['organization'] = '200'
        manage.form['category'] = '11'
        manage.form['issues'] = ['2017-44', '2017-45']
        manage.form['text'] = "1. Oktober 2017"
        manage.form.submit()

    marker = "Bitte Ausgaben neu wählen."
    with freeze_time("2017-11-01 11:00"):
        assert marker not in editor_1.get('/notice/notice/edit')
        assert marker not in publisher.get('/notice/notice/edit')

    with freeze_time("2017-11-01 13:00"):
        assert marker in editor_1.get('/notice/notice/edit')
        assert marker not in publisher.get('/notice/notice/edit')

    with freeze_time("2017-11-10 13:00"):
        assert marker in editor_1.get('/notice/notice/edit')
        assert marker in publisher.get('/notice/notice/edit')


def test_view_notice_edit_invalid_category(gazette_app):
    editor_1, editor_2, editor_3, publisher = login_users(gazette_app)

    with freeze_time("2017-11-01 11:00"):
        manage = editor_1.get('/notices/drafted/new-notice')
        manage.form['title'] = "Notice"
        manage.form['organization'] = '200'
        manage.form['category'] = '11'
        manage.form['issues'] = ['2017-44', '2017-45']
        manage.form['text'] = "1. Oktober 2017"
        manage.form.submit()

        marker = "Bitte Rubrik neu wählen."

        assert marker not in editor_1.get('/notice/notice/edit')

        change_category(gazette_app, '11', active=False)
        assert marker in editor_1.get('/notice/notice/edit')


def test_view_notice_edit_invalid_organization(gazette_app):
    editor_1, editor_2, editor_3, publisher = login_users(gazette_app)

    with freeze_time("2017-11-01 11:00"):
        manage = editor_1.get('/notices/drafted/new-notice')
        manage.form['title'] = "Notice"
        manage.form['organization'] = '200'
        manage.form['category'] = '11'
        manage.form['issues'] = ['2017-44', '2017-45']
        manage.form['text'] = "1. Oktober 2017"
        manage.form.submit()

        marker = "Bitte Organisation neu wählen."

        assert marker not in editor_1.get('/notice/notice/edit')

        change_organization(gazette_app, '200', active=False)
        assert marker in editor_1.get('/notice/notice/edit')


def test_view_notice_edit_unrestricted(gazette_app):
    editor_1 = Client(gazette_app)
    login_editor_1(editor_1)

    publisher = Client(gazette_app)
    login_publisher(publisher)

    admin = Client(gazette_app)
    login_admin(admin)

    then = "2017-11-01 11:00"
    future = "2020-11-01 11:00"

    with freeze_time(then):
        manage = editor_1.get('/notices/drafted/new-notice')
        manage.form['title'] = "Notice"
        manage.form['organization'] = '200'
        manage.form['category'] = '11'
        manage.form['issues'] = ['2017-44', '2017-45']
        manage.form['text'] = "1. Oktober 2017"
        manage.form.submit()

    # drafted
    with freeze_time(future):
        edit_notice_unrestricted(editor_1, 'notice', forbidden=True)
        edit_notice_unrestricted(publisher, 'notice', forbidden=True)
        edit_notice_unrestricted(admin, 'notice', title='unres_drafted')
        assert 'unres_drafted' in editor_1.get('/notice/notice')

        manage = admin.get('/notice/notice/edit_unrestricted')
        assert "(Complaints)" in manage
        assert "(Sikh Community)" in manage

    # submitted
    with freeze_time(then):
        submit_notice(editor_1, 'notice')
    with freeze_time(future):
        edit_notice_unrestricted(editor_1, 'notice', forbidden=True)
        edit_notice_unrestricted(publisher, 'notice', forbidden=True)
        edit_notice_unrestricted(admin, 'notice', title='unres_submitted')
        assert 'unres_submitted' in editor_1.get('/notice/notice')

        manage = admin.get('/notice/notice/edit_unrestricted')
        assert "(Complaints)" in manage
        assert "(Sikh Community)" in manage

    # rejected
    with freeze_time(then):
        reject_notice(publisher, 'notice')
    with freeze_time(future):
        edit_notice_unrestricted(editor_1, 'notice', forbidden=True)
        edit_notice_unrestricted(publisher, 'notice', forbidden=True)
        edit_notice_unrestricted(admin, 'notice', title='unres_rejected')
        assert 'unres_rejected' in editor_1.get('/notice/notice')

        manage = admin.get('/notice/notice/edit_unrestricted')
        assert "(Complaints)" in manage
        assert "(Sikh Community)" in manage

    # accepted
    with freeze_time(then):
        submit_notice(editor_1, 'notice')
        accept_notice(publisher, 'notice')
    with freeze_time(future):
        edit_notice_unrestricted(editor_1, 'notice', forbidden=True)
        edit_notice_unrestricted(publisher, 'notice', forbidden=True)
        edit_notice_unrestricted(admin, 'notice', title='unres_accepted')
        assert 'unres_accepted' in editor_1.get('/notice/notice')

        manage = admin.get('/notice/notice/edit_unrestricted')
        assert "(Complaints)" in manage
        assert "(Sikh Community)" in manage
        assert "Diese Meldung wurde bereits angenommen!" in manage

    with freeze_time(then):
        publish_notice(publisher, 'notice')
    with freeze_time(future):
        edit_notice_unrestricted(editor_1, 'notice', forbidden=True)
        edit_notice_unrestricted(publisher, 'notice', forbidden=True)
        edit_notice_unrestricted(admin, 'notice', title='unres_published')
        assert 'unres_published' in editor_1.get('/notice/notice')

        manage = admin.get('/notice/notice/edit_unrestricted')
        assert "(Complaints)" in manage
        assert "(Sikh Community)" in manage
        assert "Diese Meldung wurde bereits veröffentlicht!" in manage

        edit_notice_unrestricted(admin, 'notice', issues=['2017-46'])
        manage = admin.get('/notice/notice')
        assert 'Nr. 44' in manage
        assert 'Nr. 45' in manage
        assert 'Nr. 46' not in manage


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
