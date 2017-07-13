from freezegun import freeze_time
from onegov.gazette.tests import login_editor
from onegov.gazette.tests import login_publisher
from webtest import TestApp as Client


def test_view_archive(gazette_app):
    with freeze_time("2017-11-01 12:00"):

        editor = Client(gazette_app)
        login_editor(editor)

        publisher = Client(gazette_app)
        login_publisher(publisher)

        manage = editor.get('/').follow()
        manage = manage.click("Abgeschlossene amtliche Meldungen")
        assert "Keine amtlichen Meldungen." in manage

        # add notice, submit, publish
        manage = editor.get('/').follow()
        manage = manage.click("Neu")
        manage.form['title'] = "Erneuerungswahlen"
        manage.form['category'] = '1403'
        manage.form['issues'] = ['2017-44', '2017-45']
        manage.form['text'] = "1. Oktober 2017"
        manage = manage.form.submit().follow()
        manage = manage.click("Einreichen").form.submit().follow()
        manage = publisher.get('/').follow().click("Erneuerungswahlen")
        manage.click("Veröffentlichen").form.submit()

        manage = editor.get('/').follow()
        manage = manage.click("Abgeschlossene amtliche Meldungen")
        assert "Keine amtlichen Meldungen." not in manage
        assert "Erneuerungswahlen" in manage
