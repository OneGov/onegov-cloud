from freezegun import freeze_time
from onegov.gazette.tests import login_editor
from onegov.gazette.tests import login_publisher
from webtest import TestApp as Client


def test_view_notice_reject_publish(gazette_app):

    with freeze_time("2017-11-01 12:00"):

        editor = Client(gazette_app)
        login_editor(editor)

        publisher = Client(gazette_app)
        login_publisher(publisher)

        # new notice(s)
        # state: DRAFTED
        manage = editor.get('/notices/drafted/new-notice')
        manage.form['title'] = "Erneuerungswahlen"
        manage.form['category'] = '1403'
        manage.form['issues'] = ['2017-44', '2017-45']
        manage.form['text'] = "1. Oktober 2017"
        manage = manage.form.submit().follow()
        assert "action-copy" not in manage
        assert "action-delete" in manage
        assert "action-edit" in manage
        assert "action-preview" in manage
        assert "action-publish" not in manage
        assert "action-reject" not in manage
        assert "action-submit" in manage
        assert "Erneuerungswahlen" in manage
        assert "1. Oktober 2017" in manage
        assert "Kantonale Mitteilungen / Wahlen/Abstimmungen" in manage
        assert "editor@example.org" in manage
        assert "Nr. 44, 03.11.2017" in manage
        assert "Nr. 45, 10.11.2017" in manage
        assert "in Arbeit" in manage
        assert "erstellt" in manage

        manage = publisher.get('/notices/drafted/new-notice')
        manage.form['title'] = "Schalterschliessung"
        manage.form['category'] = '1411'
        manage.form['issues'] = ['2017-44', '2017-45']
        manage.form['text'] = "1.-15. Oktober 2017"
        manage = manage.form.submit().follow()
        assert "action-copy" not in manage
        assert "action-delete" not in manage
        assert "action-edit" not in manage
        assert "action-preview" in manage
        assert "action-publish" not in manage
        assert "action-reject" not in manage
        assert "action-submit" not in manage
        assert "Schalterschliessung" in manage
        assert "1.-15. Oktober 2017" in manage
        assert "Kantonale Mitteilungen / Mitteilungen Landschreiber" in manage
        assert "publisher@example.org" in manage
        assert "Nr. 44, 03.11.2017" in manage
        assert "Nr. 45, 10.11.2017" in manage
        assert "in Arbeit" in manage
        assert "erstellt" in manage

        # preview the notice(s)
        preview = editor.get('/notice/erneuerungswahlen/preview')
        assert "Erneuerungswahlen" in preview
        assert "1. Oktober 2017" in preview
        preview = publisher.get('/notice/schalterschliessung/preview')
        assert "Schalterschliessung" in preview
        assert "1.-15. Oktober 2017" in preview

        # edit notice(s)
        manage = editor.get('/notice/erneuerungswahlen/edit')
        manage.form['issues'] = ['2017-44', '2017-45', '2017-46']
        manage = manage.form.submit().follow()
        assert "Nr. 46, 17.11.2017" in manage
        assert "bearbeitet" in manage

        manage = publisher.get('/notice/schalterschliessung/edit')
        manage.form['text'] = "1.-17. Oktober 2017"
        manage = manage.form.submit().follow()
        assert "1.-17. Oktober 2017" in manage
        assert "bearbeitet" in manage

        # try to publish the drafted notice(s)
        editor.get('/notice/erneuerungswahlen/publish', status=403)
        assert (
            "Es können nur eingereichte amtliche Meldungen publiziert werden."
        ) in publisher.get('/notice/erneuerungswahlen/publish')

        # try to reject the drafted notice(s)
        editor.get('/notice/erneuerungswahlen/reject', status=403)
        assert (
            "Es können nur eingereichte amtliche Meldungen zurückgewiesen "
            "werden."
        ) in publisher.get('/notice/erneuerungswahlen/reject')

        # submit the notice(s)
        # state: SUBMITTED
        manage = editor.get('/notice/erneuerungswahlen/submit')
        manage = manage.form.submit().follow().follow()
        assert "Amtliche Meldung eingereicht." in manage
        manage = editor.get('/notice/erneuerungswahlen')
        assert "action-copy" not in manage
        assert "action-delete" not in manage
        assert "action-edit" not in manage
        assert "action-preview" in manage
        assert "action-publish" not in manage
        assert "action-reject" not in manage
        assert "action-submit" not in manage

        manage = publisher.get('/notice/schalterschliessung/submit')
        manage = manage.form.submit().follow().follow()
        assert "Amtliche Meldung eingereicht." in manage
        manage = publisher.get('/notice/schalterschliessung')
        assert "eingereicht" in manage
        assert "action-copy" not in manage
        assert "action-delete" not in manage
        assert "action-edit" in manage
        assert "action-preview" in manage
        assert "action-publish" in manage
        assert "action-reject" in manage
        assert "action-submit" not in manage

        # try to submit submitted notice
        assert (
            "Es können nur zurückgewiesene amtliche Meldungen oder Meldungen "
            "in Arbeit eingereicht werden."
        ) in editor.get('/notice/erneuerungswahlen/submit')
        assert (
            "Es können nur zurückgewiesene amtliche Meldungen oder Meldungen "
            "in Arbeit eingereicht werden."
        ) in publisher.get('/notice/schalterschliessung/submit')

        # try to delete the submitted notice(s)
        assert (
            "Es können nur zurückgewiesene amtliche Meldungen oder Meldungen "
            "in Arbeit gelöscht werden."
        ) in editor.get('/notice/erneuerungswahlen/delete')
        assert (
            "Es können nur zurückgewiesene amtliche Meldungen oder Meldungen "
            "in Arbeit gelöscht werden."
        ) in publisher.get('/notice/schalterschliessung/delete')

        # edit the submitted notice(s)
        manage = editor.get('/notice/erneuerungswahlen/edit')
        manage.form['issues'] = ['2017-44', '2017-45', '2017-46', '2017-47']
        manage = manage.form.submit().follow()
        assert "Nr. 47, 24.11.2017" in manage

        manage = publisher.get('/notice/schalterschliessung/edit')
        manage.form['text'] = "1.-18. Oktober 2017"
        manage = manage.form.submit().follow()
        assert "1.-18. Oktober 2017" in manage

        # reject one notice
        # state: REJECTED
        editor.get('/notice/erneuerungswahlen/reject', status=403)

        manage = publisher.get('/notice/erneuerungswahlen/reject')
        manage = manage.form.submit().follow().follow()
        assert "Amtliche Meldung zurückgewiesen." in manage
        manage = publisher.get('/notice/erneuerungswahlen')
        assert "zurückgewiesen" in manage
        assert "action-copy" not in manage
        assert "action-delete" not in manage
        assert "action-edit" not in manage
        assert "action-preview" in manage
        assert "action-publish" not in manage
        assert "action-reject" not in manage
        assert "action-submit" not in manage

        manage = editor.get('/notice/erneuerungswahlen')
        assert "zurückgewiesen" in manage
        assert "action-copy" not in manage
        assert "action-delete" in manage
        assert "action-edit" in manage
        assert "action-preview" in manage
        assert "action-publish" not in manage
        assert "action-reject" not in manage
        assert "action-submit" in manage

        assert len(gazette_app.smtp.outbox) == 1
        message = gazette_app.smtp.outbox[0]
        message = message.get_payload(1).get_payload(decode=True)
        message = message.decode('utf-8')
        assert "Ihre amtliche Meldung wurde zurückgewiesen:" in message

        # try to reject the rejected notice
        editor.get('/notice/erneuerungswahlen/reject', status=403)
        assert (
            "Es können nur eingereichte amtliche Meldungen zurückgewiesen "
            "werden."
        ) in publisher.get('/notice/erneuerungswahlen/reject')

        # try to publish the rejected notice
        editor.get('/notice/erneuerungswahlen/publish', status=403)
        assert (
            "Es können nur eingereichte amtliche Meldungen publiziert werden."
        ) in publisher.get('/notice/erneuerungswahlen/publish')

        # edit the rejected notice
        manage = editor.get('/notice/erneuerungswahlen/edit')
        manage.form['title'] = "Erneuerungswahlen 2017"
        manage = manage.form.submit().follow()
        assert "Erneuerungswahlen 2017" in manage

        manage = publisher.get('/notice/erneuerungswahlen/edit')
        manage.form['title'] = "Erneuerungswahlen 10/2017"
        manage = manage.form.submit().follow()
        assert "Erneuerungswahlen 10/2017" in manage

        # submit the rejected notice
        manage = editor.get('/notice/erneuerungswahlen/submit')
        manage = manage.form.submit().follow().follow()
        assert "Amtliche Meldung eingereicht." in manage

        # publish the submitted notice
        # state: PUBLISHED
        editor.get('/notice/erneuerungswahlen/publish', status=403)

        manage = publisher.get('/notice/erneuerungswahlen/publish')
        manage = manage.form.submit().follow().follow()
        assert "Amtliche Meldung veröffentlicht." in manage
        manage = publisher.get('/notice/erneuerungswahlen')
        assert "veröffentlicht" in manage
        assert "action-copy" not in manage
        assert "action-delete" not in manage
        assert "action-edit" not in manage
        assert "action-preview" in manage
        assert "action-publish" not in manage
        assert "action-reject" not in manage
        assert "action-submit" not in manage

        manage = editor.get('/notice/erneuerungswahlen')
        assert "veröffentlicht" in manage
        assert "action-copy" in manage
        assert "action-delete" not in manage
        assert "action-edit" not in manage
        assert "action-preview" in manage
        assert "action-publish" not in manage
        assert "action-reject" not in manage
        assert "action-submit" not in manage

        assert len(gazette_app.smtp.outbox) == 3
        message = gazette_app.smtp.outbox[1]
        message = message.get_payload(1).get_payload(decode=True)
        message = message.decode('utf-8')
        assert "Ihre amtliche Meldung wurde veröffentlicht:" in message

        message = gazette_app.smtp.outbox[2]
        message = message.get_payload(1).get_payload(decode=True)
        message = message.decode('utf-8')
        assert "Bitte veröffentlichen Sie folgende amtliche Meldung:" \
            in message
        assert "Nr. 45, 10.11.2017" in message
        assert "Nr. 47, 24.11.2017" in message
        assert "Nr. 44, 03.11.2017" in message
        assert "Nr. 46, 17.11.2017" in message
        assert "Erneuerungswahlen 10/2017" in message
        assert "Kantonale Mitteilungen / Wahlen/Abstimmungen" in message
        assert "1. Oktober 2017" in message

        # try to publish a published notice
        editor.get('/notice/erneuerungswahlen/publish', status=403)
        assert (
            "Es können nur eingereichte amtliche Meldungen publiziert werden."
        ) in publisher.get('/notice/erneuerungswahlen/publish')

        # try to submit the published notice
        assert (
            "Es können nur zurückgewiesene amtliche Meldungen oder Meldungen "
            "in Arbeit eingereicht werden."
        ) in editor.get('/notice/erneuerungswahlen/submit')
        assert (
            "Es können nur zurückgewiesene amtliche Meldungen oder Meldungen "
            "in Arbeit eingereicht werden."
        ) in publisher.get('/notice/erneuerungswahlen/submit')

        # try to reject a published notice
        editor.get('/notice/erneuerungswahlen/reject', status=403)
        assert (
            "Es können nur eingereichte amtliche Meldungen zurückgewiesen "
            "werden."
        ) in publisher.get('/notice/erneuerungswahlen/reject')

        # try to edit the published notice
        assert (
            "Veröffentlichte amtliche Meldungen können nicht editiert werden."
        ) in editor.get('/notice/erneuerungswahlen/edit')
        assert (
            "Veröffentlichte amtliche Meldungen können nicht editiert werden."
        ) in publisher.get('/notice/erneuerungswahlen/edit')

        # try to delete the published notice
        assert (
            "Es können nur zurückgewiesene amtliche Meldungen oder Meldungen "
            "in Arbeit gelöscht werden."
        ) in editor.get('/notice/erneuerungswahlen/delete')
        assert (
            "Es können nur zurückgewiesene amtliche Meldungen oder Meldungen "
            "in Arbeit gelöscht werden."
        ) in publisher.get('/notice/erneuerungswahlen/delete')


def test_view_notice_delete(gazette_app):
    with freeze_time("2017-11-01 12:00"):
        editor = Client(gazette_app)
        login_editor(editor)

        publisher = Client(gazette_app)
        login_publisher(publisher)

        # delete a drafted notice
        for user in (editor, publisher):
            manage = editor.get('/notices/drafted/new-notice')
            manage.form['title'] = "Erneuerungswahlen"
            manage.form['category'] = '1403'
            manage.form['issues'] = ['2017-44', '2017-45']
            manage.form['text'] = "1. Oktober 2017"
            manage.form.submit()
            manage = user.get('/notice/erneuerungswahlen/delete')
            manage = manage.form.submit().follow().follow()
            assert "Amtliche Meldung gelöscht." in manage

        # delete a rejected notice
        for user in (editor, publisher):
            manage = editor.get('/notices/drafted/new-notice')
            manage.form['title'] = "Erneuerungswahlen"
            manage.form['category'] = '1403'
            manage.form['issues'] = ['2017-44', '2017-45']
            manage.form['text'] = "1. Oktober 2017"
            manage.form.submit()
            editor.get('/notice/erneuerungswahlen/submit').form.submit()
            publisher.get('/notice/erneuerungswahlen/reject').form.submit()
            manage = user.get('/notice/erneuerungswahlen/delete')
            manage = manage.form.submit().follow().follow()
            assert "Amtliche Meldung gelöscht." in manage


def test_view_notice_edit_others(gazette_app):
    with freeze_time("2017-11-01 12:00"):
        editor = Client(gazette_app)
        login_editor(editor)

        publisher = Client(gazette_app)
        login_publisher(publisher)

        manage = publisher.get('/notices/drafted/new-notice')
        manage.form['title'] = "Erneuerungswahlen"
        manage.form['category'] = '1403'
        manage.form['issues'] = ['2017-44', '2017-45']
        manage.form['text'] = "1. Oktober 2017"
        manage.form.submit()

        editor.get('/notice/erneuerungswahlen/edit', status=403)
        editor.get('/notice/erneuerungswahlen/submit', status=403)
        editor.get('/notice/erneuerungswahlen/delete', status=403)


def test_view_notice_copy(gazette_app):
    editor = Client(gazette_app)
    login_editor(editor)

    with freeze_time("2017-10-01 12:00"):
        manage = editor.get('/notices/drafted/new-notice')
        manage.form['title'] = "Erneuerungswahlen"
        manage.form['category'] = '1403'
        manage.form['issues'] = ['2017-40']
        manage.form['text'] = "1. Oktober 2017"
        manage.form.submit()

        editor.get('/notice/erneuerungswahlen/submit').form.submit()

    publisher = Client(gazette_app)
    login_publisher(publisher)
    publisher.get('/notice/erneuerungswahlen/publish').form.submit()

    with freeze_time("2018-01-01 12:00"):
        manage = editor.get('/notice/erneuerungswahlen').click("Kopieren")
        assert manage.form['title'].value == "Erneuerungswahlen"
        assert manage.form['category'].value == '1403'
        assert manage.form['text'].value == "1. Oktober 2017"
        assert "Das Formular enthält Fehler" in manage.form.submit()

        manage.form['issues'] = ['2018-1']
        manage = manage.form.submit().follow()

        assert "Erneuerungswahlen" in editor.get('/dashboard')
