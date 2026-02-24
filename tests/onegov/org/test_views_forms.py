from __future__ import annotations

import os
import textwrap
import transaction
import zipfile

from datetime import date, timedelta
from freezegun import freeze_time
from io import BytesIO
from onegov.core.utils import module_path
from onegov.file import FileCollection
from onegov.form import (
    FormCollection, FormDefinitionCollection, as_internal_id)
from onegov.org.models import TicketNote
from onegov.org.models.document_form import FormDocument
from onegov.people import Person
from onegov.ticket import TicketCollection, Ticket
from onegov.user import UserCollection
from tempfile import TemporaryDirectory
from tests.shared.utils import create_image, create_pdf
from unittest.mock import patch
from webtest import Upload

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from tests.shared.client import ExtendedResponse
    from unittest.mock import MagicMock
    from .conftest import Client


def test_view_form_alert(client: Client) -> None:
    login = client.get('/auth/login').form.submit()
    assert 'Das Formular enthält Fehler' in login


def test_render_form(client: Client) -> None:

    class Field:
        def __init__(
            self,
            name: str,
            definition: str,
            comment: str | None = None
        ) -> None:
            self.name = name
            self.id = as_internal_id(name)
            self.definition = definition
            self.comment = comment

        def __str__(self) -> str:
            base = f'{self.name} {self.definition}'
            if self.comment:
                base += f'\n<< {self.comment} >>'
            return base

    long_field_help = 20 * 'ZZZ'
    short_comment = 'short comment'

    # BooleanField does not appear in formcode definitions...
    # these also support the placeholder

    supporting_long_field_help = [
        Field('time', '= HH:MM', long_field_help),
        Field('date_time', '= YYYY.MM.DD HH:MM', long_field_help),
        Field('website', '= http://', long_field_help),
        Field('date', '= YYYY.MM.DD', long_field_help),
        Field('Textfield long', '*= ___', long_field_help),
        Field('Email long', '* = @@@', long_field_help),
        Field('Checkbox', """*=
    [ ] 4051
    [ ] 4052""", long_field_help),
        Field('Select', """=
    (x) A
    ( ) B""", long_field_help),
        Field('Alter', '= 0..150', long_field_help),
        Field('Percentage', '= 0.00..100.00', long_field_help),
        Field('IBAN', '= # iban', long_field_help),
        Field('AHV Nummer', '= # ch.ssn', long_field_help),
        Field('UID Nummer', '= # ch.uid', long_field_help),
        Field('MWST Nummer', '= # ch.vat', long_field_help),
        Field('Markdown', '= <markdown>', long_field_help)
    ]

    # Those should render description externally, checked visually
    not_rendering_placeholder = [
        Field('Checkbox2', """*=
    [ ] 4051
    [ ] 4052""", short_comment),
        Field('Select2', """=
    (x) A
    ( ) B""", short_comment),
        Field('Image2', '= *.jpg|*.png|*.gif', short_comment),
        Field('Dokument2', '= *.pdf', short_comment)
    ]

    fields = not_rendering_placeholder + supporting_long_field_help
    definition = "\n".join(str(f) for f in fields)

    collection = FormCollection(client.app.session())
    collection.definitions.add('Fields', definition=definition, type='custom')

    transaction.commit()

    page = client.get('/form/fields')

    for field in fields:
        row = page.pyquery(f'.field-{field.id} .long-field-help')
        print(field.name)
        assert row.text() == field.comment
        assert 'None' not in row.text()


@patch('onegov.websockets.integration.connect')
@patch('onegov.websockets.integration.authenticate')
@patch('onegov.websockets.integration.broadcast')
def test_submit_form(
    broadcast: MagicMock,
    authenticate: MagicMock,
    connect: MagicMock,
    client: Client
) -> None:

    collection = FormCollection(client.app.session())
    collection.definitions.add('Profile', definition=textwrap.dedent("""
        # Your Details
        First name * = ___
        Last name * = ___
        E-Mail * = @@@
    """), type='custom', pick_up='pickup test message')

    transaction.commit()

    form_page = client.get('/forms').click('Profile')
    assert 'Your Details' in form_page
    assert 'First name' in form_page
    assert 'Last name' in form_page
    assert 'E-Mail' in form_page

    assert 'form/' in form_page.request.url
    form_page = form_page.form.submit().follow()

    assert 'form/' not in form_page.request.url
    assert 'form-preview' in form_page.request.url
    assert len(form_page.pyquery('small.error')) == 3

    form_page.form['your_details_first_name'] = 'Kung'
    form_page = form_page.form.submit()

    assert len(form_page.pyquery('small.error')) == 2

    form_page.form['your_details_last_name'] = 'Fury'
    form_page.form['your_details_e_mail'] = 'kung.fury@example.org'
    form_page = form_page.form.submit()

    assert len(form_page.pyquery('small.error')) == 0
    ticket_page = form_page.form.submit().follow()

    # make sure a ticket has been created
    assert 'FRM-' in ticket_page
    assert 'ticket-state-open' in ticket_page
    assert 'pickup test message' in ticket_page

    tickets = TicketCollection(client.app.session()).by_handler_code('FRM')
    assert len(tickets) == 1

    assert tickets[0].title == 'Kung, Fury, kung.fury@example.org'
    assert tickets[0].group == 'Profile'

    # the user should have gotten an e-mail with the entered data
    message = client.get_email(-1)['TextBody']
    assert 'Fury' in message

    assert connect.call_count == 1
    assert authenticate.call_count == 1
    assert broadcast.call_count == 1
    assert broadcast.call_args[0][3]['event'] == 'browser-notification'
    assert broadcast.call_args[0][3]['title'] == 'Neues Ticket'
    assert broadcast.call_args[0][3]['created']

    # unless he opts out of it
    form_page = client.get('/forms').click('Profile')
    form_page = form_page.form.submit().follow()
    form_page.form['your_details_first_name'] = 'Kung'
    form_page.form['your_details_last_name'] = 'Fury'
    form_page.form['your_details_e_mail'] = 'kung.fury@example.org'
    form_page = form_page.form.submit()

    form_page.form.get('send_by_email', index=0).value = False
    ticket_page = form_page.form.submit().follow()

    message = client.get_email(-1)['TextBody']
    assert 'Fury' not in message

    assert connect.call_count == 2
    assert authenticate.call_count == 2
    assert broadcast.call_count == 2
    assert broadcast.call_args[0][3]['event'] == 'browser-notification'
    assert broadcast.call_args[0][3]['title'] == 'Neues Ticket'
    assert broadcast.call_args[0][3]['created']


def test_pending_submission_error_file_upload(client: Client) -> None:
    collection = FormCollection(client.app.session())
    collection.definitions.add('Statistics', definition=textwrap.dedent("""
        Name * = ___
        Datei * = *.txt|*.csv
    """), type='custom')
    transaction.commit()

    form_page = client.get('/forms').click('Statistics')
    form_page.form['datei'] = Upload('test.jpg', create_image().read())

    form_page = form_page.form.submit().follow()
    assert 'form-preview' in form_page.request.url
    assert len(form_page.pyquery('small.error')) == 2


def test_pending_submission_successful_file_upload(client: Client) -> None:
    collection = FormCollection(client.app.session())
    collection.definitions.add('Statistics', definition=textwrap.dedent("""
        Name * = ___
        Datei * = *.txt|*.csv
    """), type='custom')
    transaction.commit()

    form_page = client.get('/forms').click('Statistics')
    form_page.form['datei'] = Upload('README.txt', b'1;2;3')
    form_page = form_page.form.submit().follow()

    assert "README.txt" in form_page.text
    assert "Datei ersetzen" in form_page.text
    assert "Datei löschen" in form_page.text
    assert "Datei behalten" in form_page.text

    # FIXME: we should be able to test this now
    # unfortunately we can't test more here, as webtest doesn't support
    # multiple differing fields of the same name...
    # wait until webtest 3.0.1, which will support multiple file upload


def test_add_custom_form(client: Client) -> None:
    client.login_editor()

    # this error is not strictly line based, so there's a general error
    form_page = client.get('/forms/new')
    form_page.form['title'] = "My Form"
    form_page.form['lead'] = "This is a form"
    form_page.form['text'] = "There are many like it, but this one's mine"
    form_page.form['definition'] = "abc ="
    form_page = form_page.form.submit()

    assert "Das Formular ist nicht gültig." in form_page

    # this error is line based
    form_page = client.get('/forms/new')
    form_page.form['title'] = "My Form"
    form_page.form['lead'] = "This is a form"
    form_page.form['text'] = "There are many like it, but this one's mine"
    form_page.form['definition'] = "xxx = !!!"
    form_page = form_page.form.submit()

    assert "Der Syntax in der 1. Zeile ist ungültig." in form_page
    assert 'data-highlight-line="1"' in form_page

    form_page.form['definition'] = "Name * = ___\nE-Mail * = @@@"
    form_page = form_page.form.submit().follow()

    form_page.form['name'] = 'My name'
    form_page.form['e_mail'] = 'my@name.com'
    form_page = form_page.form.submit().follow()

    form_page = client.get('/form/my-form/edit')
    form_page.form['definition'] = "Nom * = ___\nMail * = @@@"
    form_page = form_page.form.submit().follow()

    form_page.form['nom'] = 'My name'
    form_page.form['mail'] = 'my@name.com'
    form_page.form.submit().follow()


def test_add_custom_form_minimum_price_validation(client: Client) -> None:
    client.login_editor()

    form_page = client.get('/forms/new')
    form_page.form['title'] = "My Form"
    form_page.form['definition'] = textwrap.dedent("""
        E-Mail *= @@@

        Stamp A = 0..20 (1.20 CHF)
        Stamp B = 0..20 (1.00 CHF)

        Discount *=
            (x) First four B stamps free (-4.00 CHF)
    """)
    form_page.form['minimum_price_total'] = '5.00'
    form_page = form_page.form.submit().follow()

    form_page.form['e_mail'] = 'my@name.com'
    form_page.form['stamp_b'] = '6'
    # the validation happens on the next page
    form_page = form_page.form.submit().follow()

    assert "Der Totalbetrag für Ihre Eingaben" in form_page
    assert "beläuft sich auf 2.00 CHF" in form_page
    assert "allerdings ist der Minimalbetrag 5.00 CHF" in form_page

    # now that we reached the minimum price we should succeed
    form_page.form['stamp_a'] = '3'
    form_page = form_page.form.submit()
    assert "Totalbetrag" in form_page
    assert "5.60 CHF" in form_page
    assert "Minimalbetrag" not in form_page


def test_add_custom_form_payment_metod_validation_error(
    client: Client
) -> None:
    client.login_editor()

    form_page = client.get('/forms/new')
    form_page.form['title'] = "My Form"
    form_page.form['definition'] = textwrap.dedent("""
        E-Mail *= @@@

        Delivery *=
            ( ) Pickup (0 CHF)
            ( ) Delivery (5 CHF!)
    """)
    form_page = form_page.form.submit()
    # here it will fail because it's mixing required cc with required
    # manual payments
    assert "'Delivery' enthält einen Preis der eine Kredit" in form_page.text

    # now it will fail because there is no payment processor
    form_page.form['payment_method'] = 'free'
    form_page = form_page.form.submit()
    assert "benötigen Sie einen Standard-Zahlungsanbieter" in form_page


def test_add_custom_form_payment_validation_error(client: Client) -> None:
    client.login_editor()

    form_page = client.get('/forms/new')
    form_page.form['title'] = "My Form"
    form_page.form['definition'] = 'E-Mail *= @@@'
    form_page.form['minimum_price_total'] = '5.00'
    form_page = form_page.form.submit()
    # this should fail because we're setting a minimum price, but there
    # are no form fields that have pricing assigned to them
    assert "Ein Minimalpreis kann nur gesetzt werden" in form_page.text

    # now it should succeed
    form_page.form['definition'] = textwrap.dedent("""
        E-Mail *= @@@

        Delivery *=
            ( ) Pickup (0 CHF)
            ( ) Delivery (5 CHF)
    """)
    form_page = form_page.form.submit().follow()


def test_add_duplicate_form(client: Client) -> None:
    client.login_editor()

    form_page = client.get('/forms/new')
    form_page.form['title'] = "My Form"
    form_page.form['lead'] = "This is a form"
    form_page.form['text'] = "There are many like it, but this one's mine"
    form_page.form['definition'] = "email *= @@@"
    form_page = form_page.form.submit().follow()

    assert "Ein neues Formular wurd hinzugefügt" in form_page

    form_page = client.get('/forms/new')
    form_page.form['title'] = "My Form"
    form_page.form['lead'] = "This is a form"
    form_page.form['text'] = "There are many like it, but this one's mine"
    form_page.form['definition'] = "email *= @@@"
    form_page = form_page.form.submit()

    assert "Ein Formular mit diesem Namen existiert bereits" in form_page


def test_forms_explicitly_link_referenced_files(client: Client) -> None:
    admin = client.spawn()
    admin.login_admin()

    path = module_path('tests.onegov.org', 'fixtures/sample.pdf')
    with open(path, 'rb') as f:
        page = admin.get('/files')
        page.form['file'] = [Upload('Sample.pdf', f.read(), 'application/pdf')]
        page.form.submit()

    session = client.app.session()
    pdf = FileCollection(session).query().one()
    pdf_url = (
        admin.get('/files')
        .pyquery(f'[ic-trigger-from="#button-{pdf.id}"]')
        .attr('ic-get-from')
        .removesuffix('/details')
    )
    pdf_link = f'<a href="{pdf_url}">Sample.pdf</a>'

    editor = client.spawn()
    editor.login_editor()

    form_page = editor.get('/forms/new')
    form_page.form['title'] = "My Form"
    form_page.form['lead'] = "This is a form"
    form_page.form['text'] = pdf_link
    form_page.form['definition'] = "email *= @@@"
    form_page = form_page.form.submit().follow()

    pdf = FileCollection(session).query().one()
    form = FormDefinitionCollection(session).by_name('my-form')
    assert form is not None
    assert form.files == [pdf]
    assert pdf.access == 'public'

    form.access = 'mtan'  # type: ignore[attr-defined]
    session.flush()
    assert pdf.access == 'mtan'

    # link removed
    form.files = []
    session.flush()
    assert pdf.access == 'secret'


def test_delete_builtin_form(client: Client) -> None:
    builtin_form = '/form/anmeldung'

    response = client.delete(builtin_form, expect_errors=True)
    assert response.status_code == 403

    client.login_editor()

    response = client.delete(builtin_form, expect_errors=True)
    assert response.status_code == 403


def test_delete_custom_form(client: Client) -> None:
    client.login_editor()

    form_page = client.get('/forms/new')
    form_page.form['title'] = "My Form"
    form_page.form['definition'] = "e-mail * = @@@"
    form_page = form_page.form.submit().follow()

    client.delete(
        form_page.pyquery('a.delete-link')[0].attrib['ic-delete-from'])


def test_show_uploaded_file(client: Client) -> None:
    collection = FormCollection(client.app.session())
    collection.definitions.add(
        'Text', definition="File * = *.txt\nE-Mail * = @@@", type='custom')
    transaction.commit()

    client.login_editor()

    form_page = client.get('/form/text')
    form_page.form['e_mail'] = 'info@example.org'
    form_page.form['file'] = Upload('test.txt', b'foobar')
    form_page = form_page.form.submit().follow()  # preview
    form_page = form_page.form.submit().follow()  # finalize

    ticket_page = client.get(
        form_page.pyquery('.ticket-number a').attr('href'))

    assert 'test.txt' in ticket_page.text
    file_response = ticket_page.click('test.txt', index=0)

    assert file_response.content_type == 'text/plain'
    assert file_response.text == 'foobar'

    assert file_response.cache_control.private
    assert file_response.cache_control.no_cache
    assert not file_response.cache_control.public

    assert client.spawn().get(file_response.request.url, status=404)


def test_hide_form(client: Client) -> None:
    client.login_editor()

    form_page = client.get('/form/anmeldung/edit')
    form_page.form['access'] = 'private'
    page = form_page.form.submit().follow()

    anonymous = client.spawn()
    response = anonymous.get(
        '/form/anmeldung', expect_errors=True)
    assert response.status_code == 403

    edit_page = page.click("Bearbeiten")
    edit_page.form['access'] = 'public'
    page = edit_page.form.submit().follow()

    response = anonymous.get(page.request.url)
    assert response.status_code == 200


def test_change_email(client: Client) -> None:
    collection = FormCollection(client.app.session())
    collection.definitions.add('Newsletter', definition=textwrap.dedent("""
        E-Mail *= @@@
    """), type='custom')

    transaction.commit()

    page = client.get('/form/newsletter')
    page.form['e_mail'] = 'info@example.org'
    page = page.form.submit().follow().form.submit().follow()
    assert "Referenz Anfrage" in page

    client.login_supporter()
    ticket = client.get('/tickets/ALL/open').click("Annehmen").follow()
    assert ticket.pyquery('.ticket-submitter-email a').text() == (
        'info@example.org')

    # change the email
    client.post(
        ticket.pyquery('.ticket-submitter-email').attr('data-edit'),
        {'email': 'new@example.org'}
    )
    ticket = client.get(ticket.request.url)
    assert 'E-Mail Adresse des Antragstellers geändert' in ticket
    assert ticket.pyquery('.ticket-submitter-email a').text() == (
        'new@example.org')


def test_manual_form_payment(client: Client) -> None:
    collection = FormCollection(client.app.session())
    collection.definitions.add('Govikon Poster', definition=textwrap.dedent("""
        E-Mail *= @@@

        Posters *=
            [ ] Local Businesses
            [ ] Executive Committee (10 CHF)
            [ ] Town Square (20 CHF)

        Delivery *=
            ( ) Pickup
            ( ) Delivery (5 CHF)
    """), type='custom')

    transaction.commit()

    page = client.get('/form/govikon-poster')
    assert '10.00 CHF' in page
    assert '20.00 CHF' in page
    assert '5.00 CHF' in page

    page.form['e_mail'] = 'info@example.org'
    page.select_checkbox('posters', "Executive Committee")
    page.select_checkbox('posters', "Town Square")
    page.form['delivery'] = 'Delivery'

    page = page.form.submit().follow()
    assert "Totalbetrag" in page
    assert "35.00 CHF" in page

    page = page.form.submit().follow()
    assert "Referenz Anfrage" in page

    client.login_editor()
    page = client.get('/tickets/ALL/open').click("Annehmen").follow()

    assert page.pyquery('.payment-state').text() == "Offen"

    # view invoice
    invoice = page.click('Rechnung anzeigen')
    assert 'Posters' in invoice
    assert '30.00' in invoice
    assert 'Delivery' in invoice
    assert '5.00' in invoice
    assert '35.00' in invoice
    assert invoice.pyquery('.payment-state').text() == "Offen"

    # mark as paid
    client.post(page.pyquery('.mark-as-paid').attr('ic-post-to'))
    page = client.get(page.request.url)
    assert page.pyquery('.payment-state').text() == "Bezahlt"
    invoice = client.get(invoice.request.url)
    assert invoice.pyquery('.payment-state').text() == "Bezahlt"

    # try to change selections (doesn't work because it would change price)
    form = page.click('Eingabe bearbeiten')
    form.select_checkbox('posters', "Local Businesses")
    form.select_checkbox('posters', "Executive Committee", checked=False)
    form.select_checkbox('posters', "Town Square", checked=False)
    form.form['delivery'] = 'Pickup'
    form = form.form.submit()
    assert 'die Zahlung ist nicht mehr offen' in form

    # mark as unpaid
    client.post(page.pyquery('.mark-as-unpaid').attr('ic-post-to'))
    page = client.get(page.request.url)
    assert page.pyquery('.payment-state').text() == "Offen"
    invoice = client.get(invoice.request.url)
    assert invoice.pyquery('.payment-state').text() == "Offen"

    # change selections again
    form = page.click('Eingabe bearbeiten')
    form.select_checkbox('posters', "Local Businesses")
    form.select_checkbox('posters', "Executive Committee", checked=False)
    form.select_checkbox('posters', "Town Square", checked=False)
    form.form['delivery'] = 'Pickup'
    page = form.form.submit().follow()
    # since we removed all priced options there's no longer a payment
    # but there's also no invoice
    assert page.pyquery('.payment-state').text() == ''
    assert 'Rechnung anzeigen' not in page
    client.get(invoice.request.url, status=404)

    # let's change them again to be priced
    form = page.click('Eingabe bearbeiten')
    form.form['delivery'] = 'Delivery'
    page = form.form.submit().follow()
    # now we should once again have a payment and invoice
    assert page.pyquery('.payment-state').text() == 'Offen'
    invoice = page.click('Rechnung anzeigen')
    assert invoice.pyquery('.payment-state').text() == "Offen"
    assert '5.00' in invoice

    # let's add a surcharge
    item = invoice.click('Abzug / Zuschlag')
    item.form['booking_text'] = 'Handling Fee'
    item.form['kind'] = 'surcharge'
    item.form['surcharge'] = '5.00'
    item.form.submit()

    # and change one of the selections again
    form = page.click('Eingabe bearbeiten')
    form.select_checkbox('posters', "Executive Committee")
    page = form.form.submit().follow()
    invoice = page.click('Rechnung anzeigen')
    assert 'Posters' in invoice
    assert '10.00' in invoice
    assert 'Delivery' in invoice
    assert '5.00' in invoice
    assert 'Handling Fee' in invoice
    assert '20.00' in invoice
    assert invoice.pyquery('.payment-state').text() == "Offen"

    # let's delete the surcharge
    client.delete(
        invoice.pyquery('.remove-invoice-item').attr('ic-delete-from')
    )
    invoice = client.get(invoice.request.url)
    assert 'Posters' in invoice
    assert '10.00' in invoice
    assert 'Delivery' in invoice
    assert '5.00' in invoice
    assert 'Handling Fee' not in invoice
    assert '15.00' in invoice
    assert invoice.pyquery('.payment-state').text() == "Offen"

    payments = client.get('/payments')
    assert "FRM-" in payments
    assert "Manuell" in payments
    assert "info@example.org" in payments
    assert "15.00" in payments
    assert "Offen" in payments


def test_form_payment_required(client: Client) -> None:
    collection = FormCollection(client.app.session())
    collection.definitions.add('Govikon Poster', definition=textwrap.dedent("""
        E-Mail *= @@@

        Posters *=
            [ ] Local Businesses (0 CHF)
            [ ] Executive Committee (10 CHF)
            [ ] Town Square (20 CHF)

        Delivery *=
            ( ) Pickup (0 CHF)
            ( ) Delivery (5 CHF!)
    """), type='custom', payment_method='free')

    transaction.commit()

    page = client.get('/form/govikon-poster')
    assert '10.00 CHF' in page
    assert '20.00 CHF' in page
    assert '5.00 CHF' in page

    page.form['e_mail'] = 'info@example.org'
    page.select_checkbox('posters', "Executive Committee")
    page.select_checkbox('posters', "Town Square")
    page.form['delivery'] = 'Delivery'

    page = page.form.submit().follow()
    assert "Totalbetrag" in page
    assert "35.00 CHF" in page
    # even though the payment method is 'free', because we selected
    # an option that requires cc payment, it should only allow cc
    # payment
    assert "Später bezahlen" not in page


def test_dependent_number_form(client: Client) -> None:
    collection = FormCollection(client.app.session())
    collection.definitions.add('Profile', definition=textwrap.dedent("""
        E-Mail *= @@@
        Country =
            ( ) Switzerland
                Email *= @@@
            (x) Other
    """), type='custom')

    transaction.commit()

    page = client.get('/form/profile')
    page.form['e_mail'] = 'info@example.org'
    page = page.form.submit().follow()

    assert "Bitte überprüfen Sie Ihre Angaben" in page


def test_registration_form_hints(client: Client) -> None:
    collection = FormCollection(client.app.session())
    collection.definitions.add('Meetup', "E-Mail *= @@@", 'custom')
    transaction.commit()

    client.login_editor()

    page = client.get('/form/meetup')
    page = page.click("Hinzufügen")

    page.form['start'] = '2018-01-01'
    page.form['end'] = '2018-01-31'
    page.form['limit_attendees'] = 'yes'
    page.form['limit'] = 2
    page.form['waitinglist'] = 'yes'
    page.form['stop'] = False
    page = page.form.submit().follow()

    assert "Der Anmeldezeitraum wurde erfolgreich hinzugefügt" in page

    # the time here is in UTC, offset is +1 hour
    with freeze_time('2017-12-31 22:59:59'):
        page = client.get('/form/meetup')
        assert "Die Anmeldung beginnt am Montag, 01. Januar 2018" in page

    with freeze_time('2017-12-31 23:00:00'):
        page = client.get('/form/meetup')
        assert "Die Anmeldung endet am Mittwoch, 31. Januar 2018" in page

    with freeze_time('2018-01-31 22:59:59'):
        page = client.get('/form/meetup')
        assert "Die Anmeldung endet am Mittwoch, 31. Januar 2018" in page

    with freeze_time('2018-01-31 23:00:00'):
        page = client.get('/form/meetup')
        assert "Die Anmeldung ist nicht mehr möglich" in page

    edit = page.click('01.01.2018 - 31.01.2018').click('Bearbeiten')
    edit.form['stop'] = True
    edit.form.submit()

    with freeze_time('2018-01-01'):
        page = client.get('/forms')
        assert 'Meetup' in page
        assert "Zur Zeit keine Anmeldung möglich" in page

        page = client.get('/form/meetup')
        assert "Zur Zeit keine Anmeldung möglich" in page

        edit.form['stop'] = False
        edit.form.submit()

        page = client.get('/forms')
        assert 'Meetup' in page
        assert "Die Anmeldung endet am Mittwoch, 31. Januar 2018" in page
        assert "Die Anmeldung ist auf 2 Teilnehmer begrenzt" in page

        page = client.get('/form/meetup')
        assert "Die Anmeldung endet am Mittwoch, 31. Januar 2018" in page
        assert "Die Anmeldung ist auf 2 Teilnehmer begrenzt" in page

        edit.form['waitinglist'] = 'no'
        edit.form.submit()

        page = client.get('/forms')
        assert 'Meetup' in page
        assert "Es sind noch 2 Plätze verfügbar" in page

        page = client.get('/form/meetup')
        assert "Es sind noch 2 Plätze verfügbar" in page

        edit.form['limit'] = 1
        edit.form.submit()

        page = client.get('/forms')
        assert 'Meetup' in page
        assert "Es ist noch ein Platz verfügbar" in page

        page = client.get('/form/meetup')
        assert "Es ist noch ein Platz verfügbar" in page

        page.form['e_mail'] = 'info@example.org'
        page.form.submit().follow().form.submit()

        page = client.get('/forms')
        assert 'Meetup' in page
        assert "Keine Plätze mehr verfügbar" in page

        page = client.get('/form/meetup')
        assert "Keine Plätze mehr verfügbar" in page


def test_registration_complete_after_deadline(client: Client) -> None:
    collection = FormCollection(client.app.session())

    form = collection.definitions.add('Meetup', "E-Mail *= @@@", 'custom')
    form.add_registration_window(
        start=date(2018, 1, 1),
        end=date(2018, 1, 31),
    )

    transaction.commit()

    # the registration is started before the end of the deadline
    with freeze_time('2018-01-31 22:59:59'):
        page = client.get('/form/meetup')
        page.form['e_mail'] = 'info@example.org'
        page = page.form.submit().follow()

    # but it is completed after the deadline (no longer possible)
    with freeze_time('2018-01-31 23:00:00'):
        page = page.form.submit().follow()
        assert "Anmeldungen sind nicht mehr möglich" in page
        assert TicketCollection(client.app.session()).query().count() == 0


def test_registration_race_condition(client: Client) -> None:
    collection = FormCollection(client.app.session())

    form = collection.definitions.add('Meetup', "E-Mail *= @@@", 'custom')
    form.add_registration_window(
        start=date(2018, 1, 1),
        end=date(2018, 1, 31),
        limit=1,
        overflow=False
    )

    transaction.commit()

    foo = client.spawn()
    bar = client.spawn()

    def fill_out_form(client: Client) -> ExtendedResponse:
        page = client.get('/form/meetup')
        page.form['e_mail'] = 'info@example.org'

        return page.form.submit().follow()

    def complete_form(page: ExtendedResponse) -> ExtendedResponse:
        return page.form.submit().follow()

    with freeze_time('2018-01-01'):
        foo_page = fill_out_form(foo)
        bar_page = fill_out_form(bar)

        assert "Vielen Dank für Ihre Eingabe" in complete_form(foo_page)
        assert "Anmeldungen sind nicht mehr möglich" in complete_form(bar_page)


def test_registration_change_limit_after_submissions(client: Client) -> None:
    collection = FormCollection(client.app.session())

    form = collection.definitions.add('Meetup', "E-Mail *= @@@", 'custom')
    form.add_registration_window(
        start=date(2018, 1, 1),
        end=date(2018, 1, 31),
        limit=10,
        overflow=False
    )

    transaction.commit()

    client.login_editor()

    with freeze_time('2018-01-01', tick=True):
        for i in range(0, 3):
            page = client.get('/form/meetup')
            page.form['e_mail'] = 'info@example.org'
            page.form.submit().follow().form.submit().follow()

    page = client.get('/form/meetup').click('01.01.2018 - 31.01.2018')
    page = page.click('Bearbeiten')

    page.form['limit'] = 1
    assert "nicht tiefer sein als die Summe" in page.form.submit()

    submissions = collection.submissions.query().all()
    submissions[0].claim()
    submissions[1].claim()
    transaction.commit()

    page.form['waitinglist'] = 'yes'
    assert "nicht tiefer sein als die Anzahl" in page.form.submit()

    page.form['waitinglist'] = 'no'
    page.form['limit'] = 2
    assert "nicht tiefer sein als die Summe" in page.form.submit()

    submissions = collection.submissions.query().all()
    submissions[2].disclaim()
    transaction.commit()

    page = page.form.submit().follow()
    assert "Ihre Änderungen wurden gespeichert" in page

    submissions = collection.submissions.query().all()
    submissions[1].disclaim()
    transaction.commit()

    page = page.click('01.01.2018 - 31.01.2018').click('Bearbeiten')
    page.form['limit'] = 1
    page = page.form.submit().follow()

    assert "Ihre Änderungen wurden gespeichert" in page


def test_registration_window_adjust_end_date(client: Client) -> None:
    collection = FormCollection(client.app.session())

    form = collection.definitions.add(
        'Meet Guido van Rossum', "E-Mail *= @@@", 'custom')
    form.add_registration_window(
        start=date(2024, 4, 1),
        end=date(2024, 4, 2),
        limit=None,
        overflow=False
    )
    transaction.commit()

    client.login_editor()

    # change end date before first submission confirmed
    with freeze_time('2024-04-01', tick=True):
        # submit form prior adjusting end date
        page = client.get('/form/meet-guido-van-rossum')
        page.form['e_mail'] = 'guido_fan@example.org'
        page.form.submit().follow().form.submit().follow()

        # adjust end date
        page = (client.get('/form/meet-guido-van-rossum').
                click('01.04.2024 - 02.04.2024'))
        page = page.click('Bearbeiten')
        page.form['end'] = '2024-04-03'
        result = page.form.submit().follow()
        assert 'Anmeldezeitraum bearbeiten' not in result
        assert 'Ihre Änderungen wurden gespeichert' in result

    # confirm first submission and change registration end date
    with freeze_time('2024-04-01', tick=True):
        # accept ticket, confirm
        accept_submission = (client.get('/tickets/ALL/open').
                             click("Annehmen").follow())
        accept_submission.click("Anmeldung bestätigen").follow()
        assert accept_submission.status_code == 200

        # change end date
        page = (client.get('/form/meet-guido-van-rossum').
                click('01.04.2024 - 03.04.2024'))
        page = page.click('Bearbeiten')
        page.form['end'] = '2024-04-04'
        result = page.form.submit().follow()
        assert 'Anmeldezeitraum bearbeiten' not in result
        assert 'Ihre Änderungen wurden gespeichert' in result


def test_registration_ticket_workflow(client: Client) -> None:
    session = client.app.session()
    collection = FormCollection(session)
    users = UserCollection(session)

    form = collection.definitions.add('Meetup', textwrap.dedent("""
        E-Mail *= @@@
        Name *= ___
    """), 'custom')
    session.flush()

    window = form.add_registration_window(
        start=date(2018, 1, 1),
        end=date(2018, 1, 31),
        limit=10,
        overflow=False
    )
    session.flush()
    window_id = window.id
    assert window_id is not None
    username = 'automaton@example.org'
    user_id = users.add(username, 'testing', 'admin').id
    transaction.commit()

    count = 0

    def register(
        client: Client,
        data_in_email: bool,
        accept_ticket: bool = True,
        url: str = '/form/meetup'
    ) -> ExtendedResponse:
        nonlocal count
        count += 1
        with freeze_time(f'2018-01-01 00:00:{count:02d}'):
            page = client.get(url)
            page.form['e_mail'] = f'info{count}@example.org'
            page.form['name'] = 'Foobar'
            page = page.form.submit().follow()

            page.form['send_by_email'] = data_in_email
            page = page.form.submit().follow()
        if not accept_ticket:
            return page
        return client.get('/tickets/ALL/open').click("Annehmen").follow()

    client.login_supporter()
    page = register(client, data_in_email=True)

    assert "bestätigen" in page
    assert "ablehnen" in page

    msg = client.get_email(-1)['TextBody']
    assert "Ihre Anfrage wurde unter der folgenden Referenz registriert" in msg
    assert "Foobar" in msg

    page = page.click("Anmeldung bestätigen").follow()

    msg = client.get_email(-1)['TextBody']
    assert 'Ihre Anmeldung für "Meetup" wurde bestätigt' in msg
    assert "01.01.2018 - 31.01.2018" in msg
    assert "Foobar" in msg

    page.click("Anmeldung stornieren").follow()

    msg = client.get_email(-1)['TextBody']
    assert 'Ihre Anmeldung für "Meetup" wurde storniert' in msg
    assert "01.01.2018 - 31.01.2018" in msg
    assert "Foobar" in msg

    page = register(client, data_in_email=False)

    msg = client.get_email(-1)['TextBody']
    assert "Ihre Anfrage wurde unter der folgenden Referenz registriert" in msg
    assert "Foobar" not in msg

    page.click("Anmeldung ablehnen")

    msg = client.get_email(-1)['TextBody']
    assert 'Ihre Anmeldung für "Meetup" wurde abgelehnt' in msg
    assert "01.01.2018 - 31.01.2018" in msg
    assert "Foobar" not in msg

    # create one undecided submission
    register(client, False, accept_ticket=False)

    # Test auto accept reservations for forms
    # views in order:
    # - /form/meetup
    # - /form-preview/{id} mit submit convert Pending in CompleteFormSubmission
    # confirm link: request.link(self.submission, 'confirm-registration')

    client.login_admin()
    settings = client.get('/ticket-settings')
    # skip_opening_email has not effect for the auto-accept setting
    # this opening mail is never sent, instead the confirmation directly
    settings.form['ticket_auto_accepts'] = ['FRM']
    settings.form['auto_closing_user'] = username
    settings.form.submit().follow()

    client = client.spawn()
    page = register(client, False, accept_ticket=False)
    mail = client.get_email(-1)
    assert mail is not None
    assert 'Meetup: Ihre Anmeldung wurde bestätigt' in mail['Subject']
    assert 'Ihr Anliegen wurde abgeschlossen' in page

    # check ownership of the ticket
    client.app.session().query(Ticket).filter_by(user_id=user_id).one()

    client.login_editor()
    # We rename the form and check if everything still works
    rename_page = client.get('/form/meetup').click('URL ändern')
    assert rename_page.form['name'].value == 'meetup'

    rename_page = rename_page.form.submit()
    assert 'Bitte geben sie einen neuen Namen an' in rename_page

    rename_page.form['name'] = 'ME'
    rename_page = rename_page.form.submit()
    assert 'Ungültiger Name. Ein gültiger Vorschlag ist' in rename_page

    rename_page.form['name'] = 'meetings'
    rename_page = rename_page.form.submit().follow()
    new_url = rename_page.request.url
    assert 'meetings' in new_url

    # Reopen the last
    page = client.get('/tickets/ALL/closed')
    last_ticket = page.pyquery('td.ticket-number-plain a').attr('href')
    ticket = client.get(last_ticket).click('Ticket wieder öffnen').follow()
    window_page = ticket.click('Anmeldezeitraum')
    assert 'Offen (1)' in window_page
    assert 'Bestätigt (1)' in window_page
    assert 'Storniert (2)' in window_page

    message = window_page.click('E-Mail an Teilnehmende')
    message.form['message'] = 'Message for all the attendees'
    message.form['registration_state'] = ['open', 'cancelled', 'confirmed']
    page = message.form.submit().follow()
    assert 'Erfolgreich 4 E-Mails gesendet' in page

    latest_ticket_note = (
        client.app.session().query(TicketNote)
        .order_by(TicketNote.created.desc())
        .first()
    )
    assert latest_ticket_note is not None
    assert "Neue E-Mail" in latest_ticket_note.text

    mail = client.get_email(-1)
    assert mail is not None
    assert 'Message for all the attendees' in mail['HtmlBody']
    assert 'Allgemeine Nachricht' in mail['Subject']

    # navigate to the registration window an cancel all
    window_page.click('Anmeldezeitraum absagen')
    page = client.get(window_page.request.url)
    assert 'Storniert (4)' in page

    ticket_url = page.pyquery('.field-display a:first-of-type').attr('href')

    # we have the case since the ticket deletion mixin that there might be
    # a submission without the ticket
    session = client.app.session()
    session.query(Ticket).delete('fetch')
    transaction.commit()

    # the window is no longer accesible through the ticket
    page = client.get(window_page.request.url, status=404)

    # the link to the deleted ticket is gone from the window view
    page = client.get(f'/form-registration-window/{window_id.hex}')
    assert not page.pyquery('.field-display a')

    client.get(ticket_url, status=404)

    # Try deleting the form with active registrations window
    form_page = client.get('/form/meetings')
    assert 'Dies kann nicht rückgängig gemacht werden.' in form_page.pyquery(
        '.delete-link.confirm').attr('data-confirm-extra')

    form_delete_link = form_page.pyquery(
        '.delete-link.confirm').attr('ic-delete-from')

    client.delete(form_delete_link, status=200)


def test_registration_not_in_front_of_queue(client: Client) -> None:
    collection = FormCollection(client.app.session())

    form = collection.definitions.add('Meetup', "E-Mail *= @@@", 'custom')
    form.add_registration_window(
        start=date(2018, 1, 1),
        end=date(2018, 1, 31),
        limit=10,
        overflow=False
    )

    transaction.commit()

    client.login_editor()

    with freeze_time('2018-01-01', tick=True):
        for i in range(0, 2):
            page = client.get('/form/meetup')
            page.form['e_mail'] = 'info@example.org'
            page.form.submit().follow().form.submit().follow()

    # NOTE: due to time ticking these are now ordered differently
    #       so the older entry in the queue is now at index=0
    page = client.get('/tickets/ALL/open').click("Annehmen", index=0).follow()
    assert "Dies ist nicht die älteste offene Eingabe" in page

    page = client.get('/tickets/ALL/open').click("Annehmen").follow()
    assert "Dies ist nicht die älteste offene Eingabe" not in page


def test_markdown_in_forms(client: Client) -> None:
    collection = FormCollection(client.app.session())
    collection.definitions.add('Content', definition=textwrap.dedent("""
        E-Mail *= @@@
        Content = <markdown>
    """), type='custom')

    transaction.commit()

    page = client.get('/forms').click('Content')
    page.form['e_mail'] = 'info@example.org'
    page.form['content'] = '* foo\n* bar'
    page = page.form.submit().follow()

    assert '<li>foo</li>' in page
    assert '<li>bar</li>' in page


def test_exploit_markdown_in_forms(client: Client) -> None:
    collection = FormCollection(client.app.session())
    collection.definitions.add('Content', definition=textwrap.dedent("""
        E-Mail *= @@@
        Content = <markdown>
    """), type='custom')

    transaction.commit()

    page = client.get('/forms').click('Content')
    page.form['e_mail'] = 'info@example.org'
    page.form['content'] = '<script>alert();</script>'
    page = page.form.submit().follow()

    assert '<script>alert' not in page
    assert '&lt;script&gt;alert' in page


def test_honeypotted_forms(client: Client) -> None:
    client.login_editor()

    # this error is not strictly line based, so there's a general error
    new_form = client.get('/forms/new')
    new_form.form['title'] = 'My Form'
    new_form.form['lead'] = 'This is a form'
    new_form.form['text'] = 'There are not many like it'
    new_form.form['definition'] = 'E-Mail * = @@@'
    new_form.form.submit().follow()

    form_page = client.get('/forms/').click('My Form')
    assert 'duplicate_of' in form_page
    assert 'lazy-wolves' in form_page
    assert 'honeypot' not in form_page

    # Honeypot not used
    form_page = client.get('/forms/').click('My Form')
    form_page.form['e_mail'] = 'test@example.com'
    preview_page = form_page.form.submit().maybe_follow()
    assert 'duplicate_of' not in preview_page
    assert 'lazy-wolves' not in preview_page
    assert 'honeypot' not in preview_page
    assert 'Das Formular enthält Fehler' not in preview_page

    # Honeypot used
    form_page = client.get('/forms/').click('My Form')
    form_page.form['e_mail'] = 'test@example.com'
    form_page.form['duplicate_of'] = 'abc'
    submission_page = form_page.form.submit().maybe_follow()
    assert 'duplicate_of' in submission_page
    assert 'lazy-wolves' in submission_page
    assert 'honeypot' not in submission_page
    assert 'Das Formular enthält Fehler' in submission_page

    submission_page = submission_page.form.submit()
    assert 'duplicate_of' in submission_page
    assert 'lazy-wolves' in submission_page
    assert 'honeypot' not in submission_page
    assert 'Das Formular enthält Fehler' in submission_page

    # Honeypot disabled
    edit_form = client.get('/forms/').click('My Form').click('Bearbeiten')
    edit_form.form['honeypot'] = ''
    edit_form.form.submit()

    form_page = client.get('/forms/').click('My Form')
    assert 'duplicate_of' not in form_page
    assert 'lazy-wolves' not in form_page

    form_page.form['e_mail'] = 'test@example.com'
    preview_page = form_page.form.submit().maybe_follow()
    assert 'duplicate_of' not in preview_page
    assert 'lazy-wolves' not in preview_page
    assert 'honeypot' not in preview_page
    assert 'Das Formular enthält Fehler' not in preview_page


def test_edit_page_people_function_is_displayed(client: Client) -> None:

    client.login_admin()

    people = client.get('/people')
    new_person = people.click('Person')
    new_person.form['first_name'] = 'Berry'
    new_person.form['last_name'] = 'Boolean'
    new_person.form.submit()
    berry = (
        client.app.session().query(Person)
        .filter(Person.first_name == 'Berry')
        .one()
    )

    new_page = client.get('/editor/new/page/1')
    option = new_page.pyquery(f'#people-0 option[value="{berry.id.hex}"]')
    assert option.attr('data-function') is None
    assert option.attr('data-show') is None

    people = client.get('/people')
    new_person = people.click('Person')
    new_person.form['first_name'] = 'John'
    new_person.form['last_name'] = 'Doe'
    new_person.form['function'] = 'President'
    new_person.form.submit()
    john = (
        client.app.session().query(Person)
        .filter(Person.first_name == 'John')
        .one()
    )

    new_page = client.get('/editor/new/page/1')
    option = new_page.pyquery(f'#people-0 option[value="{john.id.hex}"]')
    assert option.attr('data-function') == 'President'
    assert option.attr('data-show') is None

    new_page.form['title'] = "Living in Govikon is Swell"
    new_page.form['people-0-person'] = john.id.hex
    new_page.form['people-0-context_specific_function'] = 'Vice-President'
    new_page.form['people-0-display_function_in_person_directory'] = True
    page = new_page.form.submit().follow()

    # once we have chosen something the chosen value takes precedence
    edit_page = page.click("Bearbeiten")
    option = edit_page.pyquery(f'#people-0 option[value="{john.id.hex}"]')
    assert option.attr('data-function') == 'Vice-President'
    assert option.attr('data-show') == 'true'


def test_event_configuration_validation(client: Client) -> None:
    """
    Tests ValidFilterFormDefinition only allows Radio and Checkbox
    fields.
    """

    client.login_admin()

    page = client.get('/events/+edit')
    page.form['definition'] = """
    Kalender *=
        ( ) Sport Veranstaltungskalender
        ( ) Agenda Verkehrsgarten
    Sportart =
        [ ] Volleyball
        [ ] Walking
    Email Adresse = @@@
    """
    page.form['keyword_fields'] = ['kalender', 'sportart']
    page = page.form.submit()
    assert 'Invalid field type for field \'Email Adresse\'.' in page

    # test multiple errors
    page = client.get('/events/+edit')
    page.form['definition'] = """
    Kalender *=
        ( ) Sport Veranstaltungskalender
        ( ) Agenda Verkehrsgarten
    Text = ___
    Sportart =
        [ ] Volleyball
        [ ] Walking
    Webpage = https://srf.ch
    """
    page.form['keyword_fields'] = ['kalender', 'sportart']
    page = page.form.submit()
    assert 'Invalid field type for field \'Text\'.' in page
    assert 'Invalid field type for field \'Webpage\'.' in page


def test_file_export_for_ticket(
    client: Client,
    temporary_directory: str
) -> None:

    collection = FormCollection(client.app.session())
    collection.definitions.add('Statistics', definition=textwrap.dedent("""
        E-Mail * = @@@
        Name * = ___
        Datei * = *.txt
        Datei2 * = *.txt """), type='custom')
    transaction.commit()

    client.login_admin()
    page = client.get('/forms').click('Statistics')

    page.form['name'] = 'foobar'
    page.form['e_mail'] = 'foo@bar.ch'
    page.form['datei'] = Upload('README1.txt', b'first')
    page.form['datei2'] = Upload('README2.txt', b'second')

    form_page = page.form.submit().follow()

    assert 'README1.txt' in form_page.text
    assert 'README2.txt' in form_page.text
    assert 'Abschliessen' in form_page.text

    form_page.form.submit()

    ticket_page = client.get('/tickets/ALL/open').click("Annehmen").follow()

    assert 'Dateien herunterladen' in ticket_page.text
    file_response = ticket_page.click('Dateien herunterladen')

    assert file_response.content_type == 'application/zip'

    with zipfile.ZipFile(BytesIO(file_response.body), 'r') as zip_file:
        zip_file.extractall(temporary_directory)
        file_names = sorted(zip_file.namelist())

        assert {'README1.txt', 'README2.txt'}.issubset(file_names)

        for file_name, content in zip(file_names, [b'first', b'second']):
            with zip_file.open(file_name) as fp:
                extracted_file_content = fp.read()
                assert extracted_file_content == content

    # test one where the file got deleted
    page.form['name'] = 'foobar'
    page.form['e_mail'] = 'foo@bar.ch'
    page.form['datei'] = Upload('README3.txt', b'third')
    page.form['datei2'] = Upload('README4.txt', b'fourth')

    form_page = page.form.submit().follow()

    assert 'README3.txt' in form_page.text
    assert 'README4.txt' in form_page.text
    assert 'Abschliessen' in form_page.text

    form_page.form.submit()

    files = FileCollection(client.app.session())
    file = files.by_filename('README3.txt').one()
    client.app.session().delete(file)
    client.app.session().flush()

    ticket_page = client.get('/tickets/ALL/open').click("Annehmen").follow()

    # the deleted file is not in the zip
    file_response = ticket_page.click('Dateien herunterladen')

    assert file_response.content_type == 'application/zip'

    with zipfile.ZipFile(BytesIO(file_response.body), 'r') as zip_file:
        zip_file.extractall(temporary_directory)
        file_names = sorted(zip_file.namelist())

        assert 'README3.txt' not in file_names

        for file_name, content in zip(file_names, [b'fourth']):
            with zip_file.open(file_name) as fp:
                extracted_file_content = fp.read()
                assert extracted_file_content == content

    # testing something like "Datei * = *.txt (multiple)" would require
    # webtest to support multiple file upload which will come on 3.0.1


def test_create_and_fill_survey(client: Client) -> None:
    client.login_editor()
    anonymous = client.spawn()

    # Create a survey
    page = client.get('/surveys/new')
    page.form['title'] = 'Event Evaluation'
    page.form['lead'] = 'Evaluation for the best event'
    page.form['definition'] = textwrap.dedent("""
        Name = ___
        How was the event? =
            (x) Good
            ( ) Medium
            ( ) Bad
    """)
    page = page.form.submit().follow()
    assert "Event Evaluation" in page

    # Fill out the survey
    page = anonymous.get('/survey/event-evaluation')
    page.form['name'] = 'Nicolas Thomas'
    page.form['how_was_the_event_'] = 'Good'
    page = page.form.submit()

    # Check the results
    page = client.get('/survey/event-evaluation').click('Resultate')
    assert 'Nicolas Thomas' in page
    assert 'Good' in page
    assert '(1/1)' in page

    # Create submission window
    yesterday = date.today() - timedelta(days=1)
    tomorrow = date.today() + timedelta(days=1)
    page = client.get('/survey/event-evaluation').click('Hinzufügen')
    page.form['title'] = 'Team 1'
    page.form['start'] = yesterday
    page.form['end'] = tomorrow
    page = page.form.submit().follow()
    assert 'Der Anmeldezeitraum wurde erfolgreich hinzugefügt' in page

    # Try to create a window with the same time without a title
    page = client.get('/survey/event-evaluation').click('Hinzufügen')
    page.form['title'] = ''
    page.form['start'] = yesterday
    page.form['end'] = tomorrow
    page = page.form.submit()
    y = yesterday.strftime('%d.%m.%Y')
    t = tomorrow.strftime('%d.%m.%Y')
    assert f"Befragungszeitraum ({y} - {t})." in page

    # Give the window a title
    page.form['title'] = 'Team 2'
    page = page.form.submit().follow()
    assert 'Der Anmeldezeitraum wurde erfolgreich hinzugefügt' in page
    page = client.get('/survey/event-evaluation').click('Team 2')
    url = page.request.url

    # Try to access the survey without the window
    page = anonymous.get('/survey/event-evaluation', expect_errors=True)
    assert page.status_code == 403

    # Try to access the survey with the window
    page = anonymous.get(url)
    page.form['name'] = 'Rubus Bubus'
    page.form['how_was_the_event_'] = 'Medium'
    page = page.form.submit()

    # Check the results
    page = client.get('/survey/event-evaluation').click('Resultate')
    assert 'Nicolas Thomas' in page
    assert 'Good' in page
    assert 'Rubus Bubus' in page
    assert 'Medium' in page
    assert '(1/2)' in page

    # Check submission window results
    page = page.click('Team 2')
    assert 'Rubus Bubus' in page
    assert 'Medium' in page
    assert '(1/1)' in page
    assert 'Nicolas Thomas' not in page


def test_document_form(client: Client) -> None:

    session = client.app.session()
    client.login_editor()

    with TemporaryDirectory() as td:
        first_pdf = os.path.join(td, 'first_pdf.pdf')
        create_pdf(first_pdf, 'This is the wrong form')
        other_pdf = os.path.join(td, 'other_pdf.pdf')
        create_pdf(other_pdf, 'This is a deadline extension form')

        page = client.get('/forms')
        page = page.click('Dokumentenformular')
        page.form['title'] = 'Deadline Extension'
        page.form['lead'] = 'Request a deadline extension'
        page.form['text'] = '''
            Fill out the form below to request a deadline extension.
        '''
        page.form['pdf'] = Upload(first_pdf)
        page = page.form.submit().follow()
        assert 'Formular herunterladen'
        assert 'Deadline Extension' in page
        assert 'Request a deadline extension' in page
        assert '''
            Fill out the form below to request a deadline extension.
        ''' in page
        assert 'first_pdf.pdf' in page
        form_document = session.query(FormDocument).one()
        assert form_document.pdf_extract is not None
        assert 'This is the wrong form' in form_document.pdf_extract

        page = page.click('Bearbeiten')
        page.form['title'] = 'Deadline Extension Request'

        page.form.get('pdf', 0).select('replace')
        page.form.get('pdf', 1).value = Upload(other_pdf)
        page = page.form.submit().follow()
        assert 'Deadline Extension Request' in page
        assert 'other_pdf.pdf' in page
        form_document = session.query(FormDocument).one()
        assert form_document.pdf_extract is not None
        assert 'This is a deadline extension form' in form_document.pdf_extract
