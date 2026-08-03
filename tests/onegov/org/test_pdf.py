from __future__ import annotations

import transaction

from datetime import datetime, date, UTC
from io import BytesIO
from onegov.core.utils import Bunch
from onegov.directory import DirectoryCollection, DirectoryConfiguration
from onegov.form import FormCollection
from onegov.org.models.ticket import ReservationTicket
from onegov.org.models import TicketMessage, TicketChatMessage
from onegov.org.pdf.directory_entry import DirectoryEntryPdf
from onegov.org.pdf.ticket import TicketBasePdf, TicketPdf
from onegov.pdf.utils import extract_pdf_info
from onegov.reservation import ResourceCollection
from onegov.ticket import TicketCollection
from tests.onegov.pdf.test_pdf import LONGEST_TABLE_CELL_TEXT
from textwrap import dedent
from webob.multidict import MultiDict


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.form import Form, FormSubmission
    from onegov.org.models import ExtendedDirectory, ExtendedDirectoryEntry
    from onegov.org.request import OrgRequest
    from onegov.reservation import Resource
    from onegov.ticket import Ticket
    from sqlalchemy.orm import Session
    from uuid import UUID
    from .conftest import Client, TestOrgApp


def open_ticket(
    request: OrgRequest,
    token: str,
    handler_code: str,
    create_message: bool = True
) -> Ticket:
    with request.session.no_autoflush:
        ticket = TicketCollection(request.session).open_ticket(
            handler_code=handler_code, handler_id=token
        )
        ticket.handler.refresh_invoice_items(request, None)
        if create_message:
            TicketMessage.create(ticket, request, 'opened')
    return ticket


def add_submission(
    session: Session,
    resource: Resource,
    token: UUID
) -> FormSubmission | None:
    # add the submission if it doesn't yet exist
    forms = FormCollection(session)
    submission = None
    if resource.definition:
        submission = forms.submissions.add_external(
            form=resource.form_class(),  # type: ignore[misc]
            state='pending',
            id=token,
            payment_method=resource.payment_method
        )
    return submission


def update_submission(
    session: Session,
    submission: FormSubmission,
    form: Form
) -> None:
    # update the data on the submission
    forms = FormCollection(session)
    if submission:
        forms.submissions.update(submission, form)


def add_ticket_message(
    request: OrgRequest,
    ticket: Ticket,
    text: str
) -> TicketChatMessage:
    message = TicketChatMessage.create(
        ticket, request,
        text=text,
        owner='info@example.org',
        recipient=None,
        notify=False,
        origin='internal')
    return message


def test_ticket_pdf(org_app: TestOrgApp) -> None:

    session = org_app.session()
    libres_context = org_app.libres_context
    owner = 'info@example.org'

    def get_translate(**kwargs: object) -> Any:
        return org_app.chameleon_translations.get('de_CH')

    def get_form(form_cls: type[Form], **kwargs: object) -> Form:
        form = form_cls(meta={'request': request})
        form.request = request
        return form

    def class_link(cls: type[object], *args: object, **kwargs: object) -> str:
        return cls.__name__

    def link(*args: object, **kwargs: object) -> str:
        name = kwargs.pop('name')
        return f'https://seantis.ch/{name or ""}'

    template_loader = (
        org_app.config.template_engine_registry._template_loaders['.pt'])

    host_url = '127.0.0.1:8080'

    request: Any = Bunch(
        app=org_app,
        translate=lambda x: x,
        session=session,
        include=lambda x: None,
        current_username=owner,
        is_manager=True,
        is_manager_for_model=lambda model: True,
        get_translate=get_translate,
        get_form=get_form,
        locale='de_CH',
        host_url=host_url,
        class_link=class_link,
        link=link,
        url='',
        template_loader=template_loader
    )
    collection = ResourceCollection(libres_context)
    forms = FormCollection(session)
    room = collection.add(
        'Stairway to Heaven',
        'Europe/Zurich',
        type='room',
        definition='# Data\nName *= ___',
        content={
            'pricing_method': 'per_hour',
            'price_per_hour': 50.0
        }
    )

    scheduler = room.get_scheduler(libres_context)
    dates = (datetime(2017, 6, 7, 12), datetime(2017, 6, 7, 18))
    scheduler.allocate(dates)

    token = scheduler.reserve(owner, dates)
    submission = add_submission(session, room, token)
    assert submission is not None

    form_data = MultiDict([('data_name', 'John')])

    # We skip the combining ReservationForm and the form from definition
    form = room.form_class(form_data)  # type: ignore[misc]
    assert form.validate()
    update_submission(session, submission, form)

    # scheduler.approve_reservations(token)
    reservation = scheduler.reservations_by_token(token).one()
    assert reservation
    ticket = open_ticket(request, str(token), 'RSV', True)
    assert isinstance(ticket, ReservationTicket)

    add_ticket_message(request, ticket, LONGEST_TABLE_CELL_TEXT)

    # We have to mitigate the case but its hard since we deal with html
    add_ticket_message(request, ticket, 2 * LONGEST_TABLE_CELL_TEXT)

    assert ticket.handler.resource

    # is the ticket object session
    assert ticket.handler.session
    submission = forms.submissions.by_id(token)

    # the pdf must be able tp parse the ticket snapshots
    summary = ticket.handler.get_summary(request)
    assert 'John' in summary

    # check the fieldset coming as h2, whenever templates are changed, this
    # is gonna be bad, since the snapshots are still in the old format
    assert 'Data' in summary
    assert submission

    pdf = TicketPdf.from_ticket(request, ticket)

    _, page = extract_pdf_info(pdf)
    assert 'John' in page
    assert 'Data' in page

    assert f'Herkunft: {host_url}' in page
    assert date.today().strftime("%d.%m.%Y") in page

    metadata = ('Betreff', 'Antragsteller/in', 'Status', 'Gruppe', 'Zuständig',
                'Erstellt', 'Reaktionszeit', 'Bearbeitungszeit')

    titles = ('Zusammenfassung', 'Aktivität', 'Rechnung')

    for entry in metadata:
        assert entry in page

    for title in titles:
        assert title in page


def test_ticket_pdf_long_message(client: Client) -> None:
    """PDF generation must not fail when a ticket message is long:

    https://reportlab-users.reportlab.narkive.com/4eO58iDH/
    flowable-too-large-how-to-keeptogether
    """

    collection = FormCollection(client.app.session())
    collection.definitions.add('Contact', definition=dedent("""
        Name * = ___
        E-Mail * = @@@
    """), type='custom')
    transaction.commit()

    client.login_admin()

    page = client.get('/forms').click('Contact')
    page.form['name'] = 'John'
    page.form['e_mail'] = 'john@example.org'
    page = page.form.submit().follow().form.submit().follow()
    assert 'FRM-' in page

    ticket_page = client.get('/tickets/ALL/open').click('Annehmen').follow()
    ticket_url = ticket_page.request.url

    # This should work with 4000 chars. (customer explicitly asked for it)
    # TABLE_CELL_CHAR_LIMIT
    long_message = 'word ' * (4000 // 5 - 1)
    assert len(long_message) < 4000
    note_page = ticket_page.click('Neue Notiz')
    note_page.form['text'] = long_message
    res = note_page.form.submit().follow()

    pdf = client.get(ticket_url + '/pdf')
    assert pdf.content_type == 'application/pdf'
    _, page_text = extract_pdf_info(BytesIO(pdf.body))
    assert 'John' in page_text


ENTRY_URL = 'https://example.org/directories/baugesuche/permit-one'


def directory_entry_request(org_app: TestOrgApp) -> Any:
    """ The minimum DirectoryEntryPdf and DefaultMailLayout need. """

    translator = org_app.translations.get('de_CH')

    def translate(text: Any) -> str:
        if not hasattr(text, 'interpolate'):
            return text
        return text.interpolate(
            translator.gettext(text) if translator else text)

    return Bunch(
        app=org_app,
        locale='de_CH',
        translate=translate,
        link=lambda *args, **kwargs: ENTRY_URL,
    )


def add_permit_entry(
    org_app: TestOrgApp,
    with_files: bool = False,
    name: str = 'Permit One'
) -> ExtendedDirectoryEntry:

    session = org_app.session()
    directories: DirectoryCollection[ExtendedDirectory]
    directories = DirectoryCollection(session, type='extended')
    directory = directories.add(
        title='Baugesuche',
        structure="""
            Gesuchsteller/in *= ___
            Termin *= YYYY.MM.DD HH:MM
            Frist *= YYYY.MM.DD
            Dokumente = *.txt (multiple)
        """,
        configuration=DirectoryConfiguration(
            title='[Gesuchsteller/in]',
            order=['Gesuchsteller/in'],
        ),
    )

    values: dict[str, Any] = dict(
        gesuchsteller_in=name,
        termin=datetime(2026, 3, 15, 9, 30),
        frist=date(2026, 8, 20),
        publication_start=datetime(2026, 7, 1, 12, 0, tzinfo=UTC),
        publication_end=datetime(2026, 7, 1, 19, 0, tzinfo=UTC),
    )
    values['dokumente'] = (
        Bunch(
            data=object(),
            file=BytesIO(b'Situationsplan'),
            filename='situationsplan.txt',
        ),
        Bunch(
            data=object(),
            file=BytesIO(b'Baubeschrieb'),
            filename='baubeschrieb.txt',
        ),
    ) if with_files else ()

    entry = directory.add(values=values)
    session.flush()
    return entry


def test_directory_entry_pdf(org_app: TestOrgApp) -> None:
    """ The certificate renders every section. """

    request = directory_entry_request(org_app)
    entry = add_permit_entry(org_app, with_files=True)
    generated_at = datetime(2026, 7, 1, 13, 0, tzinfo=UTC)

    result = DirectoryEntryPdf.from_entry(request, entry, generated_at)

    # rewound, ready to be attached
    assert result.tell() == 0

    pages, text = extract_pdf_info(result)
    assert pages == 1
    assert text.startswith('Permit One')
    assert 'Dieses Dokument bescheinigt die Publikation "Permit One"' in text
    assert 'ist abgelaufen' not in text

    # dates formatted, not dumped as ISO values
    assert 'Publikation' in text
    assert 'Gesuchsteller/in: Permit One' in text
    assert 'Termin: 15. März 2026 09:30' in text
    assert 'Frist: 20. August 2026' in text
    assert '2026-03-15' not in text
    assert '2026-08-20' not in text

    # file fields are not repeated as basic fields
    assert 'Dokumente:' not in text

    # one size/date/hash block per file
    assert 'Anhänge' in text
    for name, content in (
        ('situationsplan.txt', b'Situationsplan'),
        ('baubeschrieb.txt', b'Baubeschrieb'),
    ):
        assert name in text
        assert f'Grösse: {len(content)} Bytes' in text
    assert text.count('Datum:') == 2
    assert text.count('Prüfsumme:') == 2

    # publication details
    assert 'Publikationsdetails' in text
    assert 'Publikationsstart: 1. Juli 2026 14:00' in text
    assert 'Publikationsende: 1. Juli 2026 21:00' in text
    assert 'Zugriff: Öffentlich' in text
    assert entry.content_hash
    assert f'Prüfsumme des Verzeichniseintrages: {entry.content_hash}' in text

    assert (
        'E-Mail automatisch generiert von Govikon am 1. Juli 2026 15:00'
    ) in text


def test_directory_entry_pdf_ended(org_app: TestOrgApp) -> None:
    """ The expiry variant swaps the intro; everything else stays. """

    request = directory_entry_request(org_app)
    entry = add_permit_entry(org_app)
    generated_at = datetime(2026, 7, 1, 13, 0, tzinfo=UTC)

    result = DirectoryEntryPdf.from_entry(
        request, entry, generated_at, ended=True)

    _, text = extract_pdf_info(result)
    assert 'Die Publikation "Permit One" ist abgelaufen.' in text
    assert 'bescheinigt' not in text
    assert 'Publikationsdetails' in text


def test_directory_entry_pdf_without_attachments(
    org_app: TestOrgApp
) -> None:
    """ An entry without files says so, no empty section. """

    request = directory_entry_request(org_app)
    entry = add_permit_entry(org_app)

    result = DirectoryEntryPdf.from_entry(
        request, entry, datetime(2026, 7, 1, 13, 0, tzinfo=UTC))

    _, text = extract_pdf_info(result)
    assert 'Anhänge Keine' in text
    assert 'Grösse:' not in text


def test_directory_entry_pdf_escapes_markup(org_app: TestOrgApp) -> None:
    """ Titles and field values end up in reportlab markup - unescaped,
    reportlab eats them as tags and silently drops the content. """

    request = directory_entry_request(org_app)
    name = 'Umbau <b>Haus</b> & Garten'
    entry = add_permit_entry(org_app, name=name)
    assert entry.title == name

    result = DirectoryEntryPdf.from_entry(
        request, entry, datetime(2026, 7, 1, 13, 0, tzinfo=UTC))

    _, text = extract_pdf_info(result)
    # heading and intro link keep the markup verbatim, not bold
    assert text.startswith(name)
    assert f'Publikation "{name}"' in text

    # ... and so does the field value, via mini_html
    assert f'Gesuchsteller/in: {name}' in text


def test_ticket_summary_empty_after_cleaning() -> None:
    pdf = TicketBasePdf(
        BytesIO(),
        title='Test',
        created='01.01.2026',
        author='localhost',
        translations={},
        locale='de_CH',
    )
    pdf.init_a4_portrait()

    pdf.ticket_summary('<div></div>')

    # early-exit cases
    pdf.ticket_summary(None)
    pdf.ticket_summary('')
    pdf.ticket_summary('<p></p>')
