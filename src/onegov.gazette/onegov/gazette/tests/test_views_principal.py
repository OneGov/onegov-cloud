from freezegun import freeze_time
from onegov.gazette.tests.common import login_admin
from onegov.gazette.tests.common import login_editor_1
from onegov.gazette.tests.common import login_publisher
from pyquery import PyQuery as pq
from webtest import TestApp as Client


def test_view_principal(gazette_app):
    client = Client(gazette_app)

    assert 'Startseite' in client.get('/').maybe_follow()
    assert '<h2>Anmelden</h2>' in client.get('/').maybe_follow()

    login_admin(client)
    assert '/notices' in client.get('/').maybe_follow().request.url

    login_publisher(client)
    assert '/notices' in client.get('/').maybe_follow().request.url

    login_editor_1(client)
    assert '/dashboard' in client.get('/').maybe_follow().request.url


def test_view_archive(gazette_app):
    principal = gazette_app.principal
    principal.frontend = True
    gazette_app.cache.set('principal', principal)

    with freeze_time("2017-11-01 12:00"):
        client = Client(gazette_app)

        publisher = Client(gazette_app)
        login_publisher(publisher)

        # generate past issues
        for index in range(13, 9, -1):
            manage = publisher.get('/issues')
            manage = manage.click('Veröffentlichen', index=index)
            manage = manage.form.submit().maybe_follow()
            assert "Ausgabe veröffentlicht." in manage

        archive = client.get('/').maybe_follow()
        assert "<h3>2017</h3>" in archive
        assert "<h3>2018</h3>" not in archive

        issues = pq(archive.body)('li a')
        assert [a.text for a in issues] == [
            'Nr. 43, 27.10.2017 (PDF)',
            'Nr. 42, 20.10.2017 (PDF)',
            'Nr. 41, 13.10.2017 (PDF)',
            'Nr. 40, 06.10.2017 (PDF)'
        ]
        assert [a.attrib['href'] for a in issues] == [
            'http://localhost/pdf/2017-43.pdf',
            'http://localhost/pdf/2017-42.pdf',
            'http://localhost/pdf/2017-41.pdf',
            'http://localhost/pdf/2017-40.pdf'
        ]

        # publish the generate
        for index in range(0, 10):
            manage = publisher.get('/issues')
            manage = manage.click('Veröffentlichen', index=index)
            manage = manage.form.submit().maybe_follow()
            assert "Ausgabe veröffentlicht." in manage

        archive = client.get('/').maybe_follow()
        assert "<h3>2017</h3>" in archive
        assert "<h3>2018</h3>" in archive

        issues = pq(archive.body)('li a')
        assert [a.text for a in issues] == [
            'Nr. 1, 05.01.2018 (PDF)',
            'Nr. 52, 29.12.2017 (PDF)',
            'Nr. 51, 22.12.2017 (PDF)',
            'Nr. 50, 15.12.2017 (PDF)',
            'Nr. 49, 08.12.2017 (PDF)',
            'Nr. 48, 01.12.2017 (PDF)',
            'Nr. 47, 24.11.2017 (PDF)',
            'Nr. 46, 17.11.2017 (PDF)',
            'Nr. 45, 10.11.2017 (PDF)',
            'Nr. 44, 03.11.2017 (PDF)',
            'Nr. 43, 27.10.2017 (PDF)',
            'Nr. 42, 20.10.2017 (PDF)',
            'Nr. 41, 13.10.2017 (PDF)',
            'Nr. 40, 06.10.2017 (PDF)'
        ]
        assert [a.attrib['href'] for a in issues] == [
            'http://localhost/pdf/2018-1.pdf',
            'http://localhost/pdf/2017-52.pdf',
            'http://localhost/pdf/2017-51.pdf',
            'http://localhost/pdf/2017-50.pdf',
            'http://localhost/pdf/2017-49.pdf',
            'http://localhost/pdf/2017-48.pdf',
            'http://localhost/pdf/2017-47.pdf',
            'http://localhost/pdf/2017-46.pdf',
            'http://localhost/pdf/2017-45.pdf',
            'http://localhost/pdf/2017-44.pdf',
            'http://localhost/pdf/2017-43.pdf',
            'http://localhost/pdf/2017-42.pdf',
            'http://localhost/pdf/2017-41.pdf',
            'http://localhost/pdf/2017-40.pdf'
        ]


def test_view_help_link(gazette_app):
    client = Client(gazette_app)

    result = client.get('/').maybe_follow()
    assert 'Hilfe' not in result

    principal = gazette_app.principal
    principal.help_link = 'https://help.me'
    gazette_app.cache.set('principal', principal)

    result = client.get('/').maybe_follow()
    assert 'Hilfe' in result
    assert 'https://help.me' in result
