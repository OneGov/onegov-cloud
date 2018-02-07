from freezegun import freeze_time
from onegov.gazette.tests import login_editor_1
from onegov.gazette.tests import login_editor_2
from onegov.gazette.tests import login_editor_3
from onegov.gazette.tests import login_publisher
from webtest import TestApp as Client


def test_view_dashboard(gazette_app):
    editor_1 = Client(gazette_app)
    login_editor_1(editor_1)

    editor_2 = Client(gazette_app)
    login_editor_2(editor_2)

    editor_3 = Client(gazette_app)
    login_editor_3(editor_3)

    publisher = Client(gazette_app)
    login_publisher(publisher)

    # Group: Testgroup (editor_1 & editor_2)

    with freeze_time("2017-10-20 12:00"):
        deadline = (
            "<span>Nächster Eingabeschluss</span>: "
            "<strong>Mittwoch 25.10.2017 14:00</strong>"
        )

        manage = editor_1.get('/').maybe_follow()
        assert "Keine Meldungen." in manage
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
        manage.form['author_place'] = 'Govikon'
        manage.form['author_name'] = 'State Chancellerist'
        manage.form['author_date'] = '2019-01-01'
        manage.form.submit()

        manage = editor_1.get('/').maybe_follow()
        assert "Keine Meldungen." not in manage
        assert "<h3>Zurückgewiesen</h3>" not in manage
        assert "<h3>in Arbeit</h3>" in manage
        assert "<h3>Eingereicht</h3>" not in manage

        manage = editor_2.get('/').maybe_follow()  # same group
        assert "Keine Meldungen." not in manage
        assert "<h3>Zurückgewiesen</h3>" not in manage
        assert "<h3>in Arbeit</h3>" in manage
        assert "<h3>Eingereicht</h3>" not in manage

        manage = editor_3.get('/').maybe_follow()  # other group
        assert "Keine Meldungen." in manage
        assert "<h3>Zurückgewiesen</h3>" not in manage
        assert "<h3>in Arbeit</h3>" not in manage
        assert "<h3>Eingereicht</h3>" not in manage

    with freeze_time("2017-11-01 11:00"):
        manage = editor_1.get('/').maybe_follow()
        assert (
            "Sie haben Meldungen in Arbeit, für welche der "
            "Eingabeschluss bald erreicht ist."
        ) in manage

    with freeze_time("2017-11-02 12:00"):
        deadline = (
            "<span>Nächster Eingabeschluss</span>: "
            "<strong>Mittwoch 08.11.2017 13:00</strong>"
        )

        manage = editor_1.get('/').maybe_follow()
        assert (
            "Sie haben Meldungen in Arbeit mit vergangenen Ausgaben."
        ) in manage
        assert (
            "Sie haben Meldungenen in Arbeit, für welche der "
            "Eingabeschluss bald erreicht ist."
        ) not in manage

        # edit notice
        manage = editor_1.get('/notice/erneuerungswahlen').click("Bearbeiten")
        assert deadline in manage
        manage.form['issues'] = ['2017-45']
        manage.form.submit()

        # submit notice
        manage = editor_1.get('/').maybe_follow()
        manage.click("Erneuerungswahlen").click("Einreichen").form.submit()

        manage = editor_1.get('/').maybe_follow()
        assert "Keine Meldungen." not in manage
        assert "<h3>Zurückgewiesen</h3>" not in manage
        assert "<h3>in Arbeit</h3>" not in manage
        assert "<h3>Eingereicht</h3>" in manage

        manage = editor_2.get('/').maybe_follow()  # same group
        assert "Keine Meldungen." not in manage
        assert "<h3>Zurückgewiesen</h3>" not in manage
        assert "<h3>in Arbeit</h3>" not in manage
        assert "<h3>Eingereicht</h3>" in manage

        manage = editor_3.get('/').maybe_follow()  # other group
        assert "Keine Meldungen." in manage
        assert "<h3>Zurückgewiesen</h3>" not in manage
        assert "<h3>in Arbeit</h3>" not in manage
        assert "<h3>Eingereicht</h3>" not in manage

        # reject notice
        manage = publisher.get('/').maybe_follow().click("Erneuerungswahlen")
        manage = manage.click("Zurückweisen")
        manage.form['comment'] = 'comment'
        manage = manage.form.submit()

        manage = editor_1.get('/').maybe_follow()
        assert "Keine Meldungen." not in manage
        assert "<h3>Zurückgewiesen</h3>" in manage
        assert "<h3>in Arbeit</h3>" not in manage
        assert "<h3>Eingereicht</h3>" not in manage
        assert "Sie haben zurückgewiesene Meldungen." in manage

        manage = editor_2.get('/').maybe_follow()  # same group
        assert "Keine Meldungen." not in manage
        assert "<h3>Zurückgewiesen</h3>" in manage
        assert "<h3>in Arbeit</h3>" not in manage
        assert "<h3>Eingereicht</h3>" not in manage
        assert "Sie haben zurückgewiesene Meldungen." in manage

        manage = editor_3.get('/').maybe_follow()  # other group
        assert "Keine Meldungen." in manage
        assert "<h3>Zurückgewiesen</h3>" not in manage
        assert "<h3>in Arbeit</h3>" not in manage
        assert "<h3>Eingereicht</h3>" not in manage

        # submit & accept notice
        manage = editor_1.get('/').maybe_follow().click("Erneuerungswahlen")
        manage.click("Einreichen").form.submit()

        manage = publisher.get('/').maybe_follow().click("Erneuerungswahlen")
        manage.click("Annehmen").form.submit()

        manage = editor_1.get('/').maybe_follow()
        assert "Keine Meldungen." in manage
        assert "<h3>Zurückgewiesen</h3>" not in manage
        assert "<h3>in Arbeit</h3>" not in manage
        assert "<h3>Eingereicht</h3>" not in manage
        assert "Sie haben zurückgewiesene Meldungen." not in manage

        manage = editor_2.get('/').maybe_follow()  # same group
        assert "Keine Meldungen." in manage
        assert "<h3>Zurückgewiesen</h3>" not in manage
        assert "<h3>in Arbeit</h3>" not in manage
        assert "<h3>Eingereicht</h3>" not in manage
        assert "Sie haben zurückgewiesene Meldungen." not in manage

        manage = editor_3.get('/').maybe_follow()  # other group
        assert "Keine Meldungen." in manage
        assert "<h3>Zurückgewiesen</h3>" not in manage
        assert "<h3>in Arbeit</h3>" not in manage
        assert "<h3>Eingereicht</h3>" not in manage

    # Group: None (editor_3)

    with freeze_time("2017-10-20 12:00"):

        manage = editor_3.get('/').maybe_follow()
        assert "Keine Meldungen." in manage
        assert "<h3>Zurückgewiesen</h3>" not in manage
        assert "<h3>in Arbeit</h3>" not in manage
        assert "<h3>Eingereicht</h3>" not in manage

        # new notice
        manage = manage.click("Neu")
        manage.form['title'] = "Kantonsratswahlen"
        manage.form['organization'] = '100'
        manage.form['category'] = '11'
        manage.form['issues'] = ['2017-44', '2017-45']
        manage.form['text'] = "1. Oktober 2017"
        manage.form['author_place'] = 'Govikon'
        manage.form['author_name'] = 'State Chancellerist'
        manage.form['author_date'] = '2019-01-01'
        manage.form.submit()

        manage = editor_1.get('/').maybe_follow()  # other group
        assert "Keine Meldungen." in manage
        assert "<h3>Zurückgewiesen</h3>" not in manage
        assert "<h3>in Arbeit</h3>" not in manage
        assert "<h3>Eingereicht</h3>" not in manage

        manage = editor_2.get('/').maybe_follow()  # other group
        assert "Keine Meldungen." in manage
        assert "<h3>Zurückgewiesen</h3>" not in manage
        assert "<h3>in Arbeit</h3>" not in manage
        assert "<h3>Eingereicht</h3>" not in manage

        manage = editor_3.get('/').maybe_follow()
        assert "Keine Meldungen." not in manage
        assert "<h3>Zurückgewiesen</h3>" not in manage
        assert "<h3>in Arbeit</h3>" in manage
        assert "<h3>Eingereicht</h3>" not in manage
