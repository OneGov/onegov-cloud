from freezegun import freeze_time
from onegov.core.utils import module_path
from onegov.gazette.tests import accept_notice
from onegov.gazette.tests import login_users
from onegov.gazette.tests import submit_notice
from pytest import mark
from webtest.forms import Upload


@mark.parametrize("pdf_1, pdf_2", [(
    module_path('onegov.gazette', 'tests/fixtures/example_1.pdf'),
    module_path('onegov.gazette', 'tests/fixtures/example_2.pdf')
)])
def test_view_notice_attachments(gazette_app, temporary_path, pdf_1, pdf_2):

    admin, editor_1, editor_2, editor_3, publisher = login_users(gazette_app)

    with freeze_time("2017-10-01 12:00"):
        manage = editor_1.get('/notices/drafted/new-notice')
        manage.form['title'] = "Erneuerungswahlen"
        manage.form['organization'] = '200'
        manage.form['category'] = '11'
        manage.form['issues'] = ['2017-40']
        manage.form['text'] = "1. Oktober 2017"
        manage.form['author_place'] = 'Govikon'
        manage.form['author_name'] = 'State Chancellerist'
        manage.form['author_date'] = '2019-01-01'
        manage.form.submit()

        editor_1.get('/notice/erneuerungswahlen/attachments', status=403)
        manage = publisher.get('/notice/erneuerungswahlen/attachments')
        assert "Keine Anhänge." in manage

        # Try to upload an invalid file
        manage.form['file'] = Upload(
            'fake.pdf', 'PDF'.encode('utf-8'), 'application/pdf'
        )
        manage.form.submit(status=415)

        # Upload two attachment (with the same name!)
        with open(pdf_1, 'rb') as file:
            content_1 = file.read()
        manage.form['file'] = Upload('1.pdf', content_1, 'application/pdf')
        manage = manage.form.submit().maybe_follow()
        assert "Anhang hinzugefügt" in manage
        assert "1.pdf" in manage
        assert manage.click('1.pdf').content_type == 'application/pdf'

        with open(pdf_2, 'rb') as file:
            content_2 = file.read()
        manage.form['file'] = Upload('1.pdf', content_2, 'application/pdf')
        manage = manage.form.submit().maybe_follow()
        assert "Anhang hinzugefügt" in manage
        assert "1.pdf" in manage
        assert manage.click('1.pdf', index=0).content_type == 'application/pdf'
        assert manage.click('1.pdf', index=1).content_type == 'application/pdf'

        # Test if visible in notice view
        manage = editor_1.get('/notice/erneuerungswahlen')
        assert "1.pdf" in manage
        assert manage.click('1.pdf', index=0).content_type == 'application/pdf'
        assert manage.click('1.pdf', index=1).content_type == 'application/pdf'

        # Accept notice
        submit_notice(editor_1, 'erneuerungswahlen')
        accept_notice(publisher, 'erneuerungswahlen')

        # Check email
        message = gazette_app.smtp.outbox.pop()
        html = message.get_payload(0).get_payload(1).get_payload(decode=True)
        html = html.decode('utf-8')
        assert '1.pdf' in html

        assert message.get_payload(1).get_filename() == '1.pdf'
        assert message.get_payload(2).get_filename() == '1.pdf'

        attachment_1 = message.get_payload(1).get_payload(decode=True)
        attachment_2 = message.get_payload(2).get_payload(decode=True)
        assert attachment_1 != attachment_2
        assert attachment_1 == content_1 or attachment_1 == content_2
        assert attachment_2 == content_1 or attachment_2 == content_2

        # Delete attachment
        editor_1.get('/notice/erneuerungswahlen/attachments', status=403)
        publisher.get('/notice/erneuerungswahlen/attachments', status=302)
        manage = admin.get('/notice/erneuerungswahlen/attachments')

        manage = manage.click('Löschen', index=0)
        assert 'form' not in publisher.get(manage.request.url)

        manage = manage.form.submit().maybe_follow()
        assert "Anhang gelöscht." in manage
        assert "1.pdf" in editor_1.get('/notice/erneuerungswahlen')

        manage.click('Löschen').form.submit()
        assert "1.pdf" not in editor_1.get('/notice/erneuerungswahlen')
