import os
import transaction

from onegov.org.models.ticket import FormSubmissionHandler
from onegov.ticket import Ticket


def test_ticket_deleted_submission_is_resilient(client):
    # it so happened that the ticket.handler.submission was None
    # Viewing a ticket should not break this if that is the case.

    client.login_editor()

    page = client.get('/forms/new')
    page.form['title'] = "Newsletter"
    page.form['definition'] = "E-Mail *= @@@"
    page.form.submit()

    page = client.get('/form/newsletter')
    page.form['e_mail'] = 'info@seantis.ch'

    page.form.submit().follow().form.submit().follow()
    assert len(os.listdir(client.app.maildir)) == 1
    assert len(client.get('/timeline/feed').json['messages']) == 1

    page = client.get('/tickets/ALL/open')
    page.click('Annehmen')
    page.click('Annehmen')
    ticket_page = page.click('Annehmen').follow()

    ticket_url = ticket_page.request.path

    _, _, found_attrs = ticket_page._find_element(
        tag='a',
        href_attr='href',
        href_extract=None,
        content='Ticket abschliessen',
        id=None,
        href_pattern=None,
        index=None,
        verbose=False,
    )

    ticket_close_url = str(found_attrs['uri'])

    # intentionally call this twice, as this happened actually
    client.get(ticket_close_url).follow()
    client.get(ticket_close_url).follow()

    # reopen
    client.login_admin()
    ticket_page = client.get(ticket_url)
    ticket_page.click('Ticket wieder öffnen').follow()

    session = client.app.session()

    ticket = session.query(Ticket).first()
    session.delete(ticket.handler.submission)

    transaction.commit()
    ticket = session.query(Ticket).first()

    # monkey patch the property
    ticket.handler.__dict__['deleted'] = True

    session.add(ticket)
    transaction.commit()

    ticket = session.query(Ticket).first()
    assert ticket.handler.submission is None
    assert ticket.handler.deleted
    assert isinstance(ticket.handler, FormSubmissionHandler)

    # now navigate to ticket submission is None
    ticket_url = ticket_close_url[:-6]
    assert client.get(ticket_url).status_code == 200
