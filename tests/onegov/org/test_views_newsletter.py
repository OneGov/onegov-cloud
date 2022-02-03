import os
import re
from datetime import datetime

import transaction
from freezegun import freeze_time
from sedate import replace_timezone

from onegov.core.utils import Bunch
from onegov.newsletter import RecipientCollection, NewsletterCollection
from onegov.user import UserCollection


def test_unsubscribe_link(client):

    user = UserCollection(client.app.session())\
        .by_username('editor@example.org')

    assert not user.data

    request = Bunch(identity_secret=client.app.identity_secret, app=client.app)

    token = client.app.request_class.new_url_safe_token(request, {
        'user': 'editor@example.org'
    }, salt='unsubscribe')

    client.get('/unsubscribe?token={}'.format(token))
    page = client.get('/')
    assert "abgemeldet" in page

    user = UserCollection(client.app.session())\
        .by_username('editor@example.org')

    assert user.data['daily_ticket_statistics'] == False

    token = client.app.request_class.new_url_safe_token(request, {
        'user': 'unknown@example.org'
    }, salt='unsubscribe')

    page = client.get(
        '/unsubscribe?token={}'.format(token), expect_errors=True)
    assert page.status_code == 403

    token = client.app.request_class.new_url_safe_token(request, {
        'user': 'editor@example.org'
    }, salt='foobar')

    page = client.get(
        '/unsubscribe?token={}'.format(token), expect_errors=True)
    assert page.status_code == 403


def test_newsletters_crud(client):

    client.login_editor()

    newsletter = client.get('/newsletters')
    assert 'Es wurden noch keine Newsletter versendet' in newsletter

    new = newsletter.click('Newsletter')
    new.form['title'] = "Our town is AWESOME"
    new.form['lead'] = "Like many of you, I just love our town..."
    new.select_checkbox("occurrences", "150 Jahre Govikon")
    new.select_checkbox("occurrences", "Gemeinsames Turnen")
    newsletter = new.form.submit().follow()

    assert newsletter.pyquery('h1').text() == "Our town is AWESOME"
    assert "Like many of you" in newsletter
    assert "Gemeinsames Turnen" in newsletter
    assert "Turnhalle" in newsletter
    assert "150 Jahre Govikon" in newsletter
    assert "Sportanlage" in newsletter

    edit = newsletter.click("Bearbeiten")
    edit.form['title'] = "I can't even"
    edit.select_checkbox("occurrences", "150 Jahre Govikon", checked=False)

    newsletter = edit.form.submit().follow()

    assert newsletter.pyquery('h1').text() == "I can't even"
    assert "Like many of you" in newsletter
    assert "Gemeinsames Turnen" in newsletter
    assert "Turnhalle" in newsletter
    assert "150 Jahre Govikon" not in newsletter
    assert "Sportanlage" not in newsletter

    newsletters = client.get('/newsletters')
    assert "I can't even" in newsletters
    assert "Noch nicht gesendet." in newsletters

    # not sent, therefore not visible to the public
    assert "noch keine Newsletter" in client.spawn().get('/newsletters')

    delete_link = newsletter.pyquery('a.delete-link').attr('ic-delete-from')
    client.delete(delete_link)

    newsletters = client.get('/newsletters')
    assert "noch keine Newsletter" in newsletters


def test_newsletter_signup(client):

    page = client.get('/newsletters')
    page.form['address'] = 'asdf'
    page = page.form.submit()

    assert 'Ungültig' in page

    page.form['address'] = 'info@example.org'
    page.form.submit()

    assert len(os.listdir(client.app.maildir)) == 1

    # make sure double submissions don't result in multiple e-mails
    page.form.submit()
    assert len(os.listdir(client.app.maildir)) == 1

    message = client.get_email(0)['TextBody']
    assert 'Mit freundlichen Grüssen' not in message
    assert 'Das OneGov Cloud Team' not in message

    confirm = re.search(r'Anmeldung bestätigen\]\(([^\)]+)', message).group(1)
    unsubscribe = re.search(r'abzumelden.\]\(([^\)]+)', message).group(1)
    assert confirm.split('/confirm')[0] == unsubscribe.split('/unsubscribe')[0]

    # unsubscribing before the opt-in does nothing, no emails are sent
    assert "erfolgreich abgemeldet" in client.get(unsubscribe).follow()

    # try an illegal token first
    illegal_confirm = confirm.split('/confirm')[0] + 'x/confirm'
    assert "falsches Token" in client.get(illegal_confirm).follow()

    # make sure double calls work
    assert "info@example.org wurde erfolgreich" in client.get(confirm).follow()
    assert "info@example.org wurde erfolgreich" in client.get(confirm).follow()

    # subscribing still works the same, but there's still no email sent
    page.form.submit()
    assert len(os.listdir(client.app.maildir)) == 1

    # unsubscribing does not result in an e-mail either
    illegal_unsub = unsubscribe.split('/unsubscribe')[0] + 'x/unsubscribe'
    assert "falsches Token" in client.get(illegal_unsub).follow()
    assert "erfolgreich abgemeldet" in client.get(unsubscribe).follow()

    # no e-mail is sent when unsubscribing
    assert len(os.listdir(client.app.maildir)) == 1

    # however, we can now signup again
    page.form.submit()
    assert len(os.listdir(client.app.maildir)) == 2


def test_newsletter_rfc8058(client):

    page = client.get('/newsletters')
    page.form['address'] = 'asdf'
    page = page.form.submit()

    assert 'Ungültig' in page

    page.form['address'] = 'info@example.org'
    page.form.submit()

    assert len(os.listdir(client.app.maildir)) == 1

    # make sure double submissions don't result in multiple e-mails
    page.form.submit()
    assert len(os.listdir(client.app.maildir)) == 1

    email = client.get_email(0)
    message = email['TextBody']
    assert 'Mit freundlichen Grüssen' not in message
    assert 'Das OneGov Cloud Team' not in message
    headers = {h['Name']: h['Value'] for h in email['Headers']}
    assert 'List-Unsubscribe' in headers
    assert 'List-Unsubscribe-Post' in headers
    unsubscribe = headers['List-Unsubscribe'].strip('<>')

    confirm = re.search(r'Anmeldung bestätigen\]\(([^\)]+)', message).group(1)
    assert confirm.split('/confirm')[0] == unsubscribe.split('/unsubscribe')[0]

    # unsubscribing before the opt-in does nothing, no emails are sent
    client.post(unsubscribe)

    # try an illegal token first
    illegal_confirm = confirm.split('/confirm')[0] + 'x/confirm'
    assert "falsches Token" in client.get(illegal_confirm).follow()

    # make sure double calls work
    assert "info@example.org wurde erfolgreich" in client.get(confirm).follow()
    assert "info@example.org wurde erfolgreich" in client.get(confirm).follow()

    # subscribing still works the same, but there's still no email sent
    page.form.submit()
    assert len(os.listdir(client.app.maildir)) == 1

    # unsubscribing does not result in an e-mail either
    client.post(unsubscribe)

    # no e-mail is sent when unsubscribing
    assert len(os.listdir(client.app.maildir)) == 1

    # however, we can now signup again
    page.form.submit()
    assert len(os.listdir(client.app.maildir)) == 2


def test_newsletter_subscribers_management(client):

    page = client.get('/newsletters')
    page.form['address'] = 'info@example.org'
    page.form.submit()

    assert len(os.listdir(client.app.maildir)) == 1

    message = client.get_email(0)['TextBody']

    confirm = re.search(r'Anmeldung bestätigen\]\(([^\)]+)', message).group(1)
    assert "info@example.org wurde erfolgreich" in client.get(confirm).follow()

    client.login_editor()

    subscribers = client.get('/subscribers')
    assert "info@example.org" in subscribers

    unsubscribe = subscribers.pyquery('a[ic-get-from]').attr('ic-get-from')
    result = client.get(unsubscribe).follow()
    assert "info@example.org wurde erfolgreich abgemeldet" in result


def test_newsletter_send(client):
    anon = client.spawn()

    client.login_editor()
    page = client.get('/news').click('Nachricht')
    page.form['title'] = 'Testnews'
    page.form['lead'] = 'My Lead Text'
    page.form['text'] = '<p>My Html editor text</p>'
    page.form['text_in_newsletter'] = True
    page.form.submit().follow()

    # add a newsletter
    new = client.get('/newsletters').click('Newsletter')
    new.form['title'] = "Our town is AWESOME"
    new.form['lead'] = "Like many of you, I just love our town..."

    new.select_checkbox("news", "Testnews")
    new.select_checkbox("occurrences", "150 Jahre Govikon")
    new.select_checkbox("occurrences", "Gemeinsames Turnen")

    newsletter = new.form.submit().follow()

    # add some recipients the quick wqy
    recipients = RecipientCollection(client.app.session())
    recipients.add('one@example.org', confirmed=True)
    recipients.add('two@example.org', confirmed=True)
    recipients.add('xxx@example.org', confirmed=False)

    transaction.commit()

    assert "2 Abonnenten registriert" in client.get('/newsletters')

    # send the newsletter
    send = newsletter.click('Senden')
    assert "Dieser Newsletter wurde noch nicht gesendet." in send
    assert "one@example.org" not in send
    assert "two@example.org" not in send
    assert "xxx@example.org" not in send

    newsletter = send.form.submit().follow()
    assert '"Our town is AWESOME" wurde an 2 Empfänger gesendet' in newsletter

    page = anon.get('/newsletters')
    assert "gerade eben" in page

    # the send form should now look different
    send = newsletter.click('Senden')

    assert "Zum ersten Mal gesendet gerade eben." in send
    assert "Dieser Newsletter wurde an 2 Abonnenten gesendet." in send
    assert "one@example.org" in send
    assert "two@example.org" in send
    assert "xxx@example.org" not in send

    assert len(send.pyquery('.previous-recipients li')) == 2

    # make sure the mail was sent correctly
    assert len(os.listdir(client.app.maildir)) == 1

    mail = client.get_email(0, 0)
    message = mail['TextBody']

    assert "Our town is AWESOME" in message
    assert "Like many of you" in message

    web = re.search(r'Web-Version anzuzeigen.\]\(([^\)]+)', message).group(1)
    assert web.endswith('/newsletter/our-town-is-awesome')

    # make sure the unconfirm link is different for each mail
    unconfirm_1 = re.search(r'abzumelden.\]\(([^\)]+)', message).group(1)

    mail = client.get_email(0, 1)
    message = mail['TextBody']
    unconfirm_2 = re.search(r'abzumelden.\]\(([^\)]+)', message).group(1)

    assert unconfirm_1 and unconfirm_2
    assert unconfirm_1 != unconfirm_2

    # make sure the unconfirm link actually works
    anon.get(unconfirm_1)
    assert recipients.query().count() == 2

    anon.get(unconfirm_2)
    assert recipients.query().count() == 1

    # check content of mail
    assert 'Like many of you,' in message
    assert '150 Jahre Govikon' in message
    assert 'Gemeinsames Turnen' in message
    assert 'Testnews' in message
    assert 'My Lead Text' not in message
    assert 'My Html editor text' in message


def test_newsletter_schedule(client):
    client.login_editor()

    # add a newsletter
    new = client.get('/newsletters').click('Newsletter')
    new.form['title'] = "Our town is AWESOME"
    new.form['lead'] = "Like many of you, I just love our town..."

    new.select_checkbox("news", "Willkommen bei OneGov")
    new.select_checkbox("occurrences", "150 Jahre Govikon")

    newsletter = new.form.submit().follow()

    # add some recipients the quick wqy
    recipients = RecipientCollection(client.app.session())
    recipients.add('one@example.org', confirmed=True)
    recipients.add('two@example.org', confirmed=True)

    transaction.commit()

    send = newsletter.click('Senden')
    send.form['send'] = 'specify'

    # schedule the newsletter too close to execute
    time = replace_timezone(datetime(2018, 5, 31, 11, 55, 1), 'Europe/Zurich')

    with freeze_time(time):
        send.form['time'] = '2018-05-31 12:00'
        assert '5 Minuten in der Zukunft' in send.form.submit()

        # schedule the newsletter outside the hour
        send.form['time'] = '2018-05-31 12:55'
        assert 'nur zur vollen Stunde' in send.form.submit()

    # schedule the newsletter at a valid time
    time = replace_timezone(datetime(2018, 5, 31, 11, 55, 0), 'Europe/Zurich')

    with freeze_time(time):
        send.form['time'] = '2018-05-31 12:00'
        send.form.submit().follow()


def test_newsletter_test_delivery(client):
    client.login_editor()

    # add a newsletter
    new = client.get('/newsletters').click('Newsletter')
    new.form['title'] = "Our town is AWESOME"
    new.form['lead'] = "Like many of you, I just love our town..."

    new.select_checkbox("news", "Willkommen bei OneGov")
    new.select_checkbox("occurrences", "150 Jahre Govikon")

    newsletter = new.form.submit().follow()

    # add some recipients the quick wqy
    recipients = RecipientCollection(client.app.session())
    recipients.add('one@example.org', confirmed=True)
    recipients.add('two@example.org', confirmed=True)

    recipient = recipients.query().first().id.hex

    transaction.commit()

    send = newsletter.click('Test')
    send.form['selected_recipient'] = recipient
    send.form.submit().follow()

    assert len(os.listdir(client.app.maildir)) == 1

    send = newsletter.click('Test')
    send.form['selected_recipient'] = recipient
    send.form.submit().follow()

    assert len(os.listdir(client.app.maildir)) == 2

    newsletter = NewsletterCollection(client.app.session()).query().one()
    assert newsletter.sent is None
    assert not newsletter.recipients
