from __future__ import annotations

import isodate
import morepath
import pytz
import sedate
import transaction

from datetime import date, time, timedelta
from libres.modules.errors import LibresError
from onegov.core.custom import json, msgpack
from onegov.core.html import html_to_text
from onegov.core.security import Public, Private
from onegov.core.templates import render_template
from onegov.form import FormCollection, merge_forms, as_internal_id
from onegov.org import _, log, OrgApp
from onegov.org import utils
from onegov.org.cli import close_ticket
from onegov.org.elements import Link
from onegov.org.forms import (
    AddReservationForm, KabaEditForm, ReservationAdjustmentForm,
    ReservationForm, InternalTicketChatMessageForm)
from onegov.org.kaba import KabaApiError, KabaClient
from onegov.org.layout import ReservationLayout, TicketChatMessageLayout
from onegov.org.layout import DefaultMailLayout, TicketLayout
from onegov.org.mail import send_ticket_mail
from onegov.org.models import (
    TicketMessage, TicketChatMessage, ReservationAdjustedMessage,
    ReservationMessage, ResourceRecipient, ResourceRecipientCollection)
from onegov.org.models.resource import FindYourSpotCollection
from onegov.org.models.ticket import ReservationTicket
from onegov.org.utils import emails_for_new_ticket, group_invoice_items
from onegov.pay import InvoiceItemMeta, PaymentError, Price
from onegov.reservation import Allocation, Reservation, Resource
from onegov.reservation.collection import ResourceCollection
from onegov.ticket import TicketCollection, TicketInvoice
from onegov.user import Auth
from onegov.user.collections import TANCollection
from purl import URL
from uuid import uuid4
from webob import exc, Response
from wtforms import HiddenField


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Collection, Iterable, Iterator, Sequence
    from onegov.core.types import EmailJsonDict, JSON_ro, RenderData
    from onegov.form import Form
    from onegov.org.request import OrgRequest
    from onegov.reservation import Reservation


def assert_anonymous_access_only_temporary(
    resource: Resource,
    reservation: Reservation,
    request: OrgRequest
) -> None:
    """ Raises exceptions if the current user is anonymous and no longer
    should be given access to the reservation models.

    This could probably be done using morepath's security system, but it would
    not be quite as straight-forward. This approach is, though we have
    to manually add this function to all reservation views the anonymous user
    should be able to access when creating a new reservatin, but not anymore
    after that.

    """
    if request.is_manager:
        return

    if not reservation.session_id:
        raise exc.HTTPForbidden()

    if reservation.status == 'approved':
        raise exc.HTTPForbidden()

    # FIXME: should this method be moved to the base class?
    assert hasattr(resource, 'bound_session_id')
    if reservation.session_id != resource.bound_session_id(request):
        raise exc.HTTPForbidden()


def assert_access_only_if_there_are_reservations(
    reservations: Collection[Any]
) -> None:
    """ Raises an exception if no reservations are available. """
    if not reservations:
        raise exc.HTTPForbidden()


def respond_with_success(request: OrgRequest) -> JSON_ro:
    @request.after
    def trigger_calendar_update(response: Response) -> None:
        response.headers.add('X-IC-Trigger', 'rc-reservations-changed')

    return {
        'success': True
    }


def respond_with_error(request: OrgRequest, error: str) -> JSON_ro:
    message: JSON_ro = {
        'message': error,
        'success': False
    }

    @request.after
    def trigger(response: Response) -> None:
        response.headers.add('X-IC-Trigger', 'rc-reservation-error')
        response.headers.add(
            'X-IC-Trigger-Data',
            json.dumps(message, ensure_ascii=True)
        )

    return message


@OrgApp.json(
    model=Allocation,
    name='reserve',
    request_method='POST',
    permission=Public
)
def reserve_allocation(self: Allocation, request: OrgRequest) -> JSON_ro:
    """ Adds a single reservation to the list of reservations bound to the
    current browser session.

    Does not actually reserve anything, just keeps a list of things to
    reserve later. Though it will still check if the reservation is
    feasible.

    """

    # the reservation is defined through query parameters
    start_str = request.params.get('start') or f'{self.start:%H:%M}'
    end_str = request.params.get('end') or f'{self.end:%H:%M}'
    if not isinstance(start_str, str) or not isinstance(end_str, str):
        raise exc.HTTPBadRequest()

    quota_str = request.params.get('quota', '1')
    if not isinstance(quota_str, str) or not quota_str.isdigit():
        raise exc.HTTPBadRequest()

    quota = int(quota_str)
    whole_day = request.params.get('whole_day') == '1'

    if self.partly_available:
        if self.whole_day and whole_day:
            start_time = time(0, 0)
            end_time = time(23, 59)
        else:
            start_time = sedate.parse_time(start_str)
            end_time = sedate.parse_time(end_str)

        try:
            start, end = sedate.get_date_range(
                self.display_start(),
                start_time,
                end_time,
                raise_non_existent=True
            )
        except pytz.NonExistentTimeError:
            err = request.translate(_(
                'The selected time does not exist on this date due to '
                'the switch from standard time to daylight saving time.'
            ))
            return respond_with_error(request, err)
    else:
        start, end = self.start, self.end

    resource = request.app.libres_resources.by_allocation(self)
    # FIXME: should this method be moved to the base class?
    assert resource is not None and hasattr(resource, 'bound_session_id')

    # if there's a deadline, make sure to observe it for anonymous users...
    if not request.is_manager and resource.is_past_deadline(start):
        assert resource.deadline is not None
        unit: str
        n, unit = resource.deadline

        if unit == 'h' and n == 1:
            unit = request.translate(_('hour'))

        elif unit == 'h' and n > 1:
            unit = request.translate(_('hours'))

        elif unit == 'd' and n == 1:
            unit = request.translate(_('day'))

        elif unit == 'd' and n > 1:
            unit = request.translate(_('days'))

        else:
            raise NotImplementedError()

        err = request.translate(
            _('Reservations must be made ${n} ${unit} in advance', mapping={
                'n': n,
                'unit': unit
            })
        )

        return respond_with_error(request, err)

    # if the allocation is in the past, disable it for anonymous users...
    if not request.is_manager and end < sedate.utcnow():
        err = request.translate(_('This date lies in the past'))

        return respond_with_error(request, err)

    # ...otherwise, try to reserve
    try:
        # Todo: This entry created remained after a reservation
        # and the session id got lost
        resource.scheduler.reserve(
            email='0xdeadbeef@example.org',  # will be set later
            dates=(start, end),
            quota=quota,
            session_id=resource.bound_session_id(request),
            single_token_per_session=True
        )
    except LibresError as e:
        return respond_with_error(request, utils.get_libres_error(e, request))
    else:
        return respond_with_success(request)


@OrgApp.json(model=Reservation, request_method='DELETE', permission=Public)
def delete_reservation(self: Reservation, request: OrgRequest) -> JSON_ro:

    # anonymous users do not get a csrf token (it's bound to the identity)
    # therefore we can't check for it -> this is not a problem since
    # anonymous users do not really have much to lose here
    # FIXME: We always generate a csrf token now, so we could reconsider
    #        this, although it would mean, that people, that have blocked
    #        cookies, will not be able to delete reservations at all.
    if request.is_logged_in:
        request.assert_valid_csrf_token()

    resource = request.app.libres_resources.by_reservation(self)
    assert resource is not None

    # this view is public, but only for a limited time
    assert_anonymous_access_only_temporary(resource, self, request)
    tickets = TicketCollection(request.session)
    ticket = tickets.by_handler_id(self.token.hex)

    try:
        if ticket:
            ticket.create_snapshot(request)
        resource.scheduler.remove_reservation(self.token, self.id)
    except LibresError as e:
        return respond_with_error(request, utils.get_libres_error(e, request))
    else:
        return respond_with_success(request)


def get_reservation_form_class(
    resource: Resource,
    request: OrgRequest
) -> type[ReservationForm]:

    if resource.definition:
        form_class = resource.form_class
        assert form_class is not None
        return merge_forms(ReservationForm, form_class)
    else:
        return ReservationForm


@OrgApp.form(
    model=Resource,
    name='form',
    template='reservation_form.pt',
    permission=Public,
    form=get_reservation_form_class
)
def handle_reservation_form(
    self: Resource,
    request: OrgRequest,
    form: ReservationForm,
    layout: ReservationLayout | None = None
) -> RenderData | Response:
    """ Asks the user for the form data required to complete one or many
    reservations on a resource.

    """
    reservations_query = self.bound_reservations(request, with_data=True)  # type: ignore[attr-defined]
    reservations: tuple[Reservation, ...] = tuple(reservations_query)

    assert_access_only_if_there_are_reservations(reservations)

    # all reservations share a single token
    token = reservations[0].token

    # the submission shares the reservation token
    forms = FormCollection(request.session)
    submission = forms.submissions.by_id(token)

    # update the data if the form is submitted (even if invalid)
    if request.POST:
        assert form.email.data is not None

        if 'ticket_tag' in form:
            reserved_labels = {str(field.label.text) for field in form}
            filtered_meta = {}
            for item in request.app.org.ticket_tags:
                if not isinstance(item, dict):
                    continue

                key, meta = next(iter(item.items()))
                if key != form.ticket_tag.data:
                    continue

                # set any static data that isn't set
                # by the form itself
                filtered_meta = {
                    key: value
                    for key, value in meta.items()
                    if key not in reserved_labels
                }
                break

        # update the e-mail and tag data
        for reservation in reservations:
            reservation.email = form.email.data
            if 'ticket_tag' in form:
                data = reservation.data
                if data is None:
                    data = reservation.data = {}
                data['ticket_tag'] = form.ticket_tag.data
                if filtered_meta:
                    data['ticket_tag_meta'] = filtered_meta

        # while we re at it, remove all expired sessions
        # FIXME: Should this be part of the base class?
        self.remove_expired_reservation_sessions()  # type: ignore[attr-defined]

        # add the submission if it doesn't yet exist
        if self.definition and not submission:
            form_class = self.form_class
            assert form_class is not None
            submission = forms.submissions.add_external(
                form=form_class(),
                state='pending',
                id=token,
                payment_method=self.payment_method,
                minimum_price_total=self.minimum_price_total,
            )

        # update the data on the submission
        if submission:
            forms.submissions.update(
                submission, form, exclude=form.reserved_fields
            )

    # enforce the zip-code block if configured
    if request.POST:
        blocked = blocked_by_zipcode(request, self, form, reservations)
    else:
        blocked = {}

    # go to the next step if the submitted data is valid
    if form.submitted(request) and not blocked:
        # also remember submitted form data
        remembered: dict[str, Any]
        remembered = request.browser_session.get('field_submissions', {})
        remembered.update({
            f'{field.id}+{field.type}': field.data
            for field in form
            if not isinstance(field, HiddenField)
        })
        # only remember the data if we can encode the data to msgpack
        if msgpack.packable(remembered):
            request.browser_session.field_submissions = remembered
        return morepath.redirect(request.link(self, 'confirmation'))
    else:
        data = {}

        # the email is the same for all reservations
        # Todo: This entry created remained after a reservation
        if reservations[0].email != '0xdeadbeef@example.org':
            data['email'] = reservations[0].email

        # set defaults based on remembered submissions from session
        # TODO: should we first apply defaults based on the remembered tag?
        if not request.POST and (remembered := {
            field_id: value
            for key, value in request.browser_session.get(
                'field_submissions', {}).items()
            if (field_id := (pair := key.split('+', 1))[0]) in form
            if form[field_id].type == pair[1]
        }):
            data.update(remembered)

        if submission:
            data.update(submission.data)

        form.process(data=data)

    if not form.errors and blocked:
        request.alert(_(
            'The form contains errors. Please check the marked fields.'
        ))

    layout = layout or layout or ReservationLayout(self, request)
    layout.breadcrumbs.append(Link(_('Reserve'), '#'))

    title = _('New dates for ${title}', mapping={
        'title': self.title,
    })

    return {
        'layout': layout,
        'title': title,
        'form': form,
        'blocked': blocked,
        'zipcodes': self.zipcode_block and self.zipcode_block['zipcode_list'],
        'reservation_infos': [
            utils.ReservationInfo(self, r, request) for r in reservations
        ],
        'resource': self,
        'button_text': _('Continue')
    }


def get_next_resource_context(
    reservations: dict[Resource, list[Reservation]]
) -> Resource:
    # pick the resource with the most reservations, but if there
    # is a tie, pick the one with the earliest reservation
    selected: tuple[Resource, list[Reservation]] | None = None
    for item in reservations.items():
        if selected is None:
            selected = item
            continue

        max_len = len(selected[1])
        cur_len = len(item[1])
        if cur_len > max_len:
            selected = item
        elif cur_len == max_len:
            # FIXME: Technically Reservation.start is nullable, but
            #        we don't really ever set it to None, so we may
            #        just need to fix this in libres, since it probably
            #        doesn't make sense for a Reservation to not have
            #        a start or end anyways.
            if selected[1][0].start > item[1][0].start:  # type:ignore
                selected = item

    if selected is None:
        raise exc.HTTPNotFound()

    return selected[0]


@OrgApp.view(model=FindYourSpotCollection, name='form', permission=Public)
def handle_find_your_spot_reservation_form(
    self: FindYourSpotCollection,
    request: OrgRequest
) -> Response:
    """ This is a convenience view that redirects to the appropriate
    resource specific reservation form.

    """
    reservations = {
        resource: bound
        for resource in request.exclude_invisible(self.query())
        if (bound := list(resource.bound_reservations(request)))  # type:ignore
    }

    assert_access_only_if_there_are_reservations(reservations)

    resource = get_next_resource_context(reservations)
    return morepath.redirect(request.link(resource, 'form'))


def blocked_by_zipcode(
    request: OrgRequest,
    resource: Resource,
    form: Form,
    reservations: Iterable[Reservation]
) -> dict[int, date]:
    """ Returns a dict of reservation ids that are blocked by zipcode, with
    the value set to the date it will be available.

    """

    if request.is_manager:
        return {}

    if not resource.zipcode_block:
        return {}

    field_id = as_internal_id(resource.zipcode_block['zipcode_field'])
    zipcode = (getattr(form, field_id).data or '').replace(' ', '')
    excempt = resource.zipcode_block['zipcode_list']

    if zipcode and zipcode.isdigit() and int(zipcode) in excempt:
        return {}

    blocked = {}
    days = resource.zipcode_block['zipcode_days']

    for reservation in reservations:
        date = reservation.display_start().date()

        if resource.is_zip_blocked(date):
            blocked[reservation.id] = date - timedelta(days=days)

    return blocked


@OrgApp.html(
    model=Resource,
    name='confirmation',
    permission=Public,
    template='reservation_confirmation.pt'
)
def confirm_reservation(
    self: Resource,
    request: OrgRequest,
    layout: ReservationLayout | None = None
) -> RenderData:

    reservations: list[Reservation]
    reservations = self.bound_reservations(request).all()  # type: ignore[attr-defined]
    assert_access_only_if_there_are_reservations(reservations)

    token = reservations[0].token

    forms = FormCollection(request.session)
    submission = forms.submissions.by_id(token)

    if submission:
        form = request.get_form(submission.form_class, data=submission.data)
        item_extra = {'submission_id': submission.id}
        extras = form.invoice_items(extra=item_extra)
        discounts = form.discount_items(extra=item_extra)
        credit_card_payment = any(
            price.credit_card_payment
            for __, price in form.prices()
        )
        # TODO: We may want to add an option for whether or not the discount
        #       should apply to extras or not. For now the discount doesn't
        #       apply to extras.
    else:
        form = None
        credit_card_payment = False
        extras = []
        discounts = []

    layout = layout or ReservationLayout(self, request)
    layout.breadcrumbs.append(Link(_('Confirm'), '#'))

    failed_reservations_str = request.params.get('failed_reservations')
    if not isinstance(failed_reservations_str, str):
        failed_reservations_str = ''

    failed_reservations = {
        int(failed)
        for failed in failed_reservations_str.split(',')
        if failed and failed.isdigit()
    }

    invoice_items = self.invoice_items_for_reservation(
        reservations,
        extras,
        discounts,
        reduced_amount_label=request.translate(_('Discount'))
    )
    total_amount = InvoiceItemMeta.total(invoice_items)
    price = request.app.adjust_price(Price(
        total_amount,
        self.currency,
        credit_card_payment=credit_card_payment
    ) if total_amount > 0 else None)

    assert request.locale is not None
    return {
        'title': _('Confirm your reservation'),
        'layout': layout,
        'form': form,
        'resource': self,
        'reservation_infos': [
            utils.ReservationInfo(self, r, request) for r in reservations
        ],
        'failed_reservations': failed_reservations,
        'complete_link': request.link(self, 'finish'),
        'edit_link': request.link(self, 'form'),
        'price': price,
        'invoice_items': group_invoice_items(invoice_items),
        'total_amount': total_amount,
        # TODO: Once reservations can include VAT, this should change
        'total_vat': None,
        'checkout_button': price and request.app.checkout_button(
            button_label=request.translate(_('Pay Online and Complete')),
            title=self.title,
            price=price,
            email=reservations[0].email,
            complete_url=request.link(self, 'finish'),
            request=request,
        )
    }


@OrgApp.html(
    model=Resource,
    name='finish',
    permission=Public,
    template='layout.pt',
    request_method='GET'
)
@OrgApp.html(
    model=Resource,
    name='finish',
    permission=Public,
    template='layout.pt',
    request_method='POST'
)
def finalize_reservation(self: Resource, request: OrgRequest) -> Response:
    reservations: list[Reservation]
    reservations = self.bound_reservations(request, with_data=True).all()  # type: ignore[attr-defined]
    assert_access_only_if_there_are_reservations(reservations)

    session_id = self.bound_session_id(request)  # type:ignore
    token = reservations[0].token

    forms = FormCollection(request.session)
    submission = forms.submissions.by_id(token)
    provider = request.app.default_payment_provider
    if request.method == 'GET' and (
        provider is None or not provider.payment_via_get
    ):
        # TODO: A redirect back to the previous step with an error might
        #       be better UX, if this error can occur too easily...
        raise exc.HTTPMethodNotAllowed()

    try:
        payment_token = provider.get_token(request) if provider else None
        # TODO: We may want to add an option for whether or not the discount
        #       should apply to extras or not. For now the discount doesn't
        #       apply to extras.
        if submission:
            _form_obj = submission.form_obj
            item_extra = {'submission_id': submission.id}
            extras = _form_obj.invoice_items(extra=item_extra)
            discounts = _form_obj.discount_items(extra=item_extra)
            credit_card_payment = any(
                price.credit_card_payment
                for __, price in _form_obj.prices()
            )
        else:
            credit_card_payment = False
            extras = []
            discounts = []

        invoice_items = self.invoice_items_for_reservation(
            reservations,
            extras,
            discounts,
            reduced_amount_label=request.translate(_('Discount'))
        )
        amount = InvoiceItemMeta.total(invoice_items)
        price = request.app.adjust_price(Price(
            amount,
            self.currency,
            credit_card_payment=credit_card_payment
        ) if amount > 0 else None)

        payment = self.process_payment(price, provider, payment_token)

        # FIXME: Payment errors should probably have their own error message
        if not payment or isinstance(payment, PaymentError):
            request.alert(_('Your payment could not be processed'))
            return morepath.redirect(request.link(self))

        elif payment is not True:
            for reservation in reservations:
                reservation.payment = payment

        self.scheduler.queries.confirm_reservations_for_session(session_id)
        self.scheduler.approve_reservations(token)

    except LibresError as e:
        transaction.abort()
        utils.show_libres_error(e, request)

        url_obj = URL(request.link(self, name='confirmation'))
        url_obj = url_obj.query_param(
            'failed_reservations', str(e.reservation.id))

        return morepath.redirect(url_obj.as_string())

    if submission:
        forms.submissions.complete_submission(submission)

    with request.session.no_autoflush:
        ticket = TicketCollection(request.session).open_ticket(
            handler_code='RSV', handler_id=token.hex
        )
        if getattr(self, 'kaba_components', []):
            # populate key code defaults
            ticket.handler_data = {
                'key_code': KabaClient.random_code(),
                'key_code_lead_time':
                    request.app.org.default_key_code_lead_time,
                'key_code_lag_time':
                    request.app.org.default_key_code_lag_time,
            }
        if data := reservations[0].data:
            ticket.tag = data.get('ticket_tag')
            tag_meta = data.get('ticket_tag_meta', {})
            key_code = tag_meta.pop('Kaba Code', None)
            tag_meta.pop('Color', None)
            if key_code and ticket.handler_data:
                # set associated key code
                ticket.handler_data['key_code'] = key_code
            ticket.tag_meta = tag_meta

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
        TicketMessage.create(ticket, request, 'opened', 'external')

    show_submission = request.params.get('send_by_email') == 'yes'

    if submission and show_submission:
        form = submission.form_obj
    else:
        form = None

    send_ticket_mail(
        request=request,
        template='mail_ticket_opened.pt',
        subject=_('Your request has been registered'),
        receivers=(reservations[0].email,),
        ticket=ticket,
        content={
            'model': ticket,
            'resource': self,
            'reservations': reservations,
            'form': form,
            'show_submission': show_submission
        }
    )
    for email in emails_for_new_ticket(request, ticket):
        send_ticket_mail(
            request=request,
            template='mail_ticket_opened_info.pt',
            subject=_('New ticket'),
            ticket=ticket,
            receivers=(email, ),
            content={
                'model': ticket,
                'resource': self,
                'reservations': reservations,
            }
        )

    request.app.send_websocket(
        channel=request.app.websockets_private_channel,
        message={
            'event': 'browser-notification',
            'title': request.translate(_('New ticket')),
            'created': ticket.created.isoformat()
        },
        groupids=request.app.groupids_for_ticket(ticket),
    )

    if request.auto_accept(ticket):
        try:
            assert request.auto_accept_user is not None
            ticket.accept_ticket(request.auto_accept_user)
            request.view(reservations[0], name='accept')
        except Exception:
            request.warning(_('Your request could not be '
                              'accepted automatically!'))
        else:
            close_ticket(ticket, request.auto_accept_user, request)

    collection = FindYourSpotCollection(
        request.app.libres_context, self.group)
    pending: dict[Resource, list[Reservation]] = {
        resource: bound
        for resource in request.exclude_invisible(collection.query())
        if (bound := list(
            resource.bound_reservations(request)  # type:ignore
        ))
    }

    # by default we will redirect to the created ticket
    message = _('Thank you for your reservation!')
    url = request.link(ticket, 'status')

    # retrieve remembered tickets
    tickets: dict[str | None, list[str]]
    tickets = request.browser_session.get('reservation_tickets', {})

    # continue to the next resource in this group with pending reservations
    if pending:
        resource = get_next_resource_context(pending)

        # remember ticket so we can show them all at the end
        tickets.setdefault(self.group, []).append(str(ticket.id))
        request.browser_session.reservation_tickets = tickets

        message = _(
            'Your reservation for ${room} has been submitted. '
            'Please continue with your reservation for ${next_room}.',
            mapping={'room': self.title, 'next_room': resource.title})
        url = request.link(resource, 'form')

    # if we remembered tickets for this group that means
    # we never showed them so now we need to show them all
    elif self.group in tickets:
        tickets[self.group].append(str(ticket.id))
        request.browser_session.reservation_tickets = tickets
        url = request.link(collection, 'tickets')

    request.success(message)

    return morepath.redirect(url)


def get_my_reservations_url(request: OrgRequest, email: str) -> str | None:
    if not request.app.org.citizen_login_enabled:
        return None

    auth = Auth.from_request(
        request,
        to=request.class_link(
            ResourceCollection,
            name='my-reservations'
        )
    )
    tans = TANCollection(request.session, scope='citizen-login')
    tan_obj = tans.add(
        client='unknown',
        email=email,
        redirect_to=auth.to,
    )
    return request.link(
        auth,
        name='confirm-citizen-login',
        query_params={'token': tan_obj.tan}
    )


@OrgApp.view(model=Reservation, name='accept', permission=Private)
def accept_reservation(
    self: Reservation,
    request: OrgRequest,
    text: str | None = None,
    notify: bool = False,
    view_ticket: ReservationTicket | None = None,
) -> Response:

    resource = request.app.libres_resources.by_reservation(self)
    assert resource is not None
    reservations = [
        reservation
        for reservation in resource.scheduler
                           .reservations_by_token(self.token)
                           .order_by(Reservation.start)
        if not (reservation.data or {}).get('accepted')
    ]

    if reservations:
        token = self.token
        tickets = TicketCollection(request.session)
        ticket = tickets.by_handler_id(token.hex)
        assert ticket is not None

        # if we're accessing this view through the ticket it
        # had better match the ticket we retrieved
        if view_ticket is not None and view_ticket != ticket:
            raise exc.HTTPNotFound()

        forms = FormCollection(request.session)
        submission = forms.submissions.by_id(token)

        if submission:
            form = submission.form_obj
        else:
            form = None

        # Include all the forms details to be able to print it out
        show_submission = True

        clients = KabaClient.from_resource(resource, request.app)
        if clients:
            # compute the things we need inside the loop once
            components: dict[str, list[str]] = {}
            for site_id, component in resource.kaba_components:  # type: ignore[attr-defined]
                components.setdefault(site_id, []).append(component)
            code = ticket.handler.data.setdefault(
                'key_code', next(iter(clients.values())).random_code()
            )
            lead_delta = timedelta(minutes=ticket.handler.data.setdefault(
                'key_code_lead_time',
                request.app.org.default_key_code_lead_time
            ))
            lag_delta = timedelta(minutes=ticket.handler.data.setdefault(
                'key_code_lag_time',
                request.app.org.default_key_code_lag_time
            ))
            ticket.handler.refresh()
        else:
            code = None
            lead_delta = timedelta(minutes=0)

        savepoint = transaction.savepoint()

        now = sedate.utcnow()
        for reservation in reservations:
            data = reservation.data
            if data is None:
                data = reservation.data = {}
            data['accepted'] = True

            # NOTE: We can only create future visits
            start = reservation.display_start() - lead_delta
            if clients and start > now:
                visit_ids = {}
                end = reservation.display_end() + lag_delta
                for site_id, group in components.items():
                    assert code is not None
                    try:
                        visit_id = clients[site_id].create_visit(
                            code=code,
                            name=ticket.number,
                            message='Managed through OneGov Cloud',
                            start=start,
                            end=end,
                            components=group,
                        )
                    except (KeyError, KabaApiError) as exc:
                        if isinstance(exc, KabaApiError):
                            log.info('Kaba API error', exc_info=True)

                        # roll back previous changes
                        savepoint.rollback()
                        request.alert(_(
                            'Failed to create visits using the dormakaba API '
                            'for site ID ${site_id} please make sure your '
                            'credentials are still valid.',
                            mapping={'site_id': site_id}
                        ))
                        if view_ticket is not None:
                            return request.redirect(request.link(view_ticket))

                        return request.redirect(request.link(self))
                    else:
                        visit_ids[site_id] = visit_id

                data['kaba'] = {
                    'code': code,
                    'visit_ids': visit_ids,
                }

        ReservationMessage.create(
            reservations,
            ticket,
            request,
            'accepted'
        )

        message = None
        if text:
            assert request.current_username is not None
            message = TicketChatMessage.create(
                ticket,
                request,
                text=text,
                owner=request.current_username,
                recipient=self.email,
                notify=notify,
                origin='internal',
            )

        send_ticket_mail(
            request=request,
            template='mail_reservation_accepted.pt',
            subject=_('Your reservations were accepted'),
            receivers=(self.email,),
            ticket=ticket,
            content={
                'model': self,
                'resource': resource,
                'reservations': reservations,
                'show_submission': show_submission,
                'code': code,
                'form': form,
                'message': message,
                'my_reservations_url': get_my_reservations_url(
                    request, self.email
                ),
            },
        )

        def recipients_which_have_registered_for_mail() -> Iterator[str]:
            q = ResourceRecipientCollection(request.session).query()
            q = q.filter(ResourceRecipient.medium == 'email')
            q = q.order_by(None).order_by(ResourceRecipient.address)
            q = q.with_entities(
                ResourceRecipient.address, ResourceRecipient.content
            )

            for res in q:
                if self.resource.hex in res.content[
                    'resources'
                ] and res.content.get('new_reservations', False):
                    yield res.address

        title = request.translate(
            _(
                'Reservation(s) confirmed ${org} ${resource}',
                mapping={
                    'org': request.app.org.title,
                    'resource': resource.title,
                },
            )
        )

        content = render_template(
            'mail_new_reservation_notification.pt',
            request,
            {
                'layout': DefaultMailLayout(object(), request),
                'title': title,
                'form': form,
                'model': self,
                'ticket': ticket,
                'resource': resource,
                'reservations': reservations,
                'show_submission': show_submission,
                'message': message,
            },
        )
        plaintext = html_to_text(content)

        def email_iter() -> Iterator[EmailJsonDict]:
            for recipient_addr in recipients_which_have_registered_for_mail():
                yield request.app.prepare_email(
                    receivers=(recipient_addr,),
                    subject=title,
                    content=content,
                    plaintext=plaintext,
                    category='transactional',
                    attachments=(),
                )

        request.app.send_transactional_email_batch(email_iter())

        request.success(_('The reservations were accepted'))
    else:
        request.warning(_('The reservations have already been accepted'))

    if view_ticket is not None:
        return request.redirect(request.link(view_ticket))

    return request.redirect(request.link(self))


@OrgApp.view(
    model=ReservationTicket,
    name='accept-reservation',
    permission=Private
)
def accept_reservation_from_ticket(
    self: ReservationTicket,
    request: OrgRequest
) -> Response:

    if self.handler.deleted:
        raise exc.HTTPNotFound()

    return accept_reservation(
        self.handler.reservations[0],
        request,
        view_ticket=self
    )


@OrgApp.form(
    model=Reservation,
    name='accept-with-message',
    permission=Private,
    form=InternalTicketChatMessageForm,
    template='form.pt'
)
def accept_reservation_with_message(
    self: Reservation,
    request: OrgRequest,
    form: InternalTicketChatMessageForm,
    layout: TicketChatMessageLayout | None = None,
    view_ticket: ReservationTicket | None = None,
) -> RenderData | Response:

    recipient = self.email
    if not recipient:
        request.alert(_('The submitter email is not available'))
        if view_ticket is not None:
            return request.redirect(request.link(view_ticket))
        return request.redirect(request.link(self))

    if form.submitted(request):
        return accept_reservation(
            self,
            request,
            text=form.text.data,
            notify=form.notify.data,
            view_ticket=view_ticket
        )

    layout = layout or TicketChatMessageLayout(self, request)  # type:ignore
    return {
        'title': _('Accept all reservation with message'),
        'layout': layout,
        'form': form,
        'helptext': _(
            'The following message will be sent to ${address} and it will be '
            'recorded for future reference.', mapping={
                'address': recipient
            }
        )
    }


@OrgApp.form(
    model=ReservationTicket,
    name='accept-reservation-with-message',
    permission=Private,
    form=InternalTicketChatMessageForm,
    template='form.pt'
)
def accept_reservation_with_message_from_ticket(
    self: ReservationTicket,
    request: OrgRequest,
    form: InternalTicketChatMessageForm,
    layout: TicketChatMessageLayout | None = None
) -> RenderData | Response:

    if self.handler.deleted:
        raise exc.HTTPNotFound()

    return accept_reservation_with_message(
        self.handler.reservations[0],
        request,
        form,
        layout or TicketChatMessageLayout(self, request, internal=True),
        view_ticket=self
    )


@OrgApp.view(model=Reservation, name='reject', permission=Private)
def reject_reservation(
    self: Reservation,
    request: OrgRequest,
    text: str | None = None,
    notify: bool = False,
    view_ticket: ReservationTicket | None = None
) -> Response | None:

    token = self.token
    resource = request.app.libres_resources.by_reservation(self)
    assert resource is not None
    reservation_id_str = request.params.get('reservation-id')
    if isinstance(reservation_id_str, str) and reservation_id_str.isdigit():
        reservation_id = int(reservation_id_str)
    else:
        reservation_id = 0

    all_reservations: list[Reservation] = (
        resource.scheduler.reservations_by_token(token)  # type:ignore
        .order_by(Reservation.start).all()
    )

    targeted: Sequence[Reservation]
    targeted = tuple(r for r in all_reservations if r.id == reservation_id)
    targeted = targeted or all_reservations
    excluded = tuple(r for r in all_reservations if r.id not in {
        r.id for r in targeted
    })

    forms = FormCollection(request.session)
    submission = forms.submissions.by_id(token)

    tickets = TicketCollection(request.session)
    ticket = tickets.by_handler_id(token.hex)
    assert ticket is not None

    # if we're accessing the view through a ticket it had better match
    if view_ticket is not None and view_ticket != ticket:
        raise exc.HTTPNotFound()

    clients = KabaClient.from_resource(resource, request.app)

    # if there's a invoiced/captured payment we cannot continue
    payment = ticket.handler.payment
    if payment and payment.state in ('invoiced', 'paid'):
        request.alert(_(
            'The payment associated with this reservation needs '
            'to be refunded before the reservation can be rejected'
        ))

        if not request.headers.get('X-IC-Request'):
            if view_ticket is not None:
                return request.redirect(request.link(view_ticket))
            return request.redirect(request.link(self))

        return None

    savepoint = transaction.savepoint()
    ReservationMessage.create(targeted, ticket, request, 'rejected')

    message = None
    if text:
        assert request.current_username is not None
        message = TicketChatMessage.create(
            ticket, request,
            text=text,
            owner=request.current_username,
            recipient=self.email,
            notify=notify,
            origin='internal')

    send_ticket_mail(
        request=request,
        template='mail_reservation_rejected.pt',
        subject=_('The following reservations were rejected'),
        receivers=(self.email, ),
        ticket=ticket,
        content={
            'model': self,
            'resource': resource,
            'reservations': targeted,
            'message': message
        }
    )

    def recipients_with_mail_for_reservation() -> Iterator[str]:
        # all recipients which want to receive e-mail for rejected reservations
        q = ResourceRecipientCollection(request.session).query()
        q = q.filter(ResourceRecipient.medium == 'email')
        q = q.order_by(None).order_by(ResourceRecipient.address)
        q = q.with_entities(ResourceRecipient.address,
                            ResourceRecipient.content)

        for res in q:
            if (
                self.resource.hex in res.content['resources']
                and res.content.get('rejected_reservations', {})
            ):
                yield res.address

    forms = FormCollection(request.session)
    submission = forms.submissions.by_id(token)
    if submission:
        title = request.translate(
            _(
                '${org} Rejected Reservation',
                mapping={'org': request.app.org.title},
            )
        )

        form = submission.form_obj

        content = render_template(
            'mail_rejected_reservation_notification',
            request,
            {
                'layout': DefaultMailLayout(object(), request),
                'title': title,
                'form': form,
                'model': self,
                'resource': resource,
                'reservations': targeted,
                'show_submission': True,
                'message': message,
            },
        )
        plaintext = html_to_text(content)

        def email_iter() -> Iterator[EmailJsonDict]:
            for recipient_addr in recipients_with_mail_for_reservation():
                yield request.app.prepare_email(
                    receivers=(recipient_addr,),
                    subject=title,
                    content=content,
                    plaintext=plaintext,
                    category='transactional',
                    attachments=(),
                )

        request.app.send_transactional_email_batch(email_iter())

    # create a snapshot of the ticket to keep the useful information
    if len(excluded) == 0:
        # HACK: Set the ticket state to closed so we don't render
        #       any links in the summary
        orginal_state = ticket.state
        ticket.state = 'closed'
        ticket.create_snapshot(request)
        ticket.state = orginal_state

    kaba_visits_to_revoke: list[tuple[str, str]] = []
    for reservation in targeted:
        if payment:
            # remove the link to the payment
            reservation.payment = None
            # flush, just in case, otherwise `remove_reservation` may fail
            request.session.flush()

        if clients and (kaba := (reservation.data or {}).get('kaba')):
            lead_delta = timedelta(
                minutes=ticket.handler.data['key_code_lead_time']
            )
            start = reservation.display_start() - lead_delta
            # we can only revoke future visits
            if start > sedate.utcnow():
                kaba_visits_to_revoke.extend(kaba['visit_ids'].items())
        resource.scheduler.remove_reservation(token, reservation.id)

    if len(excluded) == 0 and submission:
        # pretend we already deleted the submission
        ticket.handler.submission = None  # type: ignore[attr-defined]

    if ticket.handler.refreshing_invoice_is_safe(request):
        ticket.handler.refresh_invoice_items(request)

        if len(excluded) == 0 and submission:
            forms.submissions.delete(submission)

        # since we might roll back previous changes we can't revoke
        # the kaba visits until now, since we didn't hook this change
        # into the transaction system
        failed_to_revoke = False
        for site_id, visit_id in kaba_visits_to_revoke:
            try:
                clients[site_id].revoke_visit(visit_id)
            except (KeyError, KabaApiError) as exc:
                if isinstance(exc, KabaApiError):
                    log.info('Kaba API error', exc_info=True)
                failed_to_revoke = True

        if len(targeted) > 1:
            request.success(_('The reservations were rejected'))
        else:
            request.success(_('The reservation was rejected'))

        if failed_to_revoke:
            request.warning(_(
                'Failed to revoke one or more door codes in dormakaba API'
            ))
    else:
        savepoint.rollback()
        request.alert(_(
            'Your changes would alter the price total '
            'but the payment is no longer open.'
        ))

    # return none on intercooler js requests
    if not request.headers.get('X-IC-Request'):
        if view_ticket is not None:
            return request.redirect(request.link(view_ticket))
        return request.redirect(request.link(self))
    return None


@OrgApp.view(
    model=ReservationTicket,
    name='reject-reservation',
    permission=Private
)
def reject_reservation_from_ticket(
    self: ReservationTicket,
    request: OrgRequest,
) -> Response | None:

    if self.handler.deleted:
        raise exc.HTTPNotFound()

    return reject_reservation(
        self.handler.reservations[0],
        request,
        view_ticket=self
    )


@OrgApp.form(
    model=Reservation,
    name='reject-with-message',
    permission=Private,
    form=InternalTicketChatMessageForm,
    template='form.pt'
)
def reject_reservation_with_message(
    self: Reservation,
    request: OrgRequest,
    form: InternalTicketChatMessageForm,
    layout: TicketChatMessageLayout | None = None,
    view_ticket: ReservationTicket | None = None,
) -> RenderData | Response | None:

    recipient = self.email
    if not recipient:
        request.alert(_('The submitter email is not available'))
        if view_ticket is not None:
            return request.redirect(request.link(view_ticket))
        return request.redirect(request.link(self))

    if form.submitted(request):
        return reject_reservation(
            self, request,
            text=form.text.data,
            notify=form.notify.data,
            view_ticket=view_ticket
        )

    layout = layout or TicketChatMessageLayout(self, request)  # type:ignore
    return {
        'title': _('Reject all reservations with message'),
        'layout': layout,
        'form': form,
        'helptext': _(
            'The following message will be sent to ${address} and it will be '
            'recorded for future reference.', mapping={
                'address': recipient
            }
        )
    }


@OrgApp.form(
    model=ReservationTicket,
    name='reject-reservation-with-message',
    permission=Private,
    form=InternalTicketChatMessageForm,
    template='form.pt'
)
def reject_reservation_with_message_from_ticket(
    self: ReservationTicket,
    request: OrgRequest,
    form: InternalTicketChatMessageForm,
    layout: TicketChatMessageLayout | None = None
) -> RenderData | Response | None:

    if self.handler.deleted:
        raise exc.HTTPNotFound()

    return reject_reservation_with_message(
        self.handler.reservations[0],
        request,
        form,
        layout or TicketChatMessageLayout(self, request, internal=True)
    )


@OrgApp.view(
    model=ReservationTicket,
    name='send-reservation-summary',
    permission=Private
)
def send_reservation_summary(
    self: ReservationTicket,
    request: OrgRequest
) -> Response | None:

    if self.handler.deleted or not self.handler.reservations:
        raise exc.HTTPNotFound()

    recipient = self.handler.email
    if recipient:
        assert request.current_username
        TicketChatMessage.create(
            self,
            request,
            text=request.translate(_('Reservation summary')),
            owner=request.current_username,
            recipient=recipient,
            notify=False,
            origin='internal'
        )
        send_ticket_mail(
            request=request,
            template='mail_reservation_summary.pt',
            subject=_('Reservation summary'),
            receivers=(recipient, ),
            ticket=self,
            force=True,
            content={
                'model': self,
                'resource': self.handler.resource,
                'reservations': self.handler.reservations,
                'code': self.handler.data.get('key_code'),
                'changes': self.handler.get_changes(request),
                'my_reservations_url': get_my_reservations_url(
                    request, recipient
                ),
            }
        )
        request.success(_(
            'Successfully sent ${count} emails',
            mapping={'count': 1}
        ))
    else:
        request.alert(_('The submitter email is not available'))

    if request.headers.get('X-IC-Request'):
        return None
    return request.redirect(request.link(self))


@OrgApp.form(
    model=Reservation,
    name='add',
    permission=Private,
    form=AddReservationForm,
    template='form.pt'
)
def add_reservation(
    self: Reservation,
    request: OrgRequest,
    form: AddReservationForm,
    view_ticket: ReservationTicket | None = None,
    layout: ReservationLayout | TicketLayout | None = None
) -> RenderData | Response:

    token = self.token
    resource = request.app.libres_resources.by_reservation(self)
    assert resource is not None

    tickets = TicketCollection(request.session)
    ticket = tickets.by_handler_id(token.hex)
    assert ticket is not None

    # if we're accessing this view through the ticket it
    # had better match the ticket we retrieved
    if view_ticket is not None and view_ticket != ticket:
        raise exc.HTTPNotFound()

    def show_form() -> RenderData:
        return {
            'title': _('Add reservation'),
            'layout': layout or ReservationLayout(resource, request),
            'form': form,
        }

    form.apply_resource(resource)
    if not form.submitted(request):
        if self.data and self.data.get('accepted'):
            request.warning(_(
                'Since the other reservations in this ticket '
                'have already been accepted, this reservation '
                'will also be immediately accepted. However '
                'we will not send a new reservation confirmation.'
            ))
        return show_form()

    assert form.date.data is not None
    assert form.quota.data is not None
    dt = sedate.replace_timezone(
        sedate.as_datetime(form.date.data),
        resource.timezone,
    )
    if 'whole_day' in form and form.whole_day.data == 'no':
        assert form.start_time.data is not None
        assert form.end_time.data is not None
        start_time = form.start_time.data
        end_time = form.end_time.data
    else:
        start_time = time(0, 0)
        end_time = time(23, 59)

    try:
        start, end = sedate.get_date_range(
            dt,
            start_time,
            end_time,
            raise_non_existent=True
        )
    except pytz.NonExistentTimeError:
        request.alert(_(
            'The selected time does not exist on this date due to '
            'the switch from standard time to daylight saving time.'
        ))
        return show_form()

    # if the matched allocation isn't partly available expand it to the
    # whole allocation for a better user experience, but don't ever shrink
    # it, since that's most certainly not what they want to have happen.
    for allocation in resource.scheduler.allocations_in_range(start, end):
        if not allocation.overlaps(start, end):
            continue

        if allocation.partly_available:
            break

        if allocation.contains(start, end):
            start, end = allocation.start, allocation.end
        else:
            request.alert(_(
                'The targeted availability is not partially reservable '
                'and does not fully cover the selected time range.'
            ))
            return show_form()

    savepoint = transaction.savepoint()
    try:
        temp_token = resource.scheduler.reserve(
            self.email,
            (start, end),
            quota=form.quota.data
        )
    except LibresError as e:
        request.alert(utils.get_libres_error(e, request))
        return show_form()

    reservation: Reservation = (
        resource.scheduler.reservations_by_token(temp_token).one()  # type:ignore
    )
    # change the temporary token back to the shared reservation token
    reservation.token = token
    try:
        resource.scheduler._approve_reservation_record(reservation)
    except LibresError as e:
        request.session.flush()
        savepoint.rollback()
        request.alert(utils.get_libres_error(e, request))
        return show_form()

    request.session.flush()
    if ticket.handler.refreshing_invoice_is_safe(request):
        ticket.handler.refresh_invoice_items(request)
    else:
        request.session.flush()
        savepoint.rollback()
        request.alert(_(
            'Your changes would alter the price total '
            'but the payment is no longer open.'
        ))
        return show_form()

    if self.data and self.data.get('accepted'):
        # we need to accept the new reservation
        data = reservation.data
        if data is None:
            data = reservation.data = {}

        data['accepted'] = True

        clients = KabaClient.from_resource(resource, request.app)
        if clients and (lead := timedelta(
            minutes=ticket.handler.data['key_code_lead_time']
        )) is not None and (
            (start := reservation.display_start() - lead) > sedate.utcnow()
        ):
            # add visit
            components: dict[str, list[str]] = {}
            for site_id, component in resource.kaba_components:  # type: ignore[attr-defined]
                components.setdefault(site_id, []).append(component)

            code = ticket.handler.data['key_code']
            lag = timedelta(minutes=ticket.handler.data['key_code_lag_time'])
            end = reservation.display_end() + lag
            visit_ids = {}
            for site_id, group in components.items():
                try:
                    visit_ids[site_id] = clients[site_id].create_visit(
                        code=code,
                        name=ticket.number,
                        message='Managed through OneGov Cloud',
                        start=start,
                        end=end,
                        components=group,
                    )
                except (KeyError, KabaApiError) as e:
                    if isinstance(e, KabaApiError):
                        log.info('Kaba API error', exc_info=True)

                    # roll back previous changes
                    request.session.flush()
                    savepoint.rollback()
                    request.alert(_(
                        'Failed to create visits using the dormakaba API '
                        'for site ID ${site_id} please make sure your '
                        'credentials are still valid.',
                        mapping={'site_id': site_id}
                    ))
                    return show_form()

                data['kaba'] = {
                    'code': code,
                    'visit_ids': visit_ids,
                }

    ReservationMessage.create(
        [reservation],
        ticket,
        request,
        'added'
    )

    request.success(_('Added a new reservation'))
    if view_ticket is not None:
        return request.redirect(request.link(view_ticket))

    return request.redirect(request.link(self))


@OrgApp.form(
    model=ReservationTicket,
    name='add-reservation',
    permission=Private,
    form=AddReservationForm,
    template='form.pt'
)
def add_reservation_from_ticket(
    self: ReservationTicket,
    request: OrgRequest,
    form: AddReservationForm,
    layout: TicketLayout | None = None
) -> RenderData | Response | None:

    if self.handler.deleted:
        raise exc.HTTPNotFound()

    layout = layout or TicketLayout(self, request)
    layout.breadcrumbs[-1].attrs['href'] = request.link(self)
    layout.breadcrumbs.append(
        Link(_('Add reservation'), '#')
    )

    return add_reservation(
        self.handler.reservations[0],
        request,
        form,
        self,
        layout
    )


@OrgApp.form(
    model=Reservation,
    name='adjust',
    permission=Private,
    form=ReservationAdjustmentForm,
    template='form.pt'
)
def adjust_reservation(
    self: Reservation,
    request: OrgRequest,
    form: ReservationAdjustmentForm,
    view_ticket: ReservationTicket | None = None,
    layout: ReservationLayout | TicketLayout | None = None
) -> RenderData | Response:

    token = self.token
    resource = request.app.libres_resources.by_reservation(self)
    assert resource is not None
    reservation_id_str = request.params.get('reservation-id')
    if isinstance(reservation_id_str, str) and reservation_id_str.isdigit():
        reservation_id = int(reservation_id_str)
    else:
        raise exc.HTTPNotFound()

    reservation: Reservation | None = (
        resource.scheduler.reservations_by_token(token)  # type:ignore
        .filter(Reservation.id == reservation_id)
        .one_or_none()
    )
    if reservation is None or not reservation.is_adjustable:
        if request.headers.get('X-IC-Request'):
            error = request.translate(_('Reservation not adjustable'))
            ic_data = {'message': error, 'success': False}

            @request.after
            def trigger(response: Response) -> None:
                response.headers.add('X-IC-Trigger', 'oc-reservation-error')
                response.headers.add(
                    'X-IC-Trigger-Data',
                    json.dumps(ic_data, ensure_ascii=True)
                )
            return Response(json=ic_data)
        raise exc.HTTPNotFound()

    tickets = TicketCollection(request.session)
    ticket = tickets.by_handler_id(token.hex)
    assert ticket is not None

    # if we're accessing this view through the ticket it
    # had better match the ticket we retrieved
    if view_ticket is not None and view_ticket != ticket:
        raise exc.HTTPNotFound()

    def show_form() -> RenderData:
        if not request.POST:
            form.start_time.data = reservation.display_start().time()
            form.end_time.data = reservation.display_end().time()
        return {
            'title': _('Adjust reservation'),
            'layout': layout or ReservationLayout(resource, request),
            'form': form,
        }

    def show_error(error: str) -> Response | RenderData:
        if intercooler:
            if type(error) is not str:
                error = request.translate(error)
            ic_data = {'message': error, 'success': False}

            @request.after
            def trigger(response: Response) -> None:
                response.headers.add('X-IC-Trigger', 'oc-reservation-error')
                response.headers.add(
                    'X-IC-Trigger-Data',
                    json.dumps(ic_data, ensure_ascii=True)
                )
            return Response(json=ic_data)
        request.alert(error)
        return show_form()

    if intercooler := bool(request.headers.get('X-IC-Request')):
        request.assert_valid_csrf_token()
        new_start = isodate.parse_datetime(request.GET['start'])
        new_end = isodate.parse_datetime(request.GET['end'])
    elif not form.submitted(request):
        return show_form()
    else:
        start_time = form.start_time.data
        end_time = form.end_time.data
        assert start_time is not None and end_time is not None
        try:
            new_start, new_end = sedate.get_date_range(
                reservation.display_start(),
                start_time,
                end_time,
                raise_non_existent=True
            )
        except pytz.NonExistentTimeError:
            request.alert(_(
                'The selected time does not exist on this date due to '
                'the switch from standard time to daylight saving time.'
            ))
            return show_form()

    savepoint = transaction.savepoint()
    try:
        payment = reservation.payment
        # we need to temporarily un-link the payment, since change_reservation
        # deletes the old reservation, which will fail, if there is a payment
        reservation.payment = None
        request.session.flush()
        new_reservation = resource.scheduler.change_reservation(
            token,
            reservation.id,
            new_start,
            new_end,
        )
        if payment is None:
            pass
        elif new_reservation is not None:
            new_reservation.payment = payment  # type: ignore[attr-defined]
            if ticket.handler.refreshing_invoice_is_safe(request):
                ticket.handler.refresh_invoice_items(request)
            else:
                request.session.flush()
                savepoint.rollback()
                return show_error(_(
                    'Your changes would alter the price total '
                    'but the payment is no longer open.'
                ))
        else:
            # restore the payment link
            reservation.payment = payment
    except LibresError as e:
        # rollback previous changes
        request.session.flush()
        savepoint.rollback()
        return show_error(utils.get_libres_error(e, request))

    if new_reservation is not None:
        failed_to_revoke = False
        clients = KabaClient.from_resource(resource, request.app)
        data = reservation.data
        if data is None:
            data = reservation.data = {}
        if clients and (kaba := data.get('kaba')):
            # adjust visit
            components: dict[str, list[str]] = {}
            for site_id, component in resource.kaba_components:  # type: ignore[attr-defined]
                components.setdefault(site_id, []).append(component)

            lead_delta = timedelta(
                minutes=ticket.handler.data['key_code_lead_time']
            )
            lag_delta = timedelta(
                minutes=ticket.handler.data['key_code_lag_time']
            )
            old_start = reservation.display_start() - lead_delta
            start = new_reservation.display_start() - lead_delta
            end = new_reservation.display_end() + lag_delta
            old_visit_ids = kaba.get('visit_ids')
            now = sedate.utcnow()
            visit_ids = {}
            for site_id, group in components.items():
                try:
                    code = kaba['code']
                    # NOTE: We can only revoke existing future visits
                    old_visit_id = old_visit_ids.get(site_id)
                    if old_visit_id and old_start > now:
                        try:
                            clients[site_id].revoke_visit(old_visit_id)
                        except (KeyError, KabaApiError) as e:
                            if isinstance(e, KabaApiError):
                                log.info('Kaba API error', exc_info=True)
                            failed_to_revoke = True
                    # NOTE: We can only create future visits
                    if start > now:
                        visit_ids[site_id] = clients[site_id].create_visit(
                            code=code,
                            name=ticket.number,
                            message='Managed through OneGov Cloud',
                            start=start,
                            end=end,
                            components=group,
                        )
                except (KeyError, KabaApiError) as e:
                    if isinstance(e, KabaApiError):
                        log.info('Kaba API error', exc_info=True)

                    # roll back previous changes
                    request.session.flush()
                    savepoint.rollback()
                    return show_error(_(
                        'Failed to create visits using the dormakaba API '
                        'for site ID ${site_id} please make sure your '
                        'credentials are still valid.',
                        mapping={'site_id': site_id}
                    ))

                data['kaba'] = {
                    'code': code,
                    'visit_ids': visit_ids,
                }

        ReservationAdjustedMessage.create(
            reservation,
            new_reservation,
            ticket,
            request,
        )
        if not intercooler:
            if failed_to_revoke:
                request.warning(_(
                    'Failed to revoke one or more door codes in dormakaba API'
                ))
            request.success(_('The reservation was adjusted'))
    elif not intercooler:
        request.warning(_('The reservation was left unchanged'))

    if intercooler:
        @request.after
        def trigger_calendar_update(response: Response) -> None:
            response.headers.add('X-IC-Trigger', 'oc-reservations-changed')

        return Response(json={'success': True})

    if view_ticket is not None:
        return request.redirect(request.link(view_ticket))

    return request.redirect(request.link(self))


@OrgApp.form(
    model=ReservationTicket,
    name='adjust-reservation',
    permission=Private,
    form=ReservationAdjustmentForm,
    template='form.pt'
)
def adjust_reservation_from_ticket(
    self: ReservationTicket,
    request: OrgRequest,
    form: ReservationAdjustmentForm,
    layout: TicketLayout | None = None
) -> RenderData | Response | None:

    if self.handler.deleted:
        raise exc.HTTPNotFound()

    layout = layout or TicketLayout(self, request)
    layout.breadcrumbs[-1].attrs['href'] = request.link(self)
    layout.breadcrumbs.append(
        Link(_('Adjust reservation'), '#')
    )

    return adjust_reservation(
        self.handler.reservations[0],
        request,
        form,
        self,
        layout
    )


@OrgApp.form(
    model=Reservation,
    name='edit-kaba',
    permission=Private,
    form=KabaEditForm,
    template='form.pt'
)
def edit_kaba(
    self: Reservation,
    request: OrgRequest,
    form: KabaEditForm,
    view_ticket: ReservationTicket | None = None,
    layout: ReservationLayout | TicketLayout | None = None
) -> RenderData | Response:

    token = self.token
    resource = request.app.libres_resources.by_reservation(self)
    assert resource is not None

    tickets = TicketCollection(request.session)
    ticket = tickets.by_handler_id(token.hex)
    assert isinstance(ticket, ReservationTicket)

    # if we're accessing this view through the ticket it
    # had better match the ticket we retrieved
    if view_ticket is not None and view_ticket != ticket:
        raise exc.HTTPNotFound()

    # we only can make kaba changes if we have a connection
    clients = KabaClient.from_resource(resource, request.app)
    if not clients:
        raise exc.HTTPNotFound()

    components: dict[str, list[str]] = {}
    for site_id, component in resource.kaba_components:  # type: ignore[attr-defined]
        components.setdefault(site_id, []).append(component)

    old_lead_delta = timedelta(
        minutes=ticket.handler.data.get('key_code_lead_time', 30)
    )
    now = sedate.utcnow()
    future_reservations = [
        reservation
        for reservation in ticket.handler.reservations
        if reservation.display_start() - old_lead_delta > now
    ]

    # if we don't have any future or ongoing reservations then
    # changes will no longer make any sense
    if not future_reservations:
        request.alert(_('There are no future reservations'))

        if view_ticket is not None:
            return request.redirect(request.link(view_ticket))

        return request.redirect(request.link(self))

    field_names = (
        'key_code',
        'key_code_lead_time',
        'key_code_lag_time'
    )

    def show_form() -> RenderData:
        if not request.POST:
            for name in field_names:
                form[name].data = ticket.handler_data.get(name)
        return {
            'title': _('Edit key code'),
            'layout': layout or ReservationLayout(resource, request),
            'form': form,
        }

    if not form.submitted(request):
        return show_form()

    failed_to_revoke = False
    savepoint = transaction.savepoint()
    if form.data != {
        name: ticket.handler_data.get(name)
        for name in field_names
    }:

        old_lead_delta = timedelta(
            minutes=ticket.handler.data['key_code_lead_time']
        )
        ticket.handler.data.update(form.data)
        ticket.handler.refresh()

        # handle reservation changes
        for reservation in future_reservations:
            data = reservation.data
            if data is None:
                data = reservation.data = {}
            # if it hasn't been accepted yet, we don't need to
            # talk to the API
            if not data.get('accepted'):
                continue

            code = ticket.handler.data['key_code']
            lead_delta = timedelta(
                minutes=ticket.handler.data['key_code_lead_time']
            )
            lag_delta = timedelta(
                minutes=ticket.handler.data['key_code_lag_time']
            )
            old_start = reservation.display_start() - old_lead_delta
            start = reservation.display_start() - lead_delta
            end = reservation.display_end() + lag_delta
            kaba = data.get('kaba') or {}
            old_visit_ids = kaba.get('visit_ids', {})
            visit_ids = {}
            for site_id, group in components.items():
                try:
                    # if there is an old visit, revoke it
                    old_visit_id = old_visit_ids.get(site_id)
                    if old_visit_id and old_start > now:
                        try:
                            clients[site_id].revoke_visit(old_visit_id)
                        except (KeyError, KabaApiError) as e:
                            if isinstance(e, KabaApiError):
                                log.info('Kaba API error', exc_info=True)
                            failed_to_revoke = True

                    if start > now:
                        visit_ids[site_id] = clients[site_id].create_visit(
                            code=code,
                            name=ticket.number,
                            message='Managed through OneGov Cloud',
                            start=start,
                            end=end,
                            components=group,
                        )
                except (KeyError, KabaApiError) as e:
                    if isinstance(e, KabaApiError):
                        log.info('Kaba API error', exc_info=True)

                    # roll back previous changes
                    savepoint.rollback()
                    request.alert(_(
                        'Failed to create visits using the dormakaba API '
                        'for site ID ${site_id} please make sure your '
                        'credentials are still valid.',
                        mapping={'site_id': site_id}
                    ))
                    return show_form()

                data['kaba'] = {
                    'code': code,
                    'visit_ids': visit_ids,
                }

    if failed_to_revoke:
        request.warning(_(
            'Failed to revoke one or more door codes in dormakaba API'
        ))

    request.success(_('Your changes were saved'))

    if view_ticket is not None:
        return request.redirect(request.link(view_ticket))

    return request.redirect(request.link(self))


@OrgApp.form(
    model=ReservationTicket,
    name='edit-kaba',
    permission=Private,
    form=KabaEditForm,
    template='form.pt'
)
def edit_kaba_from_ticket(
    self: ReservationTicket,
    request: OrgRequest,
    form: KabaEditForm,
    layout: TicketLayout | None = None
) -> RenderData | Response | None:

    if self.handler.deleted:
        raise exc.HTTPNotFound()

    layout = layout or TicketLayout(self, request)
    layout.breadcrumbs[-1].attrs['href'] = request.link(self)
    layout.breadcrumbs.append(
        Link(_('Edit key code'), '#')
    )

    return edit_kaba(
        self.handler.reservations[0],
        request,
        form,
        self,
        layout
    )
