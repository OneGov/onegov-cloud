from freezegun import freeze_time
from onegov.gazette.tests import login_admin
from onegov.gazette.tests import login_editor
from onegov.gazette.tests import login_publisher
from unittest.mock import patch
from webtest import TestApp as Client


def test_view_notices(gazette_app):
    with freeze_time("2017-11-01 12:00"):

        client = Client(gazette_app)
        login_publisher(client)

        editor = Client(gazette_app)
        login_editor(editor)

        assert "Keine amtlichen Meldungen" in client.get('/notices/drafted')
        assert "Keine amtlichen Meldungen" in client.get('/notices/submitted')
        assert "Keine amtlichen Meldungen" in client.get('/notices/rejected')
        assert "Keine amtlichen Meldungen" in client.get('/notices/published')

        # new notice
        manage = client.get('/notices/drafted/new-notice')
        manage.form['title'] = "Erneuerungswahlen"
        manage.form['organization'] = '210'
        manage.form['category'] = '1403'
        manage.form['issues'] = ['2017-44', '2017-45']
        manage.form['text'] = "1. Oktober 2017"
        manage.form.submit()

        assert "Erneuerungswahlen" in client.get('/notices/drafted')
        assert "Keine amtlichen Meldungen" in client.get('/notices/submitted')
        assert "Keine amtlichen Meldungen" in client.get('/notices/rejected')
        assert "Keine amtlichen Meldungen" in client.get('/notices/published')

        assert "Keine amtlichen Meldungen" in editor.get('/notices/drafted')

        # submit notice
        client.get('/notice/erneuerungswahlen/submit').form.submit()

        assert "Keine amtlichen Meldungen" in client.get('/notices/drafted')
        assert "Erneuerungswahlen" in client.get('/notices/submitted')
        assert "Keine amtlichen Meldungen" in client.get('/notices/rejected')
        assert "Keine amtlichen Meldungen" in client.get('/notices/published')

        assert "Keine amtlichen Meldungen" in editor.get('/notices/submitted')

        # reject notice
        manage = client.get('/notice/erneuerungswahlen/reject')
        manage.form['comment'] = 'comment'
        manage.form.submit()
        assert "Keine amtlichen Meldungen" in client.get('/notices/drafted')
        assert "Keine amtlichen Meldungen" in client.get('/notices/submitted')
        assert "Erneuerungswahlen" in client.get('/notices/rejected')
        assert "Keine amtlichen Meldungen" in client.get('/notices/published')

        assert "Keine amtlichen Meldungen" in editor.get('/notices/rejected')

        # submit & publish notice
        client.get('/notice/erneuerungswahlen/submit').form.submit()
        client.get('/notice/erneuerungswahlen/publish').form.submit()

        assert "Keine amtlichen Meldungen" in client.get('/notices/drafted')
        assert "Keine amtlichen Meldungen" in client.get('/notices/submitted')
        assert "Keine amtlichen Meldungen" in client.get('/notices/rejected')
        assert "Erneuerungswahlen" in client.get('/notices/published')

        assert "Keine amtlichen Meldungen" in editor.get('/notices/published')


def test_view_notices_search(gazette_app):
    with freeze_time("2017-11-01 12:00"):

        client = Client(gazette_app)
        login_publisher(client)

        # new notice
        manage = client.get('/notices/drafted/new-notice')
        manage.form['title'] = "Erneuerungswahlen"
        manage.form['organization'] = '210'
        manage.form['category'] = '1403'
        manage.form['issues'] = ['2017-44', '2017-45']
        manage.form['text'] = "1. Oktober 2017"
        manage.form.submit()
        client.get('/notice/erneuerungswahlen/submit').form.submit()
        client.get('/notice/erneuerungswahlen/publish').form.submit()

        manage = client.get('/notices/drafted/new-notice')
        manage.form['title'] = "Kantonsratswahlen"
        manage.form['organization'] = '210'
        manage.form['category'] = '1403'
        manage.form['issues'] = ['2017-44', '2017-45']
        manage.form['text'] = "10. Oktober 2017"
        manage.form.submit()
        client.get('/notice/kantonsratswahlen/submit').form.submit()
        client.get('/notice/kantonsratswahlen/publish').form.submit()

        assert "Erneuerungswahlen" in client.get('/notices/published')
        assert "Kantonsratswahlen" in client.get('/notices/published')

        url = '/notices/published?term={}'

        assert "Erneuerung" in client.get(url.format('wahlen'))
        assert "Kantonsrat" in client.get(url.format('wahlen'))

        assert "Erneuerung" not in client.get(url.format('10.+Oktober'))
        assert "Kantonsrat" in client.get(url.format('10.+Oktober'))

        assert "Erneuerung" in client.get(url.format('neuerun'))
        assert "Kantonsrat" not in client.get(url.format('neuerun'))


def test_view_notices_statistics(gazette_app):

    editor = Client(gazette_app)
    login_editor(editor)

    publisher = Client(gazette_app)
    login_publisher(publisher)

    url_organizations = '/notices/{}/statistics-organizations'
    url_categories = '/notices/{}/statistics-categories'
    url_groups = '/notices/{}/statistics-groups'

    # No notices yet
    states = ('drafted', 'submitted', 'published', 'rejected')
    for s in states:
        editor.get('/notices/{}/statistics'.format(s), status=403)
        editor.get('/notices/{}/statistics-groups'.format(s), status=403)
        editor.get('/notices/{}/statistics-categories'.format(s), status=403)

        publisher.get('/notices/{}/statistics'.format(s))
        assert publisher.get(url_organizations.format(s)).text == (
            'Organisation,Anzahl\r\n'
            'Staatskanzlei Kanton Zug,0\r\n'
            'Bürgergemeinde Zug,0\r\n'
            'Einwohnergemeinde Zug,0\r\n'
            'Evangelisch-reformierte Kirchgemeinde des Kantons Zug,0\r\n'
            'Katholische Kirchgemeinde Baar,0\r\n'
            'Katholische Kirchgemeinde Zug,0\r\n'
            'Korporation Zug,0\r\n'
        )
        assert publisher.get(url_categories.format(s)).text == (
            'Rubrik,Anzahl\r\n'
            'Bürgergemeinden,0\r\n'
            'Ev.-ref. Kirchgemeinde,0\r\n'
            'Handelsregister,0\r\n'
            'Kantonale Mitteilungen,0\r\n'
            'Kantonale Mitteilungen / Baudirektion,0\r\n'
            'Kantonale Mitteilungen / Direktion des Innern,0\r\n'
            'Kantonale Mitteilungen / Direktion für Bildung und Kultur,0\r\n'
            'Kantonale Mitteilungen / Einberufung Kantonsrat,0\r\n'
            'Kantonale Mitteilungen / Finanzdirektion,0\r\n'
            'Kantonale Mitteilungen / Gerichtliche Bekanntmachungen,0\r\n'
            'Kantonale Mitteilungen / Gesundheitsdirektion,0\r\n'
            'Kantonale Mitteilungen / Kant. Gesetzgebung,0\r\n'
            'Kantonale Mitteilungen / Kant. Stellenangebote,0\r\n'
            'Kantonale Mitteilungen / Konkursamt,0\r\n'
            'Kantonale Mitteilungen / Mitteilungen Landschreiber,0\r\n'
            'Kantonale Mitteilungen / Volkswirtschaftsdirektion,0\r\n'
            'Kantonale Mitteilungen / Wahlen/Abstimmungen,0\r\n'
            'Kath. Kirchgemeinden,0\r\n'
            'Korporationen,0\r\n'
            'Submissionen,0\r\n'
            'Weiterbildung,0\r\n'
        )
        assert publisher.get(url_groups.format(s)).text == (
            'Gruppe,Anzahl\r\n'
        )

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
        manage.form['email'] = user
        manage.form['group'] = dict(
            (x[2], x[0]) for x in manage.form['group'].options
        )[group]
        with patch('onegov.gazette.views.users.random_password') as password:
            password.return_value = 'hunter2'
            manage.form.submit().follow()

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
    with freeze_time("2017-11-01 12:00"):
        for (organization, category, submit, user) in (
            ('100', '13', False, editor),
            ('100', '13', False, user_1),
            ('100', '1406', False, user_1),
            ('210', '1406', False, user_1),
            ('100', '16', True, user_1),
            ('100', '19', True, user_1),
            ('310', '19', True, user_1),
            ('100', '14', False, user_2),
            ('100', '16', True, user_2),
            ('210', '19', False, user_2),
            ('100', '19', True, user_3),
            ('100', '16', True, user_3),
            ('100', '19', False, user_3),
            ('100', '19', True, user_3),
        ):
            manage = user.get('/notices/drafted/new-notice')
            manage.form['title'] = "Titel"
            manage.form['organization'] = organization
            manage.form['category'] = category
            manage.form['issues'] = ['2017-44']
            manage.form['text'] = "Text"
            manage = manage.form.submit().follow()
            if submit:
                manage.click("Einreichen").form.submit()

    for s in ('rejected', 'published'):
        assert publisher.get(url_organizations.format(s)).text == (
            'Organisation,Anzahl\r\n'
            'Staatskanzlei Kanton Zug,0\r\n'
            'Bürgergemeinde Zug,0\r\n'
            'Einwohnergemeinde Zug,0\r\n'
            'Evangelisch-reformierte Kirchgemeinde des Kantons Zug,0\r\n'
            'Katholische Kirchgemeinde Baar,0\r\n'
            'Katholische Kirchgemeinde Zug,0\r\n'
            'Korporation Zug,0\r\n'
        )
        assert "Bürgergemeinden" in publisher.get(
            '/notices/{}/statistics'.format(s)
        )
        assert publisher.get(url_categories.format(s)).text == (
            'Rubrik,Anzahl\r\n'
            'Bürgergemeinden,0\r\n'
            'Ev.-ref. Kirchgemeinde,0\r\n'
            'Handelsregister,0\r\n'
            'Kantonale Mitteilungen,0\r\n'
            'Kantonale Mitteilungen / Baudirektion,0\r\n'
            'Kantonale Mitteilungen / Direktion des Innern,0\r\n'
            'Kantonale Mitteilungen / Direktion für Bildung und Kultur,0\r\n'
            'Kantonale Mitteilungen / Einberufung Kantonsrat,0\r\n'
            'Kantonale Mitteilungen / Finanzdirektion,0\r\n'
            'Kantonale Mitteilungen / Gerichtliche Bekanntmachungen,0\r\n'
            'Kantonale Mitteilungen / Gesundheitsdirektion,0\r\n'
            'Kantonale Mitteilungen / Kant. Gesetzgebung,0\r\n'
            'Kantonale Mitteilungen / Kant. Stellenangebote,0\r\n'
            'Kantonale Mitteilungen / Konkursamt,0\r\n'
            'Kantonale Mitteilungen / Mitteilungen Landschreiber,0\r\n'
            'Kantonale Mitteilungen / Volkswirtschaftsdirektion,0\r\n'
            'Kantonale Mitteilungen / Wahlen/Abstimmungen,0\r\n'
            'Kath. Kirchgemeinden,0\r\n'
            'Korporationen,0\r\n'
            'Submissionen,0\r\n'
            'Weiterbildung,0\r\n'
        )
        assert publisher.get(url_groups.format(s)).text == (
            'Gruppe,Anzahl\r\n'
            'A,0\r\n'
            'B,0\r\n'
            'C,0\r\n'
        )

    # organizations/drafted: 5 x 100, 2 x 210
    assert publisher.get(url_organizations.format('drafted')).text == (
        'Organisation,Anzahl\r\n'
        'Staatskanzlei Kanton Zug,5\r\n'
        'Bürgergemeinde Zug,2\r\n'
        'Einwohnergemeinde Zug,0\r\n'
        'Evangelisch-reformierte Kirchgemeinde des Kantons Zug,0\r\n'
        'Katholische Kirchgemeinde Baar,0\r\n'
        'Katholische Kirchgemeinde Zug,0\r\n'
        'Korporation Zug,0\r\n'
    )

    # organizations/submitted: 6 x 100, 1 x 310
    assert publisher.get(url_organizations.format('submitted')).text == (
        'Organisation,Anzahl\r\n'
        'Staatskanzlei Kanton Zug,6\r\n'
        'Bürgergemeinde Zug,0\r\n'
        'Einwohnergemeinde Zug,1\r\n'
        'Evangelisch-reformierte Kirchgemeinde des Kantons Zug,0\r\n'
        'Katholische Kirchgemeinde Baar,0\r\n'
        'Katholische Kirchgemeinde Zug,0\r\n'
        'Korporation Zug,0\r\n'
    )

    # categories/drafted: 2 x 13, 2 x 1406, 1 x 14, 2 x 19
    assert '>2</td>' in publisher.get('/notices/drafted/statistics')
    assert publisher.get(url_categories.format('drafted')).text == (
        'Rubrik,Anzahl\r\n'
        'Bürgergemeinden,0\r\n'
        'Ev.-ref. Kirchgemeinde,0\r\n'
        'Handelsregister,0\r\n'
        'Kantonale Mitteilungen,1\r\n'
        'Kantonale Mitteilungen / Baudirektion,0\r\n'
        'Kantonale Mitteilungen / Direktion des Innern,0\r\n'
        'Kantonale Mitteilungen / Direktion für Bildung und Kultur,0\r\n'
        'Kantonale Mitteilungen / Einberufung Kantonsrat,0\r\n'
        'Kantonale Mitteilungen / Finanzdirektion,0\r\n'
        'Kantonale Mitteilungen / Gerichtliche Bekanntmachungen,0\r\n'
        'Kantonale Mitteilungen / Gesundheitsdirektion,0\r\n'
        'Kantonale Mitteilungen / Kant. Gesetzgebung,2\r\n'
        'Kantonale Mitteilungen / Kant. Stellenangebote,0\r\n'
        'Kantonale Mitteilungen / Konkursamt,0\r\n'
        'Kantonale Mitteilungen / Mitteilungen Landschreiber,0\r\n'
        'Kantonale Mitteilungen / Volkswirtschaftsdirektion,0\r\n'
        'Kantonale Mitteilungen / Wahlen/Abstimmungen,0\r\n'
        'Kath. Kirchgemeinden,0\r\n'
        'Korporationen,2\r\n'
        'Submissionen,2\r\n'
        'Weiterbildung,0\r\n'
    )

    # categories/submitted: 3x16, 4x19
    assert '>3</td>' in publisher.get('/notices/submitted/statistics')
    assert publisher.get(url_categories.format('submitted')).text == (
        'Rubrik,Anzahl\r\n'
        'Bürgergemeinden,3\r\n'
        'Ev.-ref. Kirchgemeinde,0\r\n'
        'Handelsregister,0\r\n'
        'Kantonale Mitteilungen,0\r\n'
        'Kantonale Mitteilungen / Baudirektion,0\r\n'
        'Kantonale Mitteilungen / Direktion des Innern,0\r\n'
        'Kantonale Mitteilungen / Direktion für Bildung und Kultur,0\r\n'
        'Kantonale Mitteilungen / Einberufung Kantonsrat,0\r\n'
        'Kantonale Mitteilungen / Finanzdirektion,0\r\n'
        'Kantonale Mitteilungen / Gerichtliche Bekanntmachungen,0\r\n'
        'Kantonale Mitteilungen / Gesundheitsdirektion,0\r\n'
        'Kantonale Mitteilungen / Kant. Gesetzgebung,0\r\n'
        'Kantonale Mitteilungen / Kant. Stellenangebote,0\r\n'
        'Kantonale Mitteilungen / Konkursamt,0\r\n'
        'Kantonale Mitteilungen / Mitteilungen Landschreiber,0\r\n'
        'Kantonale Mitteilungen / Volkswirtschaftsdirektion,0\r\n'
        'Kantonale Mitteilungen / Wahlen/Abstimmungen,0\r\n'
        'Kath. Kirchgemeinden,0\r\n'
        'Korporationen,4\r\n'
        'Submissionen,0\r\n'
        'Weiterbildung,0\r\n'
    )

    # groups/drafted: 1 x w/o, 5 x B, 1 x C
    assert '>5</td>' in publisher.get('/notices/drafted/statistics')
    assert publisher.get(url_groups.format('drafted')).text == (
        'Gruppe,Anzahl\r\n'
        ',1\r\n'
        'A,0\r\n'
        'B,5\r\n'
        'C,1\r\n'
    )

    # groups/submitted: 4 x B, 3 x C
    assert '>4</td>' in publisher.get('/notices/submitted/statistics')
    assert publisher.get(url_groups.format('submitted')).text == (
        'Gruppe,Anzahl\r\n'
        'A,0\r\n'
        'B,4\r\n'
        'C,3\r\n'
    )
