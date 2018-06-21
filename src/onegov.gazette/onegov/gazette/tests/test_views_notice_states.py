from freezegun import freeze_time
from onegov.gazette.tests.common import accept_notice
from onegov.gazette.tests.common import change_category
from onegov.gazette.tests.common import change_organization
from onegov.gazette.tests.common import edit_notice
from onegov.gazette.tests.common import login_users
from onegov.gazette.tests.common import reject_notice
from onegov.gazette.tests.common import submit_notice


def test_view_notice_submit(gazette_app):
    admin, editor_1, editor_2, editor_3, publisher = login_users(gazette_app)

    with freeze_time("2017-11-01 11:00"):
        # create a notice for each editor
        for count, user in enumerate((editor_1, editor_2, editor_3)):
            manage = user.get('/notices/drafted/new-notice')
            manage.form['title'] = 'Titel {}'.format(count + 1)
            manage.form['organization'] = '200'
            manage.form['category'] = '11'
            manage.form['issues'] = ['2017-44', '2017-45']
            manage.form['text'] = "1. Oktober 2017"
            manage.form['author_place'] = 'Govikon'
            manage.form['author_name'] = 'State Chancellerist'
            manage.form['author_date'] = '2019-01-01'
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
    admin, editor_1, editor_2, editor_3, publisher = login_users(gazette_app)

    with freeze_time("2017-11-01 11:00"):
        # create a notice for each editor
        for count, user in enumerate((editor_1, editor_2, editor_3)):
            manage = user.get('/notices/drafted/new-notice')
            manage.form['title'] = 'Titel {}'.format(count + 1)
            manage.form['organization'] = '200'
            manage.form['category'] = '11'
            manage.form['issues'] = ['2017-44', '2017-45']
            manage.form['text'] = "1. Oktober 2017"
            manage.form['author_place'] = 'Govikon'
            manage.form['author_name'] = 'State Chancellerist'
            manage.form['author_date'] = '2019-01-01'
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
    admin, editor_1, editor_2, editor_3, publisher = login_users(gazette_app)

    with freeze_time("2017-11-01 11:00"):
        # create a notice for each editor
        for count, user in enumerate((editor_1, editor_2, editor_3, editor_3)):
            manage = user.get('/notices/drafted/new-notice')
            manage.form['title'] = 'Titel {}'.format(count + 1)
            manage.form['organization'] = '410'
            manage.form['category'] = '11'
            manage.form['at_cost'].select('no')
            manage.form['billing_address'] = 'someone\nstreet\nplace'
            manage.form['issues'] = ['2017-44', '2017-45']
            manage.form['text'] = "1. Oktober 2017"
            manage.form['author_place'] = 'Govikon'
            manage.form['author_name'] = 'State Chancellerist'
            manage.form['author_date'] = '2019-01-01'
            manage.form.submit()
            submit_notice(user, 'titel-{}'.format(count + 1))

        edit_notice(publisher, 'titel-1', print_only=True, at_cost='yes')
        edit_notice(publisher, 'titel-2', at_cost='yes')

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
            (publisher, 'titel-3', False),
        ):
            accept_notice(user, slug, forbidden=forbidden)

        message = gazette_app.smtp.outbox.pop()
        assert message['From'] == 'mails@govikon.ch'
        assert message['To'] == 'printer@onegov.org'
        assert message['Reply-To'] == 'mails@govikon.ch'
        assert message['Subject'].startswith('44  Titel 3')
        payload = message.get_payload(1).get_payload(decode=True)
        payload = payload.decode('utf-8')
        assert '44  Titel 3' in payload
        assert "Govikon, 1. Januar 2019" in payload
        assert "State Chancellerist" in payload
        assert "someone<br>street<br>place" not in payload

        message = gazette_app.smtp.outbox.pop()
        assert message['From'] == 'mails@govikon.ch'
        assert message['To'] == 'printer@onegov.org'
        assert message['Reply-To'] == 'mails@govikon.ch'
        assert message['Subject'].startswith('Kostenpflichtig - 44  Titel 2')
        payload = message.get_payload(1).get_payload(decode=True)
        payload = payload.decode('utf-8')
        assert '44  Titel 2' in payload
        assert "Govikon, 1. Januar 2019" in payload
        assert "State Chancellerist" in payload
        assert "someone<br>street<br>place" in payload

        message = gazette_app.smtp.outbox.pop()
        assert message['From'] == 'mails@govikon.ch'
        assert message['To'] == 'printer@onegov.org'
        assert message['Reply-To'] == 'mails@govikon.ch'
        assert message['Subject'].startswith(
            'Kostenpflichtig / Stopp Internet - 44  Titel 1'
        )
        payload = message.get_payload(1).get_payload(decode=True)
        payload = payload.decode('utf-8')
        assert '44  Titel 1' in payload

        principal = gazette_app.principal
        principal.on_accept['mail_from'] = 'publisher@govikon.ch'
        gazette_app.cache.set('principal', principal)

        change_organization(gazette_app, '400', external_name='xxx')

        accept_notice(publisher, 'titel-4')

        message = gazette_app.smtp.outbox.pop()
        assert message['From'] == 'mails@govikon.ch'
        assert message['To'] == 'printer@onegov.org'
        assert message['Reply-To'] == 'publisher@govikon.ch'
        assert '44 xxx Titel 4' in message['Subject']
        payload = message.get_payload(1).get_payload(decode=True)
        payload = payload.decode('utf-8')
        assert '44 xxx Titel 4' in payload
