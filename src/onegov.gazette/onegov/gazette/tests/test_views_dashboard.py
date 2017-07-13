from freezegun import freeze_time
from onegov.gazette.tests import login_editor
from onegov.gazette.tests import login_publisher
from webtest import TestApp as Client


def test_view_dashboard(gazette_app):
    with freeze_time("2017-11-01 12:00"):

        editor = Client(gazette_app)
        login_editor(editor)

        publisher = Client(gazette_app)
        login_publisher(publisher)

        manage = editor.get('/').follow()
        assert "Keine amtlichen Meldungen." in manage
        assert "<h3>Zurückgewiesen</h3>" not in manage
        assert "<h3>in Arbeit</h3>" not in manage
        assert "<h3>Eingereicht</h3>" not in manage

        # new notice
        manage = manage.click("Neu")
        manage.form['title'] = "Erneuerungswahlen"
        manage.form['category'] = '1403'
        manage.form['issues'] = ['2017-44', '2017-45']
        manage.form['text'] = "1. Oktober 2017"
        manage.form.submit()

        manage = editor.get('/').follow()
        assert "Keine amtlichen Meldungen." not in manage
        assert "<h3>Zurückgewiesen</h3>" not in manage
        assert "<h3>in Arbeit</h3>" in manage
        assert "<h3>Eingereicht</h3>" not in manage

        # submit notice
        manage.click("Erneuerungswahlen").click("Einreichen").form.submit()

        manage = editor.get('/').follow()
        assert "Keine amtlichen Meldungen." not in manage
        assert "<h3>Zurückgewiesen</h3>" not in manage
        assert "<h3>in Arbeit</h3>" not in manage
        assert "<h3>Eingereicht</h3>" in manage

        # reject notice
        manage = publisher.get('/').follow().click("Erneuerungswahlen")
        manage.click("Zurückweisen").form.submit()

        manage = editor.get('/').follow()
        assert "Keine amtlichen Meldungen." not in manage
        assert "<h3>Zurückgewiesen</h3>" in manage
        assert "<h3>in Arbeit</h3>" not in manage
        assert "<h3>Eingereicht</h3>" not in manage
        assert "Sie haben zurückgewiesene amtliche Meldungen." in manage

        # submit & publish notice
        manage.click("Erneuerungswahlen").click("Einreichen").form.submit()

        manage = publisher.get('/').follow().click("Erneuerungswahlen")
        manage.click("Veröffentlichen").form.submit()

        manage = editor.get('/').follow()
        assert "Keine amtlichen Meldungen." in manage
        assert "<h3>Zurückgewiesen</h3>" not in manage
        assert "<h3>in Arbeit</h3>" not in manage
        assert "<h3>Eingereicht</h3>" not in manage
        assert "Sie haben zurückgewiesene amtliche Meldungen." not in manage
