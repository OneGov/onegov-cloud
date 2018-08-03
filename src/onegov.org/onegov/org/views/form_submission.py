""" Renders and handles defined forms, turning them into submissions. """

import morepath

from onegov.core.security import Public, Private
from onegov.ticket import TicketCollection
from onegov.form import (
    FormCollection,
    FormDefinition,
    PendingFormSubmission,
    CompleteFormSubmission
)
from onegov.org import _, OrgApp
from onegov.org.layout import FormSubmissionLayout
from onegov.org.mail import send_transactional_html_mail
from onegov.org.models import TicketMessage, SubmissionMessage
from onegov.pay import Price
from purl import URL


def copy_query(request, url, fields):
    url = URL(url)

    for field in fields:
        if field in request.GET:
            url = url.query_param(field, request.GET[field])

    return url.as_string()


def get_price(request, form, submission):
    total = form.total()

    if 'price' in submission.meta:
        if total is not None:
            total += Price(**submission.meta['price'])
        else:
            total = Price(**submission.meta['price'])

    return request.app.adjust_price(total)


def get_hints(layout, window):
    if not window:
        return

    if window.in_the_past:
        yield 'stop', _("The registration has ended")
    elif not window.enabled:
        yield 'stop', _("The registration is closed")

    if window.enabled and window.in_the_future:
        yield 'date', _("The registration opens on ${day}, ${date}", mapping={
            'day': layout.format_date(window.start, 'weekday_long'),
            'date': layout.format_date(window.start, 'date_long')
        })

    if window.enabled and window.in_the_present:
        yield 'date', _("The registration closes on ${day}, ${date}", mapping={
            'day': layout.format_date(window.end, 'weekday_long'),
            'date': layout.format_date(window.end, 'date_long')
        })

        if window.limit and window.overflow:
            yield 'count', _("There's a limit of ${count} attendees", mapping={
                'count': window.limit
            })

        if window.limit and not window.overflow:
            spots = window.available_spots

            if spots == 0:
                yield 'stop', _("There are no spots left")
            elif spots == 1:
                yield 'count', _("There is one spot left")
            else:
                yield 'count', _("There are ${count} spots left", mapping={
                    'count': spots
                })


@OrgApp.form(model=FormDefinition, template='form.pt', permission=Public,
             form=lambda self, request: self.form_class)
def handle_defined_form(self, request, form):
    """ Renders the empty form and takes input, even if it's not valid, stores
    it as a pending submission and redirects the user to the view that handles
    pending submissions.

    """

    collection = FormCollection(request.session)

    if not self.current_registration_window:
        spots = 0
        enabled = True
    else:
        spots = 1
        enabled = self.current_registration_window.accepts_submissions(spots)

    if enabled and request.POST:
        submission = collection.submissions.add(
            self.name, form, state='pending', spots=spots)

        return morepath.redirect(request.link(submission))

    layout = FormSubmissionLayout(self, request)

    return {
        'layout': layout,
        'title': self.title,
        'form': enabled and form,
        'definition': self,
        'form_width': 'small',
        'lead': self.meta.get('lead'),
        'text': self.content.get('text'),
        'people': self.people,
        'contact': self.contact_html,
        'coordinates': self.coordinates,
        'hints': tuple(get_hints(layout, self.current_registration_window)),
        'hints_callout': not enabled
    }


@OrgApp.html(model=PendingFormSubmission, template='submission.pt',
             permission=Public, request_method='GET')
@OrgApp.html(model=PendingFormSubmission, template='submission.pt',
             permission=Public, request_method='POST')
@OrgApp.html(model=CompleteFormSubmission, template='submission.pt',
             permission=Private, request_method='GET')
@OrgApp.html(model=CompleteFormSubmission, template='submission.pt',
             permission=Private, request_method='POST')
def handle_pending_submission(self, request):
    """ Renders a pending submission, takes it's input and allows the
    user to turn the submission into a complete submission, once all data
    is valid.

    This view has two states, a completeable state where the form values
    are displayed without a form and an edit state, where a form is rendered
    to change the values.

    Takes the following query parameters for customization::

        * ``edit`` render the view in the edit state
        * ``return-to`` the view redirects to this url once complete
        * ``title`` a custom title (required if external submission)
        * ``quiet`` no success messages are rendered if present

    """
    collection = FormCollection(request.session)

    form = request.get_form(self.form_class, data=self.data)
    form.action = request.link(self)

    if 'edit' not in request.GET:
        form.validate()

    if not request.POST:
        form.ignore_csrf_error()
    elif not form.errors:
        collection.submissions.update(self, form)

    completable = not form.errors and 'edit' not in request.GET

    if completable and 'return-to' in request.GET:

        if 'quiet' not in request.GET:
            request.success(_("Your changes were saved"))

        # the default url should actually never be called
        return request.redirect(request.url)

    if 'title' in request.GET:
        title = request.GET['title']
    else:
        title = self.form.title

    price = get_price(request, form, self)

    # retain some parameters in links (the rest throw away)
    form.action = copy_query(
        request, form.action, ('return-to', 'title', 'quiet'))

    edit_link = URL(copy_query(
        request, request.link(self), ('title', )))

    # the edit link always points to the editable state
    edit_link = edit_link.query_param('edit', '')
    edit_link = edit_link.as_string()

    return {
        'layout': FormSubmissionLayout(self, request, title),
        'title': title,
        'form': form,
        'completable': completable,
        'edit_link': edit_link,
        'complete_link': request.link(self, 'complete'),
        'model': self,
        'price': price,
        'checkout_button': price and request.app.checkout_button(
            button_label=request.translate(_("Pay Online and Complete")),
            title=title,
            price=price,
            email=self.email or self.get_email_field_data(form),
            locale=request.locale
        )
    }


@OrgApp.view(model=PendingFormSubmission, name='complete',
             permission=Public, request_method='POST')
@OrgApp.view(model=CompleteFormSubmission, name='complete',
             permission=Private, request_method='POST')
def handle_complete_submission(self, request):
    form = request.get_form(self.form_class)
    form.process(data=self.data)

    # we're not really using a csrf protected form here (the complete form
    # button is basically just there so we can use a POST instead of a GET)
    form.validate()
    form.ignore_csrf_error()

    if form.errors:
        return morepath.redirect(request.link(self))
    else:
        if self.state == 'complete':
            self.data.changed()  # trigger updates
            request.success(_("Your changes were saved"))

            return morepath.redirect(request.link(
                FormCollection(request.session).scoped_submissions(
                    self.name, ensure_existance=False)
            ))
        else:
            provider = request.app.default_payment_provider
            token = request.params.get('payment_token')

            price = get_price(request, form, self)
            payment = self.process_payment(price, provider, token)

            if not payment:
                request.alert(_("Your payment could not be processed"))
                return morepath.redirect(request.link(self))
            elif payment is not True:
                self.payment = payment

            window = self.registration_window
            if window and not window.accepts_submissions(self.spots):
                request.alert(_("Registrations are no longer possible"))
                return morepath.redirect(request.link(self))

            show_submission = request.params.get('send_by_email') == 'yes'

            self.meta['show_submission'] = show_submission
            self.meta.changed()

            collection = FormCollection(request.session)
            collection.submissions.complete_submission(self)

            # make sure accessing the submission doesn't flush it, because
            # it uses sqlalchemy utils observe, which doesn't like premature
            # flushing at all
            with collection.session.no_autoflush:
                ticket = TicketCollection(request.session).open_ticket(
                    handler_code=self.meta.get('handler_code', 'FRM'),
                    handler_id=self.id.hex
                )
                TicketMessage.create(ticket, request, 'opened')

            if self.email != request.current_username and not ticket.muted:
                send_transactional_html_mail(
                    request=request,
                    template='mail_ticket_opened.pt',
                    subject=_("A ticket has been opened"),
                    receivers=(self.email, ),
                    content={
                        'model': ticket,
                        'form': form,
                        'show_submission': self.meta['show_submission']
                    }
                )

            request.success(_("Thank you for your submission!"))

            return morepath.redirect(request.link(ticket, 'status'))


@OrgApp.view(model=CompleteFormSubmission, name='ticket', permission=Private)
def view_submission_ticket(self, request):
    ticket = TicketCollection(request.session).by_handler_id(self.id.hex)
    return request.redirect(request.link(ticket))


@OrgApp.view(model=CompleteFormSubmission, name='confirm-registration',
             permission=Private, request_method='POST')
def handle_accept_registration(self, request):
    return handle_submission_action(self, request, 'confirmed')


@OrgApp.view(model=CompleteFormSubmission, name='deny-registration',
             permission=Private, request_method='POST')
def handle_deny_registration(self, request):
    return handle_submission_action(self, request, 'denied')


@OrgApp.view(model=CompleteFormSubmission, name='cancel-registration',
             permission=Private, request_method='POST')
def handle_cancel_registration(self, request):
    return handle_submission_action(self, request, 'cancelled')


def handle_submission_action(self, request, action):
    request.assert_valid_csrf_token()

    if action == 'confirmed':
        subject = _("Your registration has been confirmed")
        success = _("The registration has been confirmed")
        failure = _("The registration could not be confirmed")

        def execute():
            if self.registration_window and self.claimed is None:
                return self.claim() or True

    elif action == 'denied':
        subject = _("Your registration has been denied")
        success = _("The registration has been denied")
        failure = _("The registration could not be denied")

        def execute():
            if self.registration_window and self.claimed is None:
                return self.disclaim() or True

    elif action == 'cancelled':
        subject = _("Your registration has been cancelled")
        success = _("The registration has been cancelled")
        failure = _("The registration could not be cancelled")

        def execute():
            if self.registration_window and self.claimed:
                return self.disclaim() or True

    if execute():
        ticket = TicketCollection(request.session).by_handler_id(self.id.hex)

        if self.email != request.current_username and not ticket.muted:
            send_transactional_html_mail(
                request=request,
                template='mail_registration_action.pt',
                receivers=(self.email, ),
                content={
                    'model': self,
                    'action': action,
                    'ticket': ticket,
                    'form': self.form_obj,
                    'show_submission': self.meta.get('show_submission')
                },
                subject=subject
            )

        SubmissionMessage.create(ticket, request, action)

        request.success(success)
    else:
        request.alert(failure)

    return request.redirect(request.link(self))
