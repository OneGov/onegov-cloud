from morepath import redirect
from onegov.org.mail import send_ticket_mail
from onegov.org.models import Organisation
from onegov.core.security import Public
from onegov.core.security import Secret
from onegov.org.models import TicketMessage
from onegov.ticket import TicketCollection
from onegov.translator_directory import _
from onegov.translator_directory import TranslatorDirectoryApp
from onegov.translator_directory.forms.accreditation import \
    AcceptAccreditationForm
from onegov.translator_directory.forms.accreditation import \
    RequestAccreditationForm
from onegov.translator_directory.layout import RequestAccreditationLayout
from onegov.translator_directory.layout import AcceptAccreditationLayout
from onegov.translator_directory.models.accreditation import Accreditation
from onegov.translator_directory.models.message import AccreditationMessage
from uuid import uuid4


@TranslatorDirectoryApp.form(
    model=Organisation,
    name='antrag-akkreditierung',
    template='accreditation.pt',
    permission=Public,
    form=RequestAccreditationForm
)
def request_accreditation(self, request, form):
    if form.submitted(request):
        session = request.session
        with session.no_autoflush:
            ticket = TicketCollection(session).open_ticket(
                handler_code='AKK',
                handler_id=uuid4().hex,
                handler_data={
                    'id': str(self.id),
                    'submitter_email': form.email.data,
                    'data': form.get_useful_data()
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
        if request.email_for_new_tickets:
            send_ticket_mail(
                request=request,
                template='mail_ticket_opened_info.pt',
                subject=_("New ticket"),
                ticket=ticket,
                receivers=(request.email_for_new_tickets, ),
                content={
                    'model': ticket
                }
            )

        request.success(_("Thank you for your submission!"))
        return redirect(request.link(ticket, 'status'))

    layout = RequestAccreditationLayout(self, request)

    return {
        'layout': layout,
        'title': _("Request accreditation"),
        'form': form
    }


@TranslatorDirectoryApp.form(
    model=Accreditation,
    name='accept',
    template='form.pt',
    permission=Secret,
    form=AcceptAccreditationForm
)
def accept_accreditation(self, request, form):
    if form.submitted(request):
        form.update_model()
        request.success(_("Translator created."))
        AccreditationMessage.create(
            self.ticket,
            request,
            'accept',
            form.changes.data
        )
        if 'return-to' in request.GET:
            return request.redirect(request.url)
        return redirect(request.link(self))
    # else:
    #     form.apply_model()

    layout = AcceptAccreditationLayout(self, request)

    return {
        'layout': layout,
        'title': _("Accept accreditation"),
        'form': form
    }
