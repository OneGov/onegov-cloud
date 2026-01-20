from __future__ import annotations

from datetime import datetime, date
from onegov.core.utils import Bunch
from onegov.form import FormCollection
from onegov.org.models.ticket import ReservationTicket
from onegov.org.models import TicketMessage, TicketChatMessage
from onegov.org.pdf.ticket import TicketPdf
from onegov.pdf.utils import extract_pdf_info
from onegov.reservation import ResourceCollection
from onegov.ticket import TicketCollection
from tests.onegov.pdf.test_pdf import LONGEST_TABLE_CELL_TEXT
from webob.multidict import MultiDict


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.form import Form, FormSubmission
    from onegov.org.request import OrgRequest
    from onegov.reservation import Resource
    from onegov.ticket import Ticket
    from sqlalchemy.orm import Session
    from uuid import UUID
    from .conftest import TestOrgApp


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
        ticket.handler.refresh_invoice_items(request)
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
    # add_ticket_message(request, ticket, 2 * LONGEST_TABLE_CELL_TEXT)

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
