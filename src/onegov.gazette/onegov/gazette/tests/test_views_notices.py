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

        assert "Keine amtlichen Meldungen" in client.get('/notices/drafted')
        assert "Keine amtlichen Meldungen" in client.get('/notices/submitted')
        assert "Keine amtlichen Meldungen" in client.get('/notices/rejected')
        assert "Keine amtlichen Meldungen" in client.get('/notices/published')

        # new notice
        manage = client.get('/notices/drafted/new-notice')
        manage.form['title'] = "Erneuerungswahlen"
        manage.form['category'] = '1403'
        manage.form['issues'] = ['2017-44', '2017-45']
        manage.form['text'] = "1. Oktober 2017"
        manage.form.submit()

        assert "Erneuerungswahlen" in client.get('/notices/drafted')
        assert "Keine amtlichen Meldungen" in client.get('/notices/submitted')
        assert "Keine amtlichen Meldungen" in client.get('/notices/rejected')
        assert "Keine amtlichen Meldungen" in client.get('/notices/published')

        # submit notice
        client.get('/notice/erneuerungswahlen/submit').form.submit()

        assert "Keine amtlichen Meldungen" in client.get('/notices/drafted')
        assert "Erneuerungswahlen" in client.get('/notices/submitted')
        assert "Keine amtlichen Meldungen" in client.get('/notices/rejected')
        assert "Keine amtlichen Meldungen" in client.get('/notices/published')

        # reject notice
        client.get('/notice/erneuerungswahlen/reject').form.submit()
        assert "Keine amtlichen Meldungen" in client.get('/notices/drafted')
        assert "Keine amtlichen Meldungen" in client.get('/notices/submitted')
        assert "Erneuerungswahlen" in client.get('/notices/rejected')
        assert "Keine amtlichen Meldungen" in client.get('/notices/published')

        # submit & publish notice
        client.get('/notice/erneuerungswahlen/submit').form.submit()
        client.get('/notice/erneuerungswahlen/publish').form.submit()

        assert "Keine amtlichen Meldungen" in client.get('/notices/drafted')
        assert "Keine amtlichen Meldungen" in client.get('/notices/submitted')
        assert "Keine amtlichen Meldungen" in client.get('/notices/rejected')
        assert "Erneuerungswahlen" in client.get('/notices/published')


def test_view_notices_statistics(gazette_app):

    editor = Client(gazette_app)
    login_editor(editor)

    publisher = Client(gazette_app)
    login_publisher(publisher)

    # No notices yet
    states = ('drafted', 'submitted', 'published', 'rejected')
    for s in states:
        editor.get('/notices/{}/statistics'.format(s), status=403)
        editor.get('/notices/{}/statistics-groups'.format(s), status=403)
        editor.get('/notices/{}/statistics-categories'.format(s), status=403)

        publisher.get('/notices/{}/statistics'.format(s))
        assert publisher.get(
            '/notices/{}/statistics-groups'.format(s)
        ).text == 'Gruppe,Anzahl\r\n'
        publisher.get(
            '/notices/{}/statistics-categories'.format(s)
        ).text == (
            'Rubrik,Titel,Anzahl\r\n'
            '12,Weiterbildung,0\r\n'
            '13,Submissionen,0\r\n'
            '14,Kantonale Mitteilungen,0\r\n'
            '1402,Kantonale Mitteilungen / Einberufung Kantonsrat,0\r\n'
            '1403,Kantonale Mitteilungen / Wahlen/Abstimmungen,0\r\n'
            '1406,Kantonale Mitteilungen / Kant. Gesetzgebung,0\r\n'
            '1411,Kantonale Mitteilungen / Mitteilungen Landschreiber,0\r\n'
            '1412,Kantonale Mitteilungen / Kant. Stellenangebote,0\r\n'
            '1413,Kantonale Mitteilungen / Direktion des Innern,0\r\n'
            '1414,Kantonale Mitteilungen / Direktion für Bildung und Kultur,0'
            '\r\n'
            '1415,Kantonale Mitteilungen / Volkswirtschaftsdirektion,0\r\n'
            '1416,Kantonale Mitteilungen / Baudirektion,0\r\n'
            '1418,Kantonale Mitteilungen / Gesundheitsdirektion,0\r\n'
            '1421,Kantonale Mitteilungen / Finanzdirektion,0\r\n'
            '1426,Kantonale Mitteilungen / Gerichtliche Bekanntmachungen,0\r\n'
            '1427,Kantonale Mitteilungen / Konkursamt,0\r\n'
            '16,Bürgergemeinden,0\r\n'
            '17,Kath. Kirchgemeinden,0\r\n'
            '18,Ev.-ref. Kirchgemeinde,0\r\n'
            '19,Korporationen,0\r\n'
            '20,Handelsregister,0\r\n'
        )

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
        for (category, submit, user) in (
            ('13', False, editor),
            ('13', False, user_1),
            ('1406', False, user_1),
            ('1406', False, user_1),
            ('16', True, user_1),
            ('19', True, user_1),
            ('19', True, user_1),
            ('14', False, user_2),
            ('16', True, user_2),
            ('19', False, user_2),
            ('19', True, user_3),
            ('16', True, user_3),
            ('19', False, user_3),
            ('19', True, user_3),
        ):
            manage = user.get('/notices/drafted/new-notice')
            manage.form['title'] = "Titel"
            manage.form['category'] = category
            manage.form['issues'] = ['2017-44']
            manage.form['text'] = "Text"
            manage = manage.form.submit().follow()
            if submit:
                manage.click("Einreichen").form.submit()

    for s in ('rejected', 'published'):
        assert "Bürgergemeinden" in publisher.get(
            '/notices/{}/statistics'.format(s)
        )
        assert publisher.get(
            '/notices/{}/statistics-groups'.format(s)
        ).text == 'Gruppe,Anzahl\r\nA,0\r\nB,0\r\nC,0\r\n'
        publisher.get(
            '/notices/{}/statistics-categories'.format(s)
        ).text == (
            'Rubrik,Titel,Anzahl\r\n'
            '12,Weiterbildung,0\r\n'
            '13,Submissionen,0\r\n'
            '14,Kantonale Mitteilungen,0\r\n'
            '1402,Kantonale Mitteilungen / Einberufung Kantonsrat,0\r\n'
            '1403,Kantonale Mitteilungen / Wahlen/Abstimmungen,0\r\n'
            '1406,Kantonale Mitteilungen / Kant. Gesetzgebung,0\r\n'
            '1411,Kantonale Mitteilungen / Mitteilungen Landschreiber,0\r\n'
            '1412,Kantonale Mitteilungen / Kant. Stellenangebote,0\r\n'
            '1413,Kantonale Mitteilungen / Direktion des Innern,0\r\n'
            '1414,Kantonale Mitteilungen / Direktion für Bildung und Kultur,0'
            '\r\n'
            '1415,Kantonale Mitteilungen / Volkswirtschaftsdirektion,0\r\n'
            '1416,Kantonale Mitteilungen / Baudirektion,0\r\n'
            '1418,Kantonale Mitteilungen / Gesundheitsdirektion,0\r\n'
            '1421,Kantonale Mitteilungen / Finanzdirektion,0\r\n'
            '1426,Kantonale Mitteilungen / Gerichtliche Bekanntmachungen,0\r\n'
            '1427,Kantonale Mitteilungen / Konkursamt,0\r\n'
            '16,Bürgergemeinden,0\r\n'
            '17,Kath. Kirchgemeinden,0\r\n'
            '18,Ev.-ref. Kirchgemeinde,0\r\n'
            '19,Korporationen,0\r\n'
            '20,Handelsregister,0\r\n'
        )

    # drafted: 1 x w/o, 5 x B, 1 x C
    assert '>5</td>' in publisher.get('/notices/drafted/statistics')
    assert publisher.get('/notices/drafted/statistics-groups').text == (
        'Gruppe,Anzahl\r\n'
        ',1\r\n'
        'A,0\r\n'
        'B,5\r\n'
        'C,1\r\n'
    )

    # submitted: 4 x B, 3 x C
    assert '>4</td>' in publisher.get('/notices/submitted/statistics')
    assert publisher.get('/notices/submitted/statistics-groups').text == (
        'Gruppe,Anzahl\r\n'
        'A,0\r\n'
        'B,4\r\n'
        'C,3\r\n'
    )

    # drafted: 2 x 13, 2 x 1406, 1 x 14, 2 x 19
    assert '>2</td>' in publisher.get('/notices/drafted/statistics')
    assert publisher.get('/notices/drafted/statistics-categories').text == (
        'Rubrik,Titel,Anzahl\r\n'
        '12,Weiterbildung,0\r\n'
        '13,Submissionen,2\r\n'
        '14,Kantonale Mitteilungen,1\r\n'
        '1402,Kantonale Mitteilungen / Einberufung Kantonsrat,0\r\n'
        '1403,Kantonale Mitteilungen / Wahlen/Abstimmungen,0\r\n'
        '1406,Kantonale Mitteilungen / Kant. Gesetzgebung,2\r\n'
        '1411,Kantonale Mitteilungen / Mitteilungen Landschreiber,0\r\n'
        '1412,Kantonale Mitteilungen / Kant. Stellenangebote,0\r\n'
        '1413,Kantonale Mitteilungen / Direktion des Innern,0\r\n'
        '1414,Kantonale Mitteilungen / Direktion für Bildung und Kultur,0\r\n'
        '1415,Kantonale Mitteilungen / Volkswirtschaftsdirektion,0\r\n'
        '1416,Kantonale Mitteilungen / Baudirektion,0\r\n'
        '1418,Kantonale Mitteilungen / Gesundheitsdirektion,0\r\n'
        '1421,Kantonale Mitteilungen / Finanzdirektion,0\r\n'
        '1426,Kantonale Mitteilungen / Gerichtliche Bekanntmachungen,0\r\n'
        '1427,Kantonale Mitteilungen / Konkursamt,0\r\n'
        '16,Bürgergemeinden,0\r\n'
        '17,Kath. Kirchgemeinden,0\r\n'
        '18,Ev.-ref. Kirchgemeinde,0\r\n'
        '19,Korporationen,2\r\n'
        '20,Handelsregister,0\r\n'
    )

    # submitted: 3x16, 4x19
    assert '>3</td>' in publisher.get('/notices/submitted/statistics')
    assert publisher.get('/notices/submitted/statistics-categories').text == (
        'Rubrik,Titel,Anzahl\r\n'
        '12,Weiterbildung,0\r\n'
        '13,Submissionen,0\r\n'
        '14,Kantonale Mitteilungen,0\r\n'
        '1402,Kantonale Mitteilungen / Einberufung Kantonsrat,0\r\n'
        '1403,Kantonale Mitteilungen / Wahlen/Abstimmungen,0\r\n'
        '1406,Kantonale Mitteilungen / Kant. Gesetzgebung,0\r\n'
        '1411,Kantonale Mitteilungen / Mitteilungen Landschreiber,0\r\n'
        '1412,Kantonale Mitteilungen / Kant. Stellenangebote,0\r\n'
        '1413,Kantonale Mitteilungen / Direktion des Innern,0\r\n'
        '1414,Kantonale Mitteilungen / Direktion für Bildung und Kultur,0\r\n'
        '1415,Kantonale Mitteilungen / Volkswirtschaftsdirektion,0\r\n'
        '1416,Kantonale Mitteilungen / Baudirektion,0\r\n'
        '1418,Kantonale Mitteilungen / Gesundheitsdirektion,0\r\n'
        '1421,Kantonale Mitteilungen / Finanzdirektion,0\r\n'
        '1426,Kantonale Mitteilungen / Gerichtliche Bekanntmachungen,0\r\n'
        '1427,Kantonale Mitteilungen / Konkursamt,0\r\n'
        '16,Bürgergemeinden,3\r\n'
        '17,Kath. Kirchgemeinden,0\r\n'
        '18,Ev.-ref. Kirchgemeinde,0\r\n'
        '19,Korporationen,4\r\n'
        '20,Handelsregister,0\r\n'
    )
