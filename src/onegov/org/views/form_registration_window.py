from collections import defaultdict
from onegov.core.security import Private
from onegov.form import FormDefinition
from onegov.form import FormRegistrationWindow
from onegov.form import FormSubmission
from onegov.org import OrgApp, _
from onegov.org.cli import close_ticket
from onegov.org.forms import FormRegistrationWindowForm
from onegov.org.forms.form_registration import FormRegistrationMessageForm
from onegov.org.layout import FormSubmissionLayout
from onegov.core.elements import Link, Confirm, Intercooler, Block

from onegov.org.models import TicketNote
from onegov.org.views.form_submission import handle_submission_action
from onegov.org.mail import send_transactional_html_mail
from onegov.org.views.ticket import accept_ticket, send_email_if_enabled
from onegov.ticket import TicketCollection, Ticket


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.org.layout import Layout
    from onegov.org.request import OrgRequest


@OrgApp.form(
    model=FormDefinition,
    name='new-registration-window',
    permission=Private,
    form=FormRegistrationWindowForm,
    template='form.pt')
def handle_new_registration_form(self, request, form, layout=None):
    title = _("New Registration Window")

    layout = layout or FormSubmissionLayout(self, request)
    layout.editbar_links = None
    layout.breadcrumbs.append(Link(title, '#'))

    if form.submitted(request):
        form.populate_obj(self.add_registration_window(
            form.start.data,
            form.end.data
        ))

        request.success(_("The registration window was added successfully"))
        return request.redirect(request.link(self))

    return {
        'layout': layout,
        'title': title,
        'form': form,
        'helptext': _(
            "Registration windows limit forms to a set number of submissions "
            "and a specific time-range."
        )
    }


def send_form_registration_email(request, receivers, content, action):
    if action == 'general-message':
        subject = _("General Message")
    else:
        raise NotImplementedError
    return send_transactional_html_mail(
        request=request,
        template='mail_registration_message.pt',
        subject=subject,
        receivers=receivers,
        content=content
    )


def ticket_linkable(
    request: 'OrgRequest',
    ticket: Ticket | None
) -> Ticket | None:

    if ticket is None:
        return None
    if not request.link(ticket):
        return None
    return ticket


@OrgApp.form(
    model=FormRegistrationWindow,
    permission=Private,
    name='send-message',
    template='form.pt',
    form=FormRegistrationMessageForm
)
def view_send_form_registration_message(
    self: FormRegistrationWindow,
    request: 'OrgRequest',
    form: FormRegistrationMessageForm,
    layout: 'Layout | None' = None,
):
    if form.submitted(request):
        count = 0
        tickets = TicketCollection(request.session)

        for email, submission in form.receivers.items():
            _ticket = tickets.by_handler_id(submission.id.hex)

            if not form.message.data:
                continue

            # be extra safe and check for missing ticket of submission
            if (ticket := ticket_linkable(request, _ticket)) is not None:
                TicketNote.create(ticket, request, (
                    request.translate(_(
                        "New e-mail: ${message}",
                        mapping={'message': form.message.data.strip()}
                    ))
                ))

            send_form_registration_email(
                request=request,
                receivers=(email,),
                action='general-message',
                content={
                    'model': submission,
                    'action': 'general-message',
                    'message': form.message.data.strip(),
                }
            )
            count += 1

        request.success(
            _("Successfully sent ${count} emails", mapping={'count': count})
        )
        return request.redirect(request.link(self))

    layout = layout or FormSubmissionLayout(self.form, request)
    layout.breadcrumbs.append(
        Link(_('Registration Window'), request.link(self))
    )
    layout.editbar_links = []
    return {
        'title': _('Send E-Mail to attendees'),
        'layout': layout,
        'form': form
    }


@OrgApp.html(
    model=FormRegistrationWindow,
    permission=Private,
    template='registration_window.pt')
def view_registration_window(self, request, layout=None):
    layout = layout or FormSubmissionLayout(self.form, request)
    title = layout.format_date_range(self.start, self.end)

    layout.breadcrumbs.append(Link(title, '#'))

    registrations = defaultdict(list)

    q = request.session.query(FormSubmission)
    q = q.filter_by(registration_window_id=self.id)
    q = q.filter_by(state='complete')
    # ogc-1345 order after family name first
    q = q.order_by(
        FormSubmission.data['nachname'],
        FormSubmission.data['name'],
        FormSubmission.data['vorname'],
    )
    has_pending_or_confirmed = False

    for submission in q:
        if not submission.registration_state:
            continue

        registrations[submission.registration_state].append(submission)
        if submission.registration_state != 'cancelled':
            has_pending_or_confirmed = True

    editbar_links = [
        Link(
            text=_("Edit"),
            url=request.link(self, 'edit'),
            attrs={'class': 'edit-link'}
        )
    ]
    if registrations:
        editbar_links.append(
            Link(
                text=_("Email attendees"),
                url=request.link(self, name="send-message"),
                attrs={'class': 'manage-recipients'}
            )
        )
        editbar_links.append(
            Link(
                text=_("Cancel Registration Window"),
                url=layout.csrf_protected_url(
                    request.link(self, name='cancel')),
                attrs={'class': 'cancel'},
                traits=(
                    Confirm(
                        _("You really want to cancel all confirmed and "
                          "deny all open submissions for this "
                          "registration window?"),
                        _("Each attendee will receive a ticket email "
                          "unless ticket messages are not muted."),
                        _("Cancel Registration Window"),
                        _("Cancel"),
                    ),
                    Intercooler(
                        request_method='POST',
                        redirect_after=request.link(self)
                    )
                )
            ),
        )
    editbar_links.append(
        Link(
            text=_("Delete"),
            url=layout.csrf_protected_url(request.link(self)),
            attrs={'class': 'delete-link'},
            traits=(
                Confirm(
                    _(
                        "Do you really want to delete "
                        "this registration window?"
                    ),
                    _("Existing submissions will be disassociated."),
                    _("Delete registration window"),
                    _("Cancel")
                ),
                Intercooler(
                    request_method='DELETE',
                    redirect_after=request.link(self.form)
                )
            ) if not has_pending_or_confirmed else (
                Block(
                    _("This registration window can't be deleted."),
                    _("There are confirmed or open submissions associated "
                      "with it. Cancel the registration window first."),
                    _("Cancel")
                )
            )
        )
    )

    layout.editbar_links = editbar_links

    tickets = TicketCollection(request.session)

    def ticket_link(subm):
        ticket = tickets.by_handler_id(subm.id.hex)
        return ticket and request.link(ticket) or None

    return {
        'layout': layout,
        'title': title,
        'model': self,
        'registrations': registrations,
        'groups': (
            (_("Open"), 'open'),
            (_("Confirmed"), 'confirmed'),
            (_("Cancelled"), 'cancelled'),
        ),
        'ticket_link': ticket_link
    }


@OrgApp.form(
    model=FormRegistrationWindow,
    permission=Private,
    form=FormRegistrationWindowForm,
    template='form.pt',
    name='edit')
def handle_edit_registration_form(self, request, form, layout=None):
    title = _("Edit Registration Window")

    layout = layout or FormSubmissionLayout(self.form, request)
    layout.breadcrumbs.append(Link(title, '#'))
    layout.editbar_links = []

    if form.submitted(request):
        form.populate_obj(self)

        request.success(_("Your changes were saved"))
        return request.redirect(request.link(self.form))

    elif not request.POST:
        form.process(obj=self)

    return {
        'layout': layout,
        'title': title,
        'form': form
    }


@OrgApp.view(
    model=FormRegistrationWindow,
    permission=Private,
    name='cancel',
    request_method='POST'
)
def view_cancel_submissions_for_registration_window(self, request):
    """ Cancels a bunch of submissions either open ones or already accepted
    ones. If there is a corresponding ticket, it is accepted before denying
    the submission. """
    request.assert_valid_csrf_token()
    count = 0
    for submission in self.submissions:
        if submission.registration_state == 'confirmed':
            action = 'cancelled'
        elif submission.registration_state == 'open':
            action = 'denied'
        else:
            continue
        ticket = TicketCollection(request.session).by_handler_id(
            submission.id.hex)
        if ticket and ticket.state == 'open':
            accept_ticket(ticket, request)

        if ticket:
            handle_submission_action(
                submission, request, action, ignore_csrf=True, raises=True,
                no_messages=True, force_email=ticket.muted
            )

            close_ticket(ticket, request.current_user, request)
            # same behaviour as when closing ticket normally
            # to disable mail on ticket close, there is a ticket-setting
            send_email_if_enabled(
                ticket=ticket,
                request=request,
                template='mail_ticket_closed.pt',
                subject=_("Your request has been closed.")
            )
        count += 1
    if count:
        request.success(
            _("${count} submissions cancelled / denied over the ticket system",
              mapping={'count': count}))


@OrgApp.view(
    model=FormRegistrationWindow,
    permission=Private,
    request_method='DELETE')
def delete_registration_window(self, request):
    request.assert_valid_csrf_token()

    self.disassociate()
    request.session.delete(self)

    request.success(_("The registration window was deleted"))
