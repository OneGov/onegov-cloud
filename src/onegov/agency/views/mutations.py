from morepath import redirect
from onegov.agency import _
from onegov.agency import AgencyApp
from onegov.agency.forms import MutationForm
from onegov.agency.layouts import AgencyLayout
from onegov.agency.layouts import ExtendedPersonLayout
from onegov.agency.models import ExtendedAgency
from onegov.agency.models import ExtendedPerson
from onegov.core.security import Public
from onegov.org.elements import Link
from onegov.org.mail import send_ticket_mail
from onegov.org.models import TicketMessage
from onegov.ticket import TicketCollection
from uuid import uuid4


@AgencyApp.form(
    model=ExtendedAgency,
    name='report-change',
    template='form.pt',
    permission=Public,
    form=MutationForm
)
def report_agency_change(self, request, form):
    if form.submitted(request):
        session = request.session
        with session.no_autoflush:
            ticket = TicketCollection(session).open_ticket(
                handler_code='AGN',
                handler_id=uuid4().hex,
                handler_data={
                    'id': str(self.id),
                    'submitter_email': form.email.data,
                    'submitter_message': form.message.data
                }
            )
            TicketMessage.create(ticket, request, 'opened')
            ticket.create_snapshot(request)

        send_ticket_mail(
            request=request,
            template='mail_ticket_opened.pt',
            subject=_("Your ticket has been opened"),
            receivers=(form.email.data, ),
            ticket=ticket
        )

        request.success(_("Thank you for your submission!"))
        return redirect(request.link(ticket, 'status'))

    layout = AgencyLayout(self, request)
    layout.breadcrumbs.append(Link(_("Report change"), '#'))

    return {
        'layout': layout,
        'title': _("Report change"),
        'lead': self.title,
        'form': form
    }


@AgencyApp.form(
    model=ExtendedPerson,
    name='report-change',
    template='form.pt',
    permission=Public,
    form=MutationForm
)
def report_person_change(self, request, form):
    if form.submitted(request):
        session = request.session
        with session.no_autoflush:
            ticket = TicketCollection(session).open_ticket(
                handler_code='PER',
                handler_id=uuid4().hex,
                handler_data={
                    'id': str(self.id),
                    'submitter_email': form.email.data,
                    'submitter_message': form.message.data
                }
            )
            TicketMessage.create(ticket, request, 'opened')
            ticket.create_snapshot(request)

        send_ticket_mail(
            request=request,
            template='mail_ticket_opened.pt',
            subject=_("Your ticket has been opened"),
            receivers=(form.email.data, ),
            ticket=ticket
        )

        request.success(_("Thank you for your submission!"))
        return redirect(request.link(ticket, 'status'))

    layout = ExtendedPersonLayout(self, request)
    layout.breadcrumbs.append(Link(_("Report change"), '#'))

    return {
        'layout': layout,
        'title': _("Report change"),
        'lead': self.title,
        'form': form
    }
