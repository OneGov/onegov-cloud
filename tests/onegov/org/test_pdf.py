from datetime import datetime, date

from PyPDF2 import PdfFileReader
from webob.multidict import MultiDict
from onegov.core.utils import Bunch
from onegov.form import FormCollection
from onegov.org.models import TicketMessage, TicketChatMessage
from onegov.org.pdf.ticket import TicketPdf
from onegov.reservation import ResourceCollection
from onegov.ticket import TicketCollection
from tests.shared.utils import open_pdf


long_text = """
OpenID is an open standard and decentralized authentication protocol. 
Promoted by the non-profit OpenID Foundation, it allows users to be 
authenticated by co-operating sites (known as relying parties, or RP) 
using a third-party service, eliminating the need for webmasters to 
provide their own ad hoc login systems, and allowing users to log into 
multiple unrelated websites without having to have a separate identity 
and password for each.[1] Users create accounts by selecting an OpenID 
identity provider[1] and then use those accounts to sign onto any website that 
accepts OpenID authentication. Several large organizations either issue or 
accept OpenIDs on their websites, according to the OpenID Foundation.[2]

The OpenID standard provides a framework for the communication that must take 
place between the identity provider and the OpenID acceptor 
(the "relying party").[3] An extension to the standard 
(the OpenID Attribute Exchange) facilitates the transfer of user attributes, 
such as name and gender, from the OpenID identity provider to the relying party 
(each relying party may request a different set of attributes, depending on 
its requirements).[4] The OpenID protocol does not rely on a central authority 
to authenticate a user's identity. Moreover, neither services nor the OpenID 
standard may mandate a specific means by which to authenticate users, 
allowing for approaches ranging from the common (such as passwords) to the 
novel (such as smart cards or biometrics).

The final version of OpenID is OpenID 2.0, finalized and published in December 
2007.[5] The term OpenID may also refer to an identifier as specified in the 
OpenID standard; these identifiers take the form of a unique Uniform Resource 
Identifier (URI), and are managed by some "OpenID provider" that handles 
authentication.[1] 

The OpenID standard provides a framework for the communication that must take 
place between the identity provider and the OpenID acceptor 
(the "relying party").[3] An extension to the standard 
(the OpenID Attribute Exchange) facilitates the transfer of user attributes, 
such as name and gender, from the OpenID identity provider to the relying party 
(each relying party may request a different set of attributes, depending on 
its requirements).[4] The OpenID protocol does not rely on a central authority 
to authenticate a user's identity. Moreover, neither services nor the OpenID 
standard may mandate a specific means by which to authenticate users, 
allowing for approaches ranging from the common (such as passwords) to the 
novel (such as smart cards or biometrics).

The final version of OpenID is OpenID 2.0, finalized and published in December 
2007.[5] The term OpenID may also refer to an identifier as specified in the 
OpenID standard; these identifiers take the form of a unique Uniform Resource 
Identifier (URI), and are managed by some "OpenID provider" that handles 
authentication.[1] 

"""

def open_ticket(request, token, handler_code, create_message=True):
    with request.session.no_autoflush:
        ticket = TicketCollection(request.session).open_ticket(
            handler_code=handler_code, handler_id=token
        )
        if create_message:
            TicketMessage.create(ticket, request, 'opened')
    return ticket


def add_submission(session, resource, token):
    # add the submission if it doesn't yet exist
    forms = FormCollection(session)
    submission = None
    if resource.definition:
        submission = forms.submissions.add_external(
            form=resource.form_class(),
            state='pending',
            id=token,
            payment_method=resource.payment_method
        )
    return submission


def update_submission(session, submission, form):
    # update the data on the submission
    forms = FormCollection(session)
    if submission:
        forms.submissions.update(submission, form)


def add_ticket_message(request, ticket, text):
    message = TicketChatMessage.create(
        ticket, request,
        text=text,
        owner='info@example.org',
        recipient=None,
        notify=None,
        origin='internal')
    return message


def test_ticket_pdf(org_app, handlers):

    session = org_app.session()
    libres_context = org_app.libres_context
    owner = 'info@example.org'

    def get_translate(**kwargs):
        return org_app.chameleon_translations.get('de_CH')

    def class_link(cls, *args, **kwargs):
        return cls.__name__

    def link(*args, **kwargs):
        name = kwargs.pop('name')
        return f'https://seantis.ch/{name or ""}'

    host_url = '127.0.0.1:8080'

    request = Bunch(
        app=org_app,
        translate=lambda x: x,
        session=session,
        include=lambda x: None,
        current_username=owner,
        is_manager=True,
        get_translate=get_translate,
        locale='de_CH',
        host_url=host_url,
        class_link=class_link,
        link=link
    )
    collection = ResourceCollection(libres_context)
    forms = FormCollection(session)
    room = collection.add('Stairway to Heaven', 'Europe/Zurich', type='room',
                          definition='# Data\nName *= ___')

    scheduler = room.get_scheduler(libres_context)
    dates = (datetime(2017, 6, 7, 12), datetime(2017, 6, 7, 18))
    scheduler.allocate(dates)

    token = scheduler.reserve(owner, dates)
    submission = add_submission(session, room, token)

    form_data = MultiDict([('data_name', 'John')])

    # We skip the combining ReservationForm and the form from definition
    form = room.form_class(form_data)
    assert form.validate()
    update_submission(session, submission, form)

    # scheduler.approve_reservations(token)
    reservation = scheduler.reservations_by_token(token).one()
    assert reservation
    ticket = open_ticket(request, token, 'RSV', owner)

    add_ticket_message(request, ticket, long_text)

    assert ticket.handler.resource

    # is the ticket object sesPdfsion
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
    # open_pdf(pdf)

    reader = PdfFileReader(pdf)
    assert reader.getNumPages() == 1
    page = reader.getPage(0).extractText()
    assert 'John' in page
    assert 'Data' in page

    assert f'Herkunft: {host_url}' in page
    assert date.today().strftime("%d.%m.%Y") in page

    metadata = ('Betreff', 'Antragsteller/in', 'Status', 'Gruppe', 'Zuständig',
                'Erstellt', 'Reaktionszeit', 'Bearbeitungszeit')

    titles = ('Zusammenfassung', 'Aktivität')

    for entry in metadata:
        assert entry in page

    for title in titles:
        assert title in page
