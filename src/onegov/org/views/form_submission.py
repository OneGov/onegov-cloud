""" Renders and handles defined forms, turning them into submissions. """
from __future__ import annotations

import morepath
from datetime import date
from onegov.core.elements import Link
from onegov.core.security import Public, Private
from onegov.form.collection import SurveyCollection
from onegov.form.models.submission import SurveySubmission
from onegov.org.cli import close_ticket
from onegov.ticket import TicketCollection
from onegov.form import (
    FormCollection,
    PendingFormSubmission,
    CompleteFormSubmission
)
from onegov.org import _, OrgApp
from onegov.org.layout import (
    FormSubmissionLayout,
    SurveySubmissionLayout,
    TicketLayout,
)
from onegov.org.mail import send_ticket_mail
from onegov.org.models import TicketMessage, SubmissionMessage
from onegov.org.models.ticket import (
    DirectoryEntryTicket,
    FormSubmissionTicket,
    ReservationTicket,
)
from onegov.org.utils import (
    currency_for_submission,
    emails_for_new_ticket,
    invoice_items_for_submission
)
from onegov.pay import InvoiceItemMeta, PaymentError, Price
from onegov.ticket import TicketInvoice
from purl import URL
from uuid import uuid4
from webob.exc import HTTPMethodNotAllowed, HTTPNotFound


from typing import Literal, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterable
    from onegov.core.types import RenderData
    from onegov.form import FormSubmission
    from onegov.org.request import OrgRequest
    from onegov.ticket import Ticket
    from webob import Response


def copy_query(
    request: OrgRequest,
    url: str,
    fields: Iterable[str]
) -> str:

    url_obj = URL(url)

    for field in fields:
        # FIXME: Technically this is incorrect when a field can have
        #        multiple values, should we switch to getall? Do we
        #        have to use a different method on URL to set them
        #        in that case?
        value = request.GET.get(field, None)
        if value is None:
            continue
        url_obj = url_obj.query_param(field, value)

    return url_obj.as_string()


@OrgApp.html(model=PendingFormSubmission, template='submission.pt',
             permission=Public, request_method='GET')
@OrgApp.html(model=PendingFormSubmission, template='submission.pt',
             permission=Public, request_method='POST')
@OrgApp.html(model=CompleteFormSubmission, template='submission.pt',
             permission=Private, request_method='GET')
@OrgApp.html(model=CompleteFormSubmission, template='submission.pt',
             permission=Private, request_method='POST')
def handle_pending_submission(
    self: FormSubmission,
    request: OrgRequest,
    layout: FormSubmissionLayout | TicketLayout | None = None,
    ticket: Ticket | None = None,
) -> RenderData | Response:
    """ Renders a pending submission, takes it's input and allows the
    user to turn the submission into a complete submission, once all data
    is valid.

    This view has two states, a completable state where the form values
    are displayed without a form and an edit state, where a form is rendered
    to change the values.

    Takes the following query parameters for customization::

        * ``edit`` render the view in the edit state
        * ``return-to`` the view redirects to this url once complete
        * ``title`` a custom title (required if external submission)
        * ``quiet`` no success messages are rendered if present

    """
    collection = FormCollection(request.session)

    if ticket is None:
        self_url = request.link(self)
    else:
        self_url = request.link(ticket, 'submission')

    form = request.get_form(self.form_class, data=self.data)
    form.action = self_url
    form.model = self

    if 'edit' not in request.GET:
        form.validate()

    if not request.POST:
        form.ignore_csrf_error()
    elif not form.errors:
        collection.submissions.update(self, form)

    completable = not form.errors and 'edit' not in request.GET
    invoice_items = invoice_items_for_submission(request, form, self)
    current_total_amount = InvoiceItemMeta.total(invoice_items)

    # check minimum price total if set
    minimum_total_amount = self.minimum_price_total or 0.0
    if current_total_amount < minimum_total_amount:
        _currency = currency_for_submission(form, self)
        completable = False
        request.alert(
            _(
                'The total amount for the currently entered data '
                'is ${total} but has to be at least ${minimum}. '
                'Please adjust your inputs.',
                mapping={
                    'total': Price(current_total_amount, _currency),
                    'minimum': Price(minimum_total_amount, _currency)
                }
            )
        )

    # Avoid allowing people to pay for registrations, they no longer
    # will be able to complete. There's still a small time window
    # where this can happen, if they're unlucky. But it should be
    # less likely this way.
    window = self.registration_window
    if window and not window.accepts_submissions(self.spots):
        request.alert(_('Registrations are no longer possible'))
        completable = False

    if completable and ticket is not None:
        # refresh invoice items if allowed, otherwise show an error
        if ticket.handler.refreshing_invoice_is_safe(request):
            ticket.handler.refresh_invoice_items(request)
        else:
            completable = False
            request.alert(_(
                'Your changes would alter the price total '
                'but the payment is no longer open.'
            ))

    if completable and (ticket is not None or 'return-to' in request.GET):

        if 'quiet' not in request.GET:
            request.success(_('Your changes were saved'))

        url = request.url if ticket is None else request.link(ticket)
        return request.redirect(url)

    if 'title' in request.GET:
        title = request.GET['title']
    else:
        assert self.form is not None
        title = self.form.title

    # retain some parameters in links (the rest throw away)
    form.action = copy_query(
        request, form.action, ('return-to', 'title', 'quiet'))

    edit_url_obj = URL(copy_query(
        request, self_url, ('title', )))

    # the edit url always points to the editable state
    edit_url_obj = edit_url_obj.query_param('edit', '')
    edit_url = edit_url_obj.as_string()

    complete_url = request.link(self, 'complete')

    if 'return-to' in request.GET:
        complete_url = copy_query(request, complete_url, ('return-to', ))

    price = request.app.adjust_price(Price(
        amount=current_total_amount,
        currency=currency_for_submission(form, self),
        credit_card_payment=any(
            price.credit_card_payment
            for __, price in form.prices()
        )
    )) if self.state == 'pending' and current_total_amount > 0.0 else None
    email = self.email or self.get_email_field_data(form)
    if price:
        assert email is not None
        checkout_button = request.app.checkout_button(
            button_label=request.translate(_('Pay Online and Complete')),
            title=title,
            price=price,
            email=email,
            complete_url=complete_url,
            request=request
        )
    else:
        checkout_button = None

    return {
        'layout': layout or FormSubmissionLayout(self, request, title),
        'title': title,
        'form': form,
        'completable': completable,
        'edit_link': edit_url,
        'complete_link': complete_url,
        'model': self,
        'price': price,
        'show_vat': getattr(self.form, 'show_vat', False),
        # NOTE: The VAT amount can be wrong if the fee is charged to
        #       the customer. So it's better to not show it yet.
        'hide_vat_amount': True,
        'checkout_button': checkout_button
    }


@OrgApp.html(model=DirectoryEntryTicket, template='submission.pt',
             permission=Private, request_method='GET', name='submission')
@OrgApp.html(model=DirectoryEntryTicket, template='submission.pt',
             permission=Private, request_method='POST', name='submission')
@OrgApp.html(model=FormSubmissionTicket, template='submission.pt',
             permission=Private, request_method='GET', name='submission')
@OrgApp.html(model=FormSubmissionTicket, template='submission.pt',
             permission=Private, request_method='POST', name='submission')
@OrgApp.html(model=ReservationTicket, template='submission.pt',
             permission=Private, request_method='GET', name='submission')
@OrgApp.html(model=ReservationTicket, template='submission.pt',
             permission=Private, request_method='POST', name='submission')
def handle_edit_submission_from_ticket(
    self: DirectoryEntryTicket | FormSubmissionTicket | ReservationTicket,
    request: OrgRequest,
    layout: TicketLayout | None = None
) -> RenderData | Response:

    submission = self.handler.submission
    if not isinstance(submission, CompleteFormSubmission):
        raise HTTPNotFound()

    if layout is None:
        layout = TicketLayout(self, request)

    layout.breadcrumbs = [
        *layout.breadcrumbs[:-1],
        Link(self.number, request.link(self)),
        Link(_('Edit submission'), '#')
    ]
    layout.editbar_links = []

    return handle_pending_submission(
        submission,
        request,
        layout,
        ticket=self,
    )


@OrgApp.view(model=PendingFormSubmission, name='complete',
             permission=Public, request_method='GET')
@OrgApp.view(model=PendingFormSubmission, name='complete',
             permission=Public, request_method='POST')
@OrgApp.view(model=CompleteFormSubmission, name='complete',
             permission=Public, request_method='GET')
@OrgApp.view(model=CompleteFormSubmission, name='complete',
             permission=Private, request_method='POST')
def handle_complete_submission(
    self: FormSubmission,
    request: OrgRequest
) -> Response:

    form = request.get_form(self.form_class)
    form.process(data=self.data)
    form.model = self

    # we're not really using a csrf protected form here (the complete form
    # button is basically just there so we can use a POST instead of a GET)
    form.validate()
    form.ignore_csrf_error()

    # NOTE: we only allow GET requests for some specific payment providers
    if request.method == 'GET' and (
        form.errors
        or self.state == 'complete'
        or (provider := request.app.default_payment_provider) is None
        or not provider.payment_via_get
    ):
        # TODO: A redirect back to the previous step with an error might
        #       be better UX, if this error can occur too easily...
        raise HTTPMethodNotAllowed()

    if form.errors:
        return morepath.redirect(request.link(self))
    else:
        if self.state == 'complete':
            self.data.changed()  # type:ignore[attr-defined]  # trigger updates
            request.success(_('Your changes were saved'))

            assert self.name is not None
            return morepath.redirect(request.link(
                FormCollection(request.session).scoped_submissions(
                    self.name, ensure_existance=False)
            ))
        else:
            provider = request.app.default_payment_provider
            token = provider.get_token(request) if provider else None
            invoice_items = invoice_items_for_submission(request, form, self)
            amount = InvoiceItemMeta.total(invoice_items)
            price = request.app.adjust_price(Price(
                amount=amount,
                currency=currency_for_submission(form, self),
                credit_card_payment=any(
                    price.credit_card_payment
                    for __, price in form.prices()
                )
            )) if amount > 0.0 else None
            payment = self.process_payment(price, provider, token)

            # FIXME: Custom error message for PaymentError?
            if not payment or isinstance(payment, PaymentError):
                request.alert(_('Your payment could not be processed'))
                return morepath.redirect(request.link(self))

            if payment is not True:
                self.payment = payment

            window = self.registration_window
            if window and not window.accepts_submissions(self.spots):
                request.alert(_('Registrations are no longer possible'))
                return morepath.redirect(request.link(self))

            show_submission = request.params.get('send_by_email') == 'yes'

            self.meta['show_submission'] = show_submission
            self.meta.changed()  # type:ignore[attr-defined]

            collection = FormCollection(request.session)
            submission_id = self.id

            # Expunges the submission from the session
            collection.submissions.complete_submission(self)

            # make sure accessing the submission doesn't flush it, because
            # it uses sqlalchemy utils observe, which doesn't like premature
            # flushing at all
            with collection.session.no_autoflush:
                ticket = TicketCollection(request.session).open_ticket(
                    handler_code=self.meta.get('handler_code', 'FRM'),
                    handler_id=self.id.hex
                )
                TicketMessage.create(ticket, request, 'opened', 'external')

                if invoice_items:
                    invoice = TicketInvoice(id=uuid4())
                    request.session.add(invoice)

                    for item_meta in invoice_items:
                        item = item_meta.add_to_invoice(invoice)
                        if payment is not True:
                            if provider and payment.source == provider.type:
                                item.payment_date = date.today()
                            item.payments.append(payment)
                            item.paid = payment.state == 'paid'

                    ticket.invoice = invoice

            assert self.email is not None
            submission = collection.submissions.by_id(
                submission_id, current_only=True
            )
            send_ticket_mail(
                request=request,
                template='mail_ticket_opened.pt',
                subject=_('Your request has been registered'),
                ticket=ticket,
                receivers=(self.email, ),
                content={
                    'model': ticket,
                    'form': form,
                    'show_submission': self.meta['show_submission'],
                }
            )
            for email in emails_for_new_ticket(request, ticket):
                send_ticket_mail(
                    request=request,
                    template='mail_ticket_opened_info.pt',
                    subject=_('New ticket'),
                    ticket=ticket,
                    receivers=(email, ),
                    content={'model': ticket},
                )

            request.app.send_websocket(
                channel=request.app.websockets_private_channel,
                message={
                    'event': 'browser-notification',
                    'title': request.translate(_('New ticket')),
                    'created': ticket.created.isoformat()
                }
            )

            if request.auto_accept(ticket):
                try:
                    # FIXME: Was the auto_accept_user being None the only
                    #        way this could raise ValueError previously?
                    #        If so refactor this to a simple if/else
                    if request.auto_accept_user is None:
                        raise ValueError()

                    ticket.accept_ticket(request.auto_accept_user)
                    # We need to reload the object with the correct polymorphic
                    # type
                    submission = collection.submissions.by_id(
                        submission_id, state='complete', current_only=True
                    )
                    assert isinstance(submission, CompleteFormSubmission)
                    handle_submission_action(
                        submission, request, 'confirmed', True, raises=True
                    )

                except ValueError:
                    if request.is_manager:
                        request.warning(_('Your request could not be '
                                          'accepted automatically!'))
                else:
                    close_ticket(
                        ticket, request.auto_accept_user, request
                    )

            request.success(_('Thank you for your submission!'))

            return morepath.redirect(request.link(ticket, 'status'))


@OrgApp.view(model=CompleteFormSubmission, name='ticket', permission=Private)
def view_submission_ticket(
    self: CompleteFormSubmission,
    request: OrgRequest
) -> Response:
    ticket = TicketCollection(request.session).by_handler_id(self.id.hex)
    if not ticket:
        raise HTTPNotFound()
    return request.redirect(request.link(ticket))


@OrgApp.view(model=CompleteFormSubmission, name='confirm-registration',
             permission=Private, request_method='POST')
def handle_accept_registration(
    self: CompleteFormSubmission,
    request: OrgRequest
) -> Response | None:
    return handle_submission_action(self, request, 'confirmed')


@OrgApp.view(model=FormSubmissionTicket, name='confirm-registration',
             permission=Private, request_method='POST')
def handle_accept_registration_from_ticket(
    self: FormSubmissionTicket,
    request: OrgRequest
) -> Response | None:
    submission = self.handler.submission
    if not isinstance(submission, CompleteFormSubmission):
        raise HTTPNotFound()
    return handle_submission_action(
        submission, request, 'confirmed', return_url=request.link(self))


@OrgApp.view(model=CompleteFormSubmission, name='deny-registration',
             permission=Private, request_method='POST')
def handle_deny_registration(
    self: CompleteFormSubmission,
    request: OrgRequest
) -> Response | None:
    return handle_submission_action(self, request, 'denied')


@OrgApp.view(model=FormSubmissionTicket, name='deny-registration',
             permission=Private, request_method='POST')
def handle_deny_registration_from_ticket(
    self: FormSubmissionTicket,
    request: OrgRequest
) -> Response | None:
    submission = self.handler.submission
    if not isinstance(submission, CompleteFormSubmission):
        raise HTTPNotFound()
    return handle_submission_action(
        submission, request, 'denied', return_url=request.link(self))


@OrgApp.view(model=CompleteFormSubmission, name='cancel-registration',
             permission=Private, request_method='POST')
def handle_cancel_registration(
    self: CompleteFormSubmission,
    request: OrgRequest
) -> Response | None:
    return handle_submission_action(self, request, 'cancelled')


@OrgApp.view(model=FormSubmissionTicket, name='cancel-registration',
             permission=Private, request_method='POST')
def handle_cancel_registration_from_ticket(
    self: FormSubmissionTicket,
    request: OrgRequest
) -> Response | None:
    submission = self.handler.submission
    if not isinstance(submission, CompleteFormSubmission):
        raise HTTPNotFound()
    return handle_submission_action(
        submission, request, 'cancelled', return_url=request.link(self))


def handle_submission_action(
    self: CompleteFormSubmission,
    request: OrgRequest,
    action: Literal['confirmed', 'denied', 'cancelled'],
    ignore_csrf: bool = False,
    raises: bool = False,
    no_messages: bool = False,
    force_email: bool = False,
    return_url: str | None = None,
) -> Response | None:

    if not ignore_csrf:
        request.assert_valid_csrf_token()

    if action == 'confirmed':
        subject = _('Your registration has been confirmed')
        success = _('The registration has been confirmed')
        failure = _('The registration could not be confirmed because the '
                    'maximum number of participants has been reached')

        def execute() -> bool:
            if self.registration_window and self.claimed is None:
                return self.claim()
            return False

    elif action == 'denied':
        subject = _('Your registration has been denied')
        success = _('The registration has been denied')
        failure = _('The registration could not be denied')

        def execute() -> bool:
            if self.registration_window and self.claimed is None:
                self.disclaim()
                return True
            return False

    elif action == 'cancelled':
        subject = _('Your registration has been cancelled')
        success = _('The registration has been cancelled')
        failure = _('The registration could not be cancelled')

        def execute() -> bool:
            if self.registration_window and self.claimed:
                self.disclaim()
                return True
            return False

    else:
        raise AssertionError('unreachable')

    if execute():
        assert self.email is not None
        ticket = TicketCollection(request.session).by_handler_id(self.id.hex)
        assert ticket is not None

        send_ticket_mail(
            request=request,
            template='mail_registration_action.pt',
            receivers=(self.email, ),
            ticket=ticket,
            content={
                'model': self,
                'action': action,
                'ticket': ticket,
                'form': self.form_obj,
                'show_submission': self.meta.get('show_submission')
            },
            subject=subject,
            force=force_email
        )

        SubmissionMessage.create(ticket, request, action)
        if not no_messages:
            request.success(success)
    else:
        if raises:
            raise ValueError(request.translate(failure))
        if not no_messages:
            request.alert(failure)
            return None

    if return_url is None:
        return_url = request.link(self)

    return request.redirect(return_url)


@OrgApp.html(model=SurveySubmission,
             template='survey_submission.pt',
             permission=Public, request_method='GET')
@OrgApp.html(model=SurveySubmission,
             template='survey_submission.pt',
             permission=Public, request_method='POST')
def handle_survey_submission(
    self: SurveySubmission,
    request: OrgRequest,
    layout: SurveySubmissionLayout | None = None
) -> RenderData | Response:
    """ Renders a pending submission, takes it's input and allows the
    user to turn the submission into a complete submission, once all data
    is valid.
    """
    collection = SurveyCollection(request.session)

    form = request.get_form(self.form_class, data=self.data)
    form.action = request.link(self)
    form.model = self

    if 'edit' not in request.GET:
        form.validate()

    if not request.POST:
        form.ignore_csrf_error()
    elif not form.errors:
        collection.submissions.update(self, form)

    completable = not form.errors and 'edit' not in request.GET

    if completable and 'return-to' in request.GET:

        if 'quiet' not in request.GET:
            request.success(_('Your changes were saved'))

        # the default url should actually never be called
        return request.redirect(request.url)

    if 'title' in request.GET:
        title = request.GET['title']
    else:
        assert self.survey is not None
        title = self.survey.title

    # retain some parameters in links (the rest throw away)
    form.action = copy_query(
        request, form.action, ('return-to', 'title', 'quiet'))

    edit_url_obj = URL(copy_query(
        request, request.link(self), ('title', )))

    # the edit url always points to the editable state
    edit_url_obj = edit_url_obj.query_param('edit', '')
    edit_url = edit_url_obj.as_string()

    layout = layout or SurveySubmissionLayout(self, request, title)
    layout.editbar_links = []

    return {
        'layout': layout or SurveySubmissionLayout(self, request, title),
        'title': title,
        'form': form,
        'completable': completable,
        'edit_link': edit_url,
        'complete_link': request.link(self, 'complete'),
        'model': self,
        'price': None,
    }
