from freezegun import freeze_time
from onegov.gazette.models import GazetteNotice
from onegov.gazette.tests import login_admin
from onegov.gazette.tests import login_editor_1
from onegov.gazette.tests import login_editor_2
from onegov.gazette.tests import login_editor_3
from onegov.gazette.tests import login_publisher
from transaction import commit
from unittest.mock import patch
from urllib.parse import parse_qs
from urllib.parse import urlparse
from webtest import TestApp as Client
from xlrd import open_workbook


def test_view_notices(gazette_app):
    with freeze_time("2017-11-01 11:00"):

        publisher = Client(gazette_app)
        login_publisher(publisher)

        editor_1 = Client(gazette_app)
        login_editor_1(editor_1)

        editor_2 = Client(gazette_app)
        login_editor_2(editor_2)

        editor_3 = Client(gazette_app)
        login_editor_3(editor_3)

        for user in (publisher, editor_1, editor_2, editor_3):
            for state in (
                'drafted', 'submitted', 'rejected', 'accepted', 'published'
            ):
                assert "Keine Meldungen" in user.get('/notices/' + state)

        # new notices
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

        manage = editor_3.get('/notices/drafted/new-notice')
        manage.form['title'] = "Kantonsratswahlen"
        manage.form['organization'] = '200'
        manage.form['category'] = '11'
        manage.form['issues'] = ['2017-44', '2017-45']
        manage.form['text'] = "1. Oktober 2017"
        manage.form['author_place'] = 'Govikon'
        manage.form['author_name'] = 'State Chancellerist'
        manage.form['author_date'] = '2019-01-01'
        manage.form.submit()

        for user in (publisher, editor_1, editor_2, editor_3):
            for state in ('submitted', 'rejected', 'accepted', 'published'):
                assert "Keine Meldungen" in user.get('/notices/' + state)

        assert "Erneuerungswahlen" in publisher.get('/notices/drafted')
        assert "Erneuerungswahlen" in editor_1.get('/notices/drafted')
        assert "Erneuerungswahlen" in editor_2.get('/notices/drafted')
        assert "Erneuerungswahlen" not in editor_3.get('/notices/drafted')
        assert "Kantonsratswahlen" in publisher.get('/notices/drafted')
        assert "Kantonsratswahlen" not in editor_1.get('/notices/drafted')
        assert "Kantonsratswahlen" not in editor_1.get('/notices/drafted')
        assert "Kantonsratswahlen" in editor_3.get('/notices/drafted')

        # submit notices
        editor_1.get('/notice/erneuerungswahlen/submit').form.submit()
        editor_3.get('/notice/kantonsratswahlen/submit').form.submit()

        for user in (publisher, editor_1, editor_2, editor_3):
            for state in ('drafted', 'rejected', 'accepted', 'published'):
                assert "Keine Meldungen" in user.get('/notices/' + state)

        assert "Erneuerungswahlen" in publisher.get('/notices/submitted')
        assert "Erneuerungswahlen" in editor_1.get('/notices/submitted')
        assert "Erneuerungswahlen" in editor_2.get('/notices/submitted')
        assert "Erneuerungswahlen" not in editor_3.get('/notices/submitted')
        assert "Kantonsratswahlen" in publisher.get('/notices/submitted')
        assert "Kantonsratswahlen" not in editor_1.get('/notices/submitted')
        assert "Kantonsratswahlen" not in editor_2.get('/notices/submitted')
        assert "Kantonsratswahlen" in editor_3.get('/notices/submitted')

        # reject notices
        manage = publisher.get('/notice/erneuerungswahlen/reject')
        manage.form['comment'] = 'comment'
        manage.form.submit()

        manage = publisher.get('/notice/kantonsratswahlen/reject')
        manage.form['comment'] = 'comment'
        manage.form.submit()

        for user in (publisher, editor_1, editor_2, editor_3):
            for state in ('drafted', 'submitted', 'accepted', 'published'):
                assert "Keine Meldungen" in user.get('/notices/' + state)

        assert "Erneuerungswahlen" in publisher.get('/notices/rejected')
        assert "Erneuerungswahlen" in editor_1.get('/notices/rejected')
        assert "Erneuerungswahlen" in editor_2.get('/notices/rejected')
        assert "Erneuerungswahlen" not in editor_3.get('/notices/rejected')
        assert "Kantonsratswahlen" in publisher.get('/notices/rejected')
        assert "Kantonsratswahlen" not in editor_1.get('/notices/rejected')
        assert "Kantonsratswahlen" not in editor_2.get('/notices/rejected')
        assert "Kantonsratswahlen" in editor_3.get('/notices/rejected')

        # submit & accept notices
        editor_1.get('/notice/erneuerungswahlen/submit').form.submit()
        publisher.get('/notice/erneuerungswahlen/accept').form.submit()
        editor_3.get('/notice/kantonsratswahlen/submit').form.submit()
        publisher.get('/notice/kantonsratswahlen/accept').form.submit()

        for user in (publisher, editor_1, editor_2, editor_3):
            for state in ('drafted', 'submitted', 'rejected', 'published'):
                assert "Keine Meldungen" in user.get('/notices/' + state)

        assert "Erneuerungswahlen" in publisher.get('/notices/accepted')
        assert "Erneuerungswahlen" in editor_1.get('/notices/accepted')
        assert "Erneuerungswahlen" in editor_2.get('/notices/accepted')
        assert "Erneuerungswahlen" not in editor_3.get('/notices/accepted')
        assert "Kantonsratswahlen" in publisher.get('/notices/accepted')
        assert "Kantonsratswahlen" not in editor_1.get('/notices/accepted')
        assert "Kantonsratswahlen" not in editor_2.get('/notices/accepted')
        assert "Kantonsratswahlen" in editor_3.get('/notices/accepted')

        # publish notices
        assert "Erneuerungswahlen" in publisher.get('/notices/accepted')
        assert "Erneuerungswahlen" in editor_1.get('/notices/accepted')
        assert "Erneuerungswahlen" in editor_2.get('/notices/accepted')
        assert "Erneuerungswahlen" not in editor_3.get('/notices/accepted')
        assert "Kantonsratswahlen" in publisher.get('/notices/accepted')
        assert "Kantonsratswahlen" not in editor_1.get('/notices/accepted')
        assert "Kantonsratswahlen" not in editor_2.get('/notices/accepted')
        assert "Kantonsratswahlen" in editor_3.get('/notices/accepted')


def test_view_notices_search(gazette_app):
    with freeze_time("2017-11-01 11:00"):

        client = Client(gazette_app)
        login_publisher(client)

        # new notice
        manage = client.get('/notices/drafted/new-notice')
        manage.form['title'] = "Erneuerungswahlen"
        manage.form['organization'] = '200'
        manage.form['category'] = '11'
        manage.form['issues'] = ['2017-44', '2017-45']
        manage.form['text'] = "1. Oktober 2017"
        manage.form['author_place'] = 'Govikon'
        manage.form['author_name'] = 'State Chancellerist'
        manage.form['author_date'] = '2019-01-01'
        manage.form.submit()
        client.get('/notice/erneuerungswahlen/submit').form.submit()
        client.get('/notice/erneuerungswahlen/accept').form.submit()

        manage = client.get('/notices/drafted/new-notice')
        manage.form['title'] = "Kantonsratswahlen"
        manage.form['organization'] = '200'
        manage.form['category'] = '11'
        manage.form['issues'] = ['2017-44', '2017-45']
        manage.form['text'] = "10. Oktober 2017"
        manage.form['author_place'] = 'Govikon'
        manage.form['author_name'] = 'State Chancellerist'
        manage.form['author_date'] = '2019-01-01'
        manage.form.submit()
        client.get('/notice/kantonsratswahlen/submit').form.submit()
        client.get('/notice/kantonsratswahlen/accept').form.submit()

        assert "Erneuerungswahlen" in client.get('/notices/accepted')
        assert "Kantonsratswahlen" in client.get('/notices/accepted')

        url = '/notices/accepted?term={}'

        assert "Erneuerung" in client.get(url.format('wahlen'))
        assert "Kantonsrat" in client.get(url.format('wahlen'))

        assert "Erneuerung" not in client.get(url.format('10.+Oktober'))
        assert "Kantonsrat" in client.get(url.format('10.+Oktober'))

        assert "Erneuerung" in client.get(url.format('neuerun'))
        assert "Kantonsrat" not in client.get(url.format('neuerun'))


def test_view_notices_order(gazette_app):

    def get_items(page):
        return [a.text for a in page.pyquery('td strong a')]

    def get_ordering(page):
        return {
            r['order'][0]: r['direction'][0]
            for r in [
                parse_qs(urlparse(a.attrib['href']).query)
                for a in page.pyquery('th a')
            ]
        }

    with freeze_time("2017-11-01 11:00"):

        client = Client(gazette_app)
        login_publisher(client)

        # new notice
        manage = client.get('/notices/drafted/new-notice')
        manage.form['title'] = "Erneuerungswahlen"
        manage.form['organization'] = '100'
        manage.form['category'] = '11'
        manage.form['issues'] = ['2017-44', '2017-46']
        manage.form['text'] = "1. Oktober 2017"
        manage.form['author_place'] = 'Govikon'
        manage.form['author_name'] = 'State Chancellerist'
        manage.form['author_date'] = '2019-01-01'
        manage.form.submit()
        client.get('/notice/erneuerungswahlen/submit').form.submit()
        client.get('/notice/erneuerungswahlen/accept').form.submit()

        manage = client.get('/notices/drafted/new-notice')
        manage.form['title'] = "Kantonsratswahlen"
        manage.form['organization'] = '200'
        manage.form['category'] = '13'
        manage.form['issues'] = ['2017-45', '2017-47']
        manage.form['text'] = "10. Oktober 2017"
        manage.form['author_place'] = 'Govikon'
        manage.form['author_name'] = 'State Chancellerist'
        manage.form['author_date'] = '2019-01-01'
        manage.form.submit()
        client.get('/notice/kantonsratswahlen/submit').form.submit()
        client.get('/notice/kantonsratswahlen/accept').form.submit()

        # Default sorting
        ordered = client.get('/notices/accepted')
        assert get_items(ordered) == ["Erneuerungswahlen", "Kantonsratswahlen"]
        assert get_ordering(client.get('/notices/accepted')) == {
            'title': 'asc',
            'organization': 'asc',
            'category': 'asc',
            'group.name': 'asc',
            'user.name': 'asc',
            'first_issue': 'desc'
        }

        # Invalid sorting
        ordered = client.get('/notices/accepted?order=xxx')
        assert get_items(ordered) == ["Erneuerungswahlen", "Kantonsratswahlen"]
        assert get_ordering(client.get('/notices/accepted')) == {
            'title': 'asc',
            'organization': 'asc',
            'category': 'asc',
            'group.name': 'asc',
            'user.name': 'asc',
            'first_issue': 'desc'
        }

        # Omit direction
        ordered = client.get('/notices/accepted?order=category')
        assert get_items(ordered) == ["Kantonsratswahlen", "Erneuerungswahlen"]
        assert get_ordering(ordered) == {
            'title': 'asc',
            'organization': 'asc',
            'category': 'desc',
            'group.name': 'asc',
            'user.name': 'asc',
            'first_issue': 'asc'
        }

        # Sort by
        # ... title
        url = '/notices/accepted?order={}&direction={}'
        ordered = client.get(url.format('title', 'asc'))
        assert get_items(ordered) == ["Erneuerungswahlen", "Kantonsratswahlen"]
        assert get_ordering(ordered) == {
            'title': 'desc',
            'organization': 'asc',
            'category': 'asc',
            'group.name': 'asc',
            'user.name': 'asc',
            'first_issue': 'asc'
        }

        ordered = client.get(url.format('title', 'desc'))
        assert get_items(ordered) == ["Kantonsratswahlen", "Erneuerungswahlen"]
        assert get_ordering(ordered) == {
            'title': 'asc',
            'organization': 'asc',
            'category': 'asc',
            'group.name': 'asc',
            'user.name': 'asc',
            'first_issue': 'asc'
        }

        # ... organization
        ordered = client.get(url.format('organization', 'asc'))
        assert get_items(ordered) == ["Kantonsratswahlen", "Erneuerungswahlen"]
        assert get_ordering(ordered) == {
            'title': 'asc',
            'organization': 'desc',
            'category': 'asc',
            'group.name': 'asc',
            'user.name': 'asc',
            'first_issue': 'asc'
        }

        ordered = client.get(url.format('organization', 'desc'))
        assert get_items(ordered) == ["Erneuerungswahlen", "Kantonsratswahlen"]
        assert get_ordering(ordered) == {
            'title': 'asc',
            'organization': 'asc',
            'category': 'asc',
            'group.name': 'asc',
            'user.name': 'asc',
            'first_issue': 'asc'
        }

        # ... category
        ordered = client.get(url.format('category', 'asc'))
        assert get_items(ordered) == ["Kantonsratswahlen", "Erneuerungswahlen"]
        assert get_ordering(ordered) == {
            'title': 'asc',
            'organization': 'asc',
            'category': 'desc',
            'group.name': 'asc',
            'user.name': 'asc',
            'first_issue': 'asc'
        }

        ordered = client.get(url.format('category', 'desc'))
        assert get_items(ordered) == ["Erneuerungswahlen", "Kantonsratswahlen"]
        assert get_ordering(ordered) == {
            'title': 'asc',
            'organization': 'asc',
            'category': 'asc',
            'group.name': 'asc',
            'user.name': 'asc',
            'first_issue': 'asc'
        }

        # ... group
        ordered = client.get(url.format('group.name', 'asc'))
        assert get_ordering(ordered) == {
            'title': 'asc',
            'organization': 'asc',
            'category': 'asc',
            'group.name': 'desc',
            'user.name': 'asc',
            'first_issue': 'asc'
        }

        ordered = client.get(url.format('category', 'desc'))
        assert get_ordering(ordered) == {
            'title': 'asc',
            'organization': 'asc',
            'category': 'asc',
            'group.name': 'asc',
            'user.name': 'asc',
            'first_issue': 'asc'
        }

        # ... user
        ordered = client.get(url.format('user.name', 'asc'))
        assert get_ordering(ordered) == {
            'title': 'asc',
            'organization': 'asc',
            'category': 'asc',
            'group.name': 'asc',
            'user.name': 'desc',
            'first_issue': 'asc'
        }

        ordered = client.get(url.format('category', 'desc'))
        assert get_items(ordered) == ["Erneuerungswahlen", "Kantonsratswahlen"]
        assert get_ordering(ordered) == {
            'title': 'asc',
            'organization': 'asc',
            'category': 'asc',
            'group.name': 'asc',
            'user.name': 'asc',
            'first_issue': 'asc'
        }

        # ... issues
        ordered = client.get(url.format('first_issue', 'asc'))
        assert get_items(ordered) == ["Erneuerungswahlen", "Kantonsratswahlen"]
        assert get_ordering(ordered) == {
            'title': 'asc',
            'organization': 'asc',
            'category': 'asc',
            'group.name': 'asc',
            'user.name': 'asc',
            'first_issue': 'desc'
        }

        ordered = client.get(url.format('first_issue', 'desc'))
        assert get_items(ordered) == ["Kantonsratswahlen", "Erneuerungswahlen"]
        assert get_ordering(ordered) == {
            'title': 'asc',
            'organization': 'asc',
            'category': 'asc',
            'group.name': 'asc',
            'user.name': 'asc',
            'first_issue': 'asc'
        }


def test_view_notices_statistics(gazette_app):

    editor = Client(gazette_app)
    login_editor_3(editor)  # this has no group

    publisher = Client(gazette_app)
    login_publisher(publisher)

    def statistic(state, sheet_name, qs=None):
        result = publisher.get(
            '/notices/{}/statistics-xlsx?{}'.format(state, qs or '')
        )
        book = open_workbook(file_contents=result.body)
        for sheet in book.sheets():
            if sheet.name == sheet_name:
                return [
                    [sheet.cell(row, col).value for col in range(sheet.ncols)]
                    for row in range(sheet.nrows)
                ]

    # No notices yet
    states = ('drafted', 'submitted', 'accepted', 'rejected')
    for s in states:
        editor.get('/notices/{}/statistics'.format(s), status=403)
        editor.get('/notices/{}/statistics-xlsx'.format(s), status=403)

        publisher.get('/notices/{}/statistics'.format(s))

        assert statistic(s, 'Organisationen') == [['Organisation', 'Anzahl']]
        assert statistic(s, 'Rubriken') == [['Rubrik', 'Anzahl']]
        assert statistic(s, 'Gruppen') == [['Gruppe', 'Anzahl']]

    # Add users and groups
    admin = Client(gazette_app)
    login_admin(admin)
    manage = admin.get('/groups').click("Neu")
    for group in ('A', 'B', 'C'):
        manage.form['name'] = group
        manage.form.submit()

    manage = admin.get('/users').click("Neu")
    for user, group in (
        ('a@example.com', 'B'),
        ('b@example.com', 'B'),
        ('c@example.com', 'C'),
    ):
        manage.form['role'] = 'member'
        manage.form['name'] = user
        manage.form['username'] = user
        manage.form['group'] = dict(
            (x[2], x[0]) for x in manage.form['group'].options
        )[group]
        with patch('onegov.gazette.views.users.random_password') as password:
            password.return_value = 'hunter2'
            manage.form.submit().maybe_follow()

    user_1 = Client(gazette_app)
    user_2 = Client(gazette_app)
    user_3 = Client(gazette_app)
    for user, client in (
        ('a@example.com', user_1),
        ('b@example.com', user_2),
        ('c@example.com', user_3),
    ):
        login = client.get('/auth/login')
        login.form['username'] = user
        login.form['password'] = 'hunter2'
        login.form.submit()

    # Add notices
    with freeze_time("2017-11-01 11:00"):
        for (organization, category, submit, user, issues) in (
            ('100', '13', False, editor, ['2017-44']),
            ('100', '13', False, user_1, ['2017-45']),
            ('100', '11', False, user_1, ['2017-46']),
            ('200', '11', False, user_1, ['2017-47']),
            ('100', '12', True, user_1, ['2017-47', '2017-45']),
            ('100', '14', True, user_1, ['2017-45', '2017-46']),
            ('300', '14', True, user_1, ['2017-46']),
            ('100', '11', False, user_2, ['2017-47']),
            ('100', '12', True, user_2, ['2017-47']),
            ('200', '14', False, user_2, ['2017-45', '2017-47']),
            ('100', '14', True, user_3, ['2017-46']),
            ('100', '12', True, user_3, ['2017-47']),
            ('100', '14', False, user_3, ['2017-47']),
            ('100', '14', True, user_3, ['2017-45', '2017-46', '2017-47']),
        ):
            manage = user.get('/notices/drafted/new-notice')
            manage.form['title'] = "Titel"
            manage.form['organization'] = organization
            manage.form['category'] = category
            manage.form['text'] = "Text"
            manage.form['author_place'] = 'Govikon'
            manage.form['author_name'] = 'State Chancellerist'
            manage.form['author_date'] = '2019-01-01'
            manage.form['issues'] = issues
            manage = manage.form.submit().maybe_follow()
            if submit:
                manage.click("Einreichen").form.submit()

    for s in ('rejected', 'accepted'):
        assert statistic(s, 'Organisationen') == [['Organisation', 'Anzahl']]
        assert statistic(s, 'Rubriken') == [['Rubrik', 'Anzahl']]
        assert statistic(s, 'Gruppen') == [['Gruppe', 'Anzahl']]

    assert publisher.get('/notices/drafted/statistics')
    assert publisher.get('/notices/submitted/statistics')
    assert publisher.get('/notices/published/statistics')

    # organizations/drafted: 5 x 100, 3 x 200
    assert statistic('drafted', 'Organisationen') == [
        ['Organisation', 'Anzahl'],
        ['Civic Community', 3],
        ['State Chancellery', 5]
    ]

    # organizations/submitted: 10 x 100, 1 x 300
    assert statistic('submitted', 'Organisationen') == [
        ['Organisation', 'Anzahl'],
        ['Municipality', 1],
        ['State Chancellery', 10],
    ]

    # organizations/submitted/2017-45/46: 6 x 100, 1 x 300
    assert statistic(
        'submitted', 'Organisationen',
        'from_date=2017-11-10&to_date=2017-11-17'
    ) == [
        ['Organisation', 'Anzahl'],
        ['Municipality', 1],
        ['State Chancellery', 6],
    ]

    # categories/drafted: 3 x 11, 2 x 13, 3 x 14
    assert statistic('drafted', 'Rubriken') == [
        ['Rubrik', 'Anzahl'],
        ['Commercial Register', 2],
        ['Education', 3],
        ['Elections', 3],
    ]

    # categories/submitted: 4 x 12, 7 x 14
    assert statistic('submitted', 'Rubriken') == [
        ['Rubrik', 'Anzahl'],
        ['Elections', 7],
        ['Submissions', 4],
    ]

    # categories/submitted/2017-45/46: 1 x 12, 6 x 14
    assert statistic(
        'submitted', 'Rubriken',
        'from_date=2017-11-10&to_date=2017-11-17'
    ) == [
        ['Rubrik', 'Anzahl'],
        ['Elections', 6],
        ['Submissions', 1],
    ]

    # groups/drafted: 1 x w/o, 6 x B, 1 x C
    assert '>5</td>' in publisher.get('/notices/drafted/statistics')
    assert statistic('drafted', 'Gruppen') == [
        ['Gruppe', 'Anzahl'],
        ['B', 6],
        ['C', 1],
    ]

    # groups/submitted: 6 x B, 5 x C
    assert '>4</td>' in publisher.get('/notices/submitted/statistics')
    assert statistic('submitted', 'Gruppen') == [
        ['Gruppe', 'Anzahl'],
        ['B', 6],
        ['C', 5],
    ]

    # groups/submitted/2017-45/46: 4 x B, 3 x C
    assert statistic(
        'submitted', 'Gruppen',
        'from_date=2017-11-10&to_date=2017-11-17'
    ) == [
        ['Gruppe', 'Anzahl'],
        ['B', 4],
        ['C', 3],
    ]


def test_view_notices_update(gazette_app):
    with freeze_time("2017-11-01 11:00"):

        client = Client(gazette_app)
        login_publisher(client)

        # Add a notice
        manage = client.get('/notices/drafted/new-notice')
        manage.form['title'] = "Erneuerungswahlen"
        manage.form['organization'] = '100'
        manage.form['category'] = '11'
        manage.form['issues'] = ['2017-44', '2017-46']
        manage.form['text'] = "1. Oktober 2017"
        manage.form['author_place'] = 'Govikon'
        manage.form['author_name'] = 'State Chancellerist'
        manage.form['author_date'] = '2019-01-01'
        manage.form.submit()
        client.get('/notice/erneuerungswahlen/submit').form.submit()
        client.get('/notice/erneuerungswahlen/accept').form.submit()

        manage = client.get('/notice/erneuerungswahlen')
        assert 'State Chancellery' in manage
        assert 'Education' in manage

        # Change the category and organization of the notice
        # (don't change the category or organization because of the observers!)
        session = gazette_app.session()
        notice = session.query(GazetteNotice).one()
        notice.category = 'Edurcatio'
        notice.organization = 'Sate Chancelery'
        commit()

        manage = client.get('/notice/erneuerungswahlen')
        assert 'Education' not in manage
        assert 'Edurcatio' in manage
        assert 'State Chancellery' not in manage
        assert 'Sate Chancelery' in manage

        # Update all notices
        manage = client.get('/notices/submitted/update')
        manage = manage.form.submit().maybe_follow()
        assert "Meldungen aktualisiert." in manage

        manage = client.get('/notice/erneuerungswahlen')
        assert 'Education' not in manage
        assert 'Edurcatio' in manage
        assert 'State Chancellery' not in manage
        assert 'Sate Chancelery' in manage

        manage = client.get('/notices/accepted/update')
        manage = manage.form.submit().maybe_follow()
        assert "Meldungen aktualisiert." in manage

        manage = client.get('/notice/erneuerungswahlen')
        assert 'Education' in manage
        assert 'Edurcatio' not in manage
        assert 'State Chancellery' in manage
        assert 'Sate Chancelery' not in manage
