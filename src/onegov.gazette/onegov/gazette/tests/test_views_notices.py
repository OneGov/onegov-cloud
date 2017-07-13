from freezegun import freeze_time
from onegov.gazette.tests import login_publisher
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
