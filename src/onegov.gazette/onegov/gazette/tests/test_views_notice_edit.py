from freezegun import freeze_time
from onegov.gazette.tests.common import accept_notice
from onegov.gazette.tests.common import change_category
from onegov.gazette.tests.common import change_organization
from onegov.gazette.tests.common import edit_notice
from onegov.gazette.tests.common import edit_notice_unrestricted
from onegov.gazette.tests.common import login_users
from onegov.gazette.tests.common import reject_notice
from onegov.gazette.tests.common import submit_notice


def test_view_notice_edit(gazette_app):
    admin, editor_1, editor_2, editor_3, publisher = login_users(gazette_app)

    with freeze_time("2017-11-01 11:00"):
        manage = editor_1.get('/notices/drafted/new-notice')

        assert manage.form['phone_number'].value == '+41415112271'

        manage.form['title'] = "Notice"
        manage.form['organization'] = '200'
        manage.form['category'] = '11'
        manage.form['issues'] = ['2017-44', '2017-45']
        manage.form['text'] = "1. Oktober 2017"
        manage.form['author_place'] = 'Govikon'
        manage.form['author_name'] = 'State Chancellerist'
        manage.form['author_date'] = '2019-01-01'
        manage.form['phone_number'].value == '+41415112281'
        manage.form.submit()

        edit_notice(
            editor_1, 'notice',
            title="Kantonsratswahl",
            organization='300',
            category='12',
            issues=['2017-46'],
            text="1. Dezember 2017",
            phone_number='+41415112291'
        )
        view = editor_1.get('/notice/notice')
        assert "Kantonsratswahl" in view
        assert "Municipality" in view
        assert "Submissions" in view
        assert "Nr. 46, 17.11.2017" in view
        assert "1. Dezember 2017" in view
        assert "+41415112291" in view
        assert '+41415112291' in admin.get('/user/editor1%40example.org/edit')

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


def test_view_notice_edit_deadlines(gazette_app):
    admin, editor_1, editor_2, editor_3, publisher = login_users(gazette_app)

    with freeze_time("2017-11-01 11:00"):
        manage = editor_1.get('/notices/drafted/new-notice')
        manage.form['title'] = "Notice"
        manage.form['organization'] = '200'
        manage.form['category'] = '11'
        manage.form['issues'] = ['2017-44', '2017-45']
        manage.form['text'] = "1. Oktober 2017"
        manage.form['author_place'] = 'Govikon'
        manage.form['author_name'] = 'State Chancellerist'
        manage.form['author_date'] = '2019-01-01'
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
    admin, editor_1, editor_2, editor_3, publisher = login_users(gazette_app)

    with freeze_time("2017-11-01 11:00"):
        manage = editor_1.get('/notices/drafted/new-notice')
        manage.form['title'] = "Notice"
        manage.form['organization'] = '200'
        manage.form['category'] = '11'
        manage.form['issues'] = ['2017-44', '2017-45']
        manage.form['text'] = "1. Oktober 2017"
        manage.form['author_place'] = 'Govikon'
        manage.form['author_name'] = 'State Chancellerist'
        manage.form['author_date'] = '2019-01-01'
        manage.form.submit()

        marker = "Bitte Rubrik neu wählen."

        assert marker not in editor_1.get('/notice/notice/edit')

        change_category(gazette_app, '11', active=False)
        assert marker in editor_1.get('/notice/notice/edit')


def test_view_notice_edit_invalid_organization(gazette_app):
    admin, editor_1, editor_2, editor_3, publisher = login_users(gazette_app)

    with freeze_time("2017-11-01 11:00"):
        manage = editor_1.get('/notices/drafted/new-notice')
        manage.form['title'] = "Notice"
        manage.form['organization'] = '200'
        manage.form['category'] = '11'
        manage.form['issues'] = ['2017-44', '2017-45']
        manage.form['text'] = "1. Oktober 2017"
        manage.form['author_place'] = 'Govikon'
        manage.form['author_name'] = 'State Chancellerist'
        manage.form['author_date'] = '2019-01-01'
        manage.form.submit()

        marker = "Bitte Organisation neu wählen."

        assert marker not in editor_1.get('/notice/notice/edit')

        change_organization(gazette_app, '200', active=False)
        assert marker in editor_1.get('/notice/notice/edit')


def test_view_notice_edit_unrestricted(gazette_app):
    admin, editor_1, editor_2, editor_3, publisher = login_users(gazette_app)

    then = "2017-11-01 11:00"
    future = "2020-11-01 11:00"

    with freeze_time(then):
        manage = editor_1.get('/notices/drafted/new-notice')

        assert manage.form['phone_number'].value == '+41415112271'

        manage.form['title'] = "Notice"
        manage.form['organization'] = '200'
        manage.form['category'] = '11'
        manage.form['issues'] = ['2017-44', '2017-45']
        manage.form['text'] = "1. Oktober 2017"
        manage.form['author_place'] = 'Govikon'
        manage.form['author_name'] = 'State Chancellerist'
        manage.form['author_date'] = '2019-01-01'
        manage.form['phone_number'].value == '+41415112281'
        manage.form.submit()

    # drafted
    with freeze_time(future):
        edit_notice_unrestricted(editor_1, 'notice', forbidden=True)
        edit_notice_unrestricted(publisher, 'notice', title='unres_drafted')
        edit_notice_unrestricted(admin, 'notice', phone_number='+41415112291')
        notice = editor_1.get('/notice/notice')
        assert 'unres_drafted' in notice
        assert '+41415112291' in notice
        assert '+41415112291' in admin.get('/user/editor1%40example.org/edit')

        manage = admin.get('/notice/notice/edit-unrestricted')
        assert "(Complaints)" in manage
        assert "(Sikh Community)" in manage

    # submitted
    with freeze_time(then):
        submit_notice(editor_1, 'notice')
    with freeze_time(future):
        edit_notice_unrestricted(editor_1, 'notice', forbidden=True)
        edit_notice_unrestricted(publisher, 'notice', author_name='Somebody')
        edit_notice_unrestricted(admin, 'notice', title='unres_submitted')
        notice = editor_1.get('/notice/notice')
        assert 'Somebody' in notice
        assert 'unres_submitted' in notice

        for user in (publisher, admin):
            manage = user.get('/notice/notice/edit-unrestricted')
            assert "(Complaints)" in manage
            assert "(Sikh Community)" in manage

    # rejected
    with freeze_time(then):
        reject_notice(publisher, 'notice')
    with freeze_time(future):
        edit_notice_unrestricted(editor_1, 'notice', forbidden=True)
        edit_notice_unrestricted(publisher, 'notice', author_name='Someone')
        edit_notice_unrestricted(admin, 'notice', title='unres_rejected')
        notice = editor_1.get('/notice/notice')
        assert 'Someone' in notice
        assert 'unres_rejected' in notice

        for user in (publisher, admin):
            manage = user.get('/notice/notice/edit-unrestricted')
            assert "(Complaints)" in manage
            assert "(Sikh Community)" in manage

    # accepted
    with freeze_time(then):
        submit_notice(editor_1, 'notice')
        accept_notice(publisher, 'notice')
    with freeze_time(future):
        edit_notice_unrestricted(editor_1, 'notice', forbidden=True)
        edit_notice_unrestricted(publisher, 'notice', author_name='No one')
        edit_notice_unrestricted(admin, 'notice', title='unres_accepted')
        notice = editor_1.get('/notice/notice')
        assert 'No one' in notice
        assert 'unres_accepted' in notice

        for user in (publisher, admin):
            manage = user.get('/notice/notice/edit-unrestricted')
            assert "(Complaints)" in manage
            assert "(Sikh Community)" in manage
            assert "Diese Meldung wurde bereits angenommen!" in manage
