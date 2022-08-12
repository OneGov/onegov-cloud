from morepath import redirect
from onegov.core.crypto import random_token
from onegov.core.security import Public
from onegov.core.security import Secret
from onegov.core.templates import render_template
from onegov.file import File
from onegov.file.utils import as_fileintent
from onegov.org.layout import DefaultMailLayout
from onegov.org.mail import send_ticket_mail
from onegov.org.models import Organisation
from onegov.org.models import TicketMessage
from onegov.org.pdf.ticket import TicketPdf
from onegov.ticket import TicketCollection
from onegov.translator_directory import _
from onegov.translator_directory import TranslatorDirectoryApp
from onegov.translator_directory.collections.translator import \
    TranslatorCollection
from onegov.translator_directory.forms.accreditation import \
    GrantAccreditationForm
from onegov.translator_directory.forms.accreditation import \
    RefuseAccreditationForm
from onegov.translator_directory.forms.accreditation import \
    RequestAccreditationForm
from onegov.translator_directory.layout import GrantAccreditationLayout
from onegov.translator_directory.layout import RefuseAccreditationLayout
from onegov.translator_directory.layout import RequestAccreditationLayout
from onegov.translator_directory.models.accreditation import Accreditation
from onegov.translator_directory.models.message import AccreditationMessage
from uuid import uuid4


@TranslatorDirectoryApp.form(
    model=Organisation,
    name='request-accreditation',
    template='form.pt',
    permission=Public,
    form=RequestAccreditationForm
)
def request_accreditation(self, request, form):
    if form.submitted(request):
        translator = TranslatorCollection(request.app).add(
            **form.get_translator_data(),
            update_user=False
        )
        translator.files.extend(form.get_files())
        session = request.session
        with session.no_autoflush:
            ticket = TicketCollection(session).open_ticket(
                handler_code='AKK',
                handler_id=uuid4().hex,
                handler_data={
                    'id': str(translator.id),
                    'submitter_email': form.email.data,
                    **form.get_ticket_data()
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
        'title': _(
            'Application for accreditation as interpreter for the '
            'authorities and courts of the Canton of Zug'
        ),
        'form': form
    }


@TranslatorDirectoryApp.form(
    model=Accreditation,
    name='grant',
    template='form.pt',
    permission=Secret,
    form=GrantAccreditationForm
)
def grant_accreditation(self, request, form):
    if form.submitted(request):
        self.grant()
        AccreditationMessage.create(self.ticket, request, 'granted')
        request.success(_("Admission granted."))

        # store a PDF of the ticket on the translator
        content = TicketPdf.from_ticket(request, self.ticket)
        self.target.files.append(
            File(
                id=random_token(),
                name='Ticket.pdf',
                note='Antrag',
                reference=as_fileintent(
                    content=content,
                    filename='Ticket.pdf'
                )
            )
        )

        # create a user account and send an activation mail
        translators = TranslatorCollection(request.app)
        translators.update_user(self.target, self.target.email)
        subject = request.translate(_('An account was created for you'))
        content = render_template('mail_new_user.pt', request, {
            'user': self.target.user,
            'org': request.app.org,
            'layout': DefaultMailLayout(self.target.user, request),
            'title': subject
        })
        request.app.send_transactional_email(
            subject=subject,
            receivers=(self.target.user.username, ),
            content=content,
        )
        request.success(_('Activation E-Mail sent'))

        if 'return-to' in request.GET:
            return request.redirect(request.url)
        return redirect(request.link(self))

    layout = GrantAccreditationLayout(self, request)

    return {
        'layout': layout,
        'title': _('Grant admission'),
        'form': form
    }


@TranslatorDirectoryApp.form(
    model=Accreditation,
    name='refuse',
    template='form.pt',
    permission=Secret,
    form=RefuseAccreditationForm
)
def refuse_accreditation(self, request, form):
    if form.submitted(request):
        self.refuse()
        request.success(_("Admission refused."))
        AccreditationMessage.create(self.ticket, request, 'refused')
        if 'return-to' in request.GET:
            return request.redirect(request.url)
        return redirect(request.link(self))

    layout = RefuseAccreditationLayout(self, request)

    return {
        'layout': layout,
        'title': _('Refuse admission'),
        'form': form
    }
