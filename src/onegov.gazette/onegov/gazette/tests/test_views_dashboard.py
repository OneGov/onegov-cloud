from freezegun import freeze_time
from onegov.gazette.tests import login_editor
from onegov.gazette.tests import login_publisher
from webtest import TestApp as Client


def test_view_dashboard(gazette_app):
    # todo: check for warnings
    editor = Client(gazette_app)
    login_editor(editor)

    publisher = Client(gazette_app)
    login_publisher(publisher)

    with freeze_time("2017-10-20 12:00"):
        deadline = (
            "<span>Nächster Redaktionsschluss</span>: "
            "<strong>Mittwoch 25.10.2017 12:00</strong>"
        )

        manage = editor.get('/').follow()
        assert "Keine amtlichen Meldungen." in manage
        assert "<h3>Zurückgewiesen</h3>" not in manage
        assert "<h3>in Arbeit</h3>" not in manage
        assert "<h3>Eingereicht</h3>" not in manage
        assert deadline in manage

        # new notice
        manage = manage.click("Neu")
        assert deadline in manage
        manage.form['title'] = "Erneuerungswahlen"
        manage.form['organization'] = '100'
        manage.form['category'] = '11'
        manage.form['issues'] = ['2017-44', '2017-45']
        manage.form['text'] = "1. Oktober 2017"
        manage.form.submit()

        manage = editor.get('/').follow()
        assert "Keine amtlichen Meldungen." not in manage
        assert "<h3>Zurückgewiesen</h3>" not in manage
        assert "<h3>in Arbeit</h3>" in manage
        assert "<h3>Eingereicht</h3>" not in manage

    with freeze_time("2017-11-01 12:00"):
        manage = editor.get('/').follow()
        assert (
            "Sie haben eine amtliche Meldung in Arbeit, für welche der "
            "Redaktionsschluss bald erreicht ist"
        ) in manage

    with freeze_time("2017-11-02 12:00"):
        deadline = (
            "<span>Nächster Redaktionsschluss</span>: "
            "<strong>Mittwoch 08.11.2017 12:00</strong>"
        )

        manage = editor.get('/').follow()
        assert (
            "Sie haben eine amtliche Meldung in Arbeit mit vergangenen "
            "Ausgaben"
        ) in manage

        # edit notice
        manage = editor.get('/notice/erneuerungswahlen').click("Bearbeiten")
        assert deadline in manage
        manage.form['issues'] = ['2017-45']
        manage.form.submit()

        # submit notice
        manage = editor.get('/').follow()
        manage.click("Erneuerungswahlen").click("Einreichen").form.submit()

        manage = editor.get('/').follow()
        assert "Keine amtlichen Meldungen." not in manage
        assert "<h3>Zurückgewiesen</h3>" not in manage
        assert "<h3>in Arbeit</h3>" not in manage
        assert "<h3>Eingereicht</h3>" in manage

        # reject notice
        manage = publisher.get('/').follow().click("Erneuerungswahlen")
        manage = manage.click("Zurückweisen")
        manage.form['comment'] = 'comment'
        manage = manage.form.submit()

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
