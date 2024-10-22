""" Renders and handles defined forms, turning them into submissions. """

import morepath

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
from onegov.org.layout import FormSubmissionLayout, SurveySubmissionLayout
from onegov.org.mail import send_ticket_mail
from onegov.org.utils import user_group_emails_for_new_ticket
from onegov.org.models import TicketMessage, SubmissionMessage
from onegov.pay import PaymentError, Price
from purl import URL
from webob.exc import HTTPNotFound


from typing import Literal, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterable
    from onegov.core.types import RenderData
    from onegov.form import Form, FormSubmission
    from onegov.org.request import OrgRequest
    from webob import Response


def copy_query(
    request: 'OrgRequest',
    url: str,
    fields: 'Iterable[str]'
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


def get_price(
    request: 'OrgRequest',
    form: 'Form',
    submission: 'FormSubmission'
) -> Price | None:

    total = form.total()

    if 'price' in submission.meta:
        if total is not None:
            total += Price(**submission.meta['price'])
        else:
            total = Price(**submission.meta['price'])

    return request.app.adjust_price(total)


@OrgApp.html(model=PendingFormSubmission, template='submission.pt',
             permission=Public, request_method='GET')
@OrgApp.html(model=PendingFormSubmission, template='submission.pt',
             permission=Public, request_method='POST')
@OrgApp.html(model=CompleteFormSubmission, template='submission.pt',
             permission=Private, request_method='GET')
@OrgApp.html(model=CompleteFormSubmission, template='submission.pt',
             permission=Private, request_method='POST')
def handle_pending_submission(
    self: PendingFormSubmission | CompleteFormSubmission,
    request: 'OrgRequest',
    layout: FormSubmissionLayout | None = None
) -> 'RenderData | Response':
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
    price = get_price(request, form, self)

    # check minimum price total if set
    current_total_amount = price and price.amount or 0.0
    minimum_total_amount = self.minimum_price_total or 0.0
    if current_total_amount < minimum_total_amount:
        if price is not None:
            currency = price.currency
        else:
            # We just pick the first currency from any pricing rule we can find
            # if we can't find any, then we fall back to 'CHF'. Although that
            # should be an invalid form definition.
            currency = 'CHF'
            for field in form._fields.values():
                if not hasattr(field, 'pricing'):
                    continue

                rules = field.pricing.rules
                if not rules:
                    continue

                currency = next(iter(rules.values())).currency
                break

        completable = False
        request.alert(
            _(
                'The total amount for the currently entered data '
                'is ${total} but has to be at least ${minimum}. '
                'Please adjust your inputs.',
                mapping={
                    'total': Price(current_total_amount, currency),
                    'minimum': Price(minimum_total_amount, currency)
                }
            )
        )

    if completable and 'return-to' in request.GET:

        if 'quiet' not in request.GET:
            request.success(_('Your changes were saved'))

        # the default url should actually never be called
        return request.redirect(request.url)

    if 'title' in request.GET:
        title = request.GET['title']
    else:
        assert self.form is not None
        title = self.form.title

    # retain some parameters in links (the rest throw away)
    form.action = copy_query(
        request, form.action, ('return-to', 'title', 'quiet'))

    edit_url_obj = URL(copy_query(
        request, request.link(self), ('title', )))

    # the edit url always points to the editable state
    edit_url_obj = edit_url_obj.query_param('edit', '')
    edit_url = edit_url_obj.as_string()

    email = self.email or self.get_email_field_data(form)
    if price:
        assert email is not None
        assert request.locale is not None
        checkout_button = request.app.checkout_button(
            button_label=request.translate(_('Pay Online and Complete')),
            title=title,
            price=price,
            email=email,
            locale=request.locale
        )
    else:
        checkout_button = None

    return {
        'layout': layout or FormSubmissionLayout(self, request, title),
        'title': title,
        'form': form,
        'completable': completable,
        'edit_link': edit_url,
        'complete_link': request.link(self, 'complete'),
        'model': self,
        'price': price,
        'checkout_button': checkout_button
    }


@OrgApp.view(model=PendingFormSubmission, name='complete',
             permission=Public, request_method='POST')
@OrgApp.view(model=CompleteFormSubmission, name='complete',
             permission=Private, request_method='POST')
def handle_complete_submission(
    self: PendingFormSubmission | CompleteFormSubmission,
    request: 'OrgRequest'
) -> 'Response':

    form = request.get_form(self.form_class)
    form.process(data=self.data)
    form.model = self

    # we're not really using a csrf protected form here (the complete form
    # button is basically just there so we can use a POST instead of a GET)
    form.validate()
    form.ignore_csrf_error()

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
            token = request.params.get('payment_token')
            if not isinstance(token, str):
                token = None

            price = get_price(request, form, self)
            payment = self.process_payment(price, provider, token)

            # FIXME: Custom error message for PaymentError?
            if not payment or isinstance(payment, PaymentError):
                request.alert(_('Your payment could not be processed'))
                return morepath.redirect(request.link(self))
            elif payment is not True:
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
                TicketMessage.create(ticket, request, 'opened')

            assert self.email is not None
            send_ticket_mail(
                request=request,
                template='mail_ticket_opened.pt',
                subject=_('Your request has been registered'),
                ticket=ticket,
                receivers=(self.email, ),
                content={
                    'model': ticket,
                    'form': form,
                    'show_submission': self.meta['show_submission']
                }
            )
            directory_user_group_recipients = user_group_emails_for_new_ticket(
                request, ticket
            )
            if request.email_for_new_tickets:
                send_ticket_mail(
                    request=request,
                    template='mail_ticket_opened_info.pt',
                    subject=_('New ticket'),
                    ticket=ticket,
                    receivers=(
                        request.email_for_new_tickets,
                        *directory_user_group_recipients,
                    ),
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
    request: 'OrgRequest'
) -> 'Response':
    ticket = TicketCollection(request.session).by_handler_id(self.id.hex)
    if not ticket:
        raise HTTPNotFound()
    return request.redirect(request.link(ticket))


@OrgApp.view(model=CompleteFormSubmission, name='confirm-registration',
             permission=Private, request_method='POST')
def handle_accept_registration(
    self: CompleteFormSubmission,
    request: 'OrgRequest'
) -> 'Response | None':
    return handle_submission_action(self, request, 'confirmed')


@OrgApp.view(model=CompleteFormSubmission, name='deny-registration',
             permission=Private, request_method='POST')
def handle_deny_registration(
    self: CompleteFormSubmission,
    request: 'OrgRequest'
) -> 'Response | None':
    return handle_submission_action(self, request, 'denied')


@OrgApp.view(model=CompleteFormSubmission, name='cancel-registration',
             permission=Private, request_method='POST')
def handle_cancel_registration(
    self: CompleteFormSubmission,
    request: 'OrgRequest'
) -> 'Response | None':
    return handle_submission_action(self, request, 'cancelled')


def handle_submission_action(
    self: CompleteFormSubmission,
    request: 'OrgRequest',
    action: Literal['confirmed', 'denied', 'cancelled'],
    ignore_csrf: bool = False,
    raises: bool = False,
    no_messages: bool = False,
    force_email: bool = False
) -> 'Response | None':

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

    return request.redirect(request.link(self))


@OrgApp.html(model=SurveySubmission,
             template='survey_submission.pt',
             permission=Private, request_method='GET')
@OrgApp.html(model=SurveySubmission,
             template='survey_submission.pt',
             permission=Private, request_method='POST')
def handle_survey_submission(
    self: SurveySubmission,
    request: 'OrgRequest',
    layout: SurveySubmissionLayout | None = None
) -> 'RenderData | Response':
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

