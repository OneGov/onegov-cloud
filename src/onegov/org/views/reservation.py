import morepath
import pytz
import sedate
import transaction

from datetime import time, timedelta
from dill import pickles
from libres.modules.errors import LibresError
from onegov.core.custom import json
from onegov.core.html import html_to_text
from onegov.core.security import Public, Private
from onegov.core.templates import render_template
from onegov.form import FormCollection, merge_forms, as_internal_id
from onegov.org import _, OrgApp
from onegov.org import utils
from onegov.org.cli import close_ticket
from onegov.org.elements import Link
from onegov.org.forms import ReservationForm, InternalTicketChatMessageForm
from onegov.org.layout import ReservationLayout, TicketChatMessageLayout
from onegov.org.layout import DefaultMailLayout
from onegov.org.mail import send_ticket_mail
from onegov.org.models import (
    TicketMessage, TicketChatMessage, ReservationMessage,
    ResourceRecipient, ResourceRecipientCollection)
from onegov.org.models.resource import FindYourSpotCollection
from onegov.reservation import Allocation, Reservation, Resource
from onegov.ticket import TicketCollection
from purl import URL
from sqlalchemy.orm.attributes import flag_modified
from webob import exc


def assert_anonymous_access_only_temporary(resource, reservation, request):
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

    if reservation.session_id != resource.bound_session_id(request):
        raise exc.HTTPForbidden()


def assert_access_only_if_there_are_reservations(reservations):
    """ Raises an exception if no reservations are available. """
    if not reservations:
        raise exc.HTTPForbidden()


def respond_with_success(request):
    @request.after
    def trigger_calendar_update(response):
        response.headers.add('X-IC-Trigger', 'rc-reservations-changed')

    return {
        'success': True
    }


def respond_with_error(request, error):
    message = {
        'message': error,
        'success': False
    }

    @request.after
    def trigger(response):
        response.headers.add('X-IC-Trigger', 'rc-reservation-error')
        response.headers.add('X-IC-Trigger-Data', json.dumps(message))

    return message


@OrgApp.json(model=Allocation, name='reserve', request_method='POST',
             permission=Public)
def reserve_allocation(self, request):
    """ Adds a single reservation to the list of reservations bound to the
    current browser session.

    Does not actually reserve anything, just keeps a list of things to
    reserve later. Though it will still check if the reservation is
    feasible.

    """

    # the reservation is defined through query parameters
    start = request.params.get('start') or '{:%H:%M}'.format(self.start)
    end = request.params.get('end') or '{:%H:%M}'.format(self.end)
    quota = int(request.params.get('quota', 1))
    whole_day = request.params.get('whole_day') == '1'

    if self.partly_available:
        if self.whole_day and whole_day:
            start = time(0, 0)
            end = time(23, 59)
        else:
            start = sedate.parse_time(start)
            end = sedate.parse_time(end)

        try:
            start, end = sedate.get_date_range(
                self.display_start(),
                start,
                end,
                raise_non_existent=True
            )
        except pytz.NonExistentTimeError:
            err = request.translate(_(
                "The selected time does not exist on this date due to "
                "the switch from standard time to daylight saving time."
            ))
            return respond_with_error(request, err)
    else:
        start, end = self.start, self.end

    resource = request.app.libres_resources.by_allocation(self)

    # if there's a deadline, make sure to observe it for anonymous users...
    if not request.is_manager and resource.is_past_deadline(start):
        n, unit = resource.deadline

        if unit == 'h' and n == 1:
            unit = request.translate(_("hour"))

        elif unit == 'h' and n > 1:
            unit = request.translate(_("hours"))

        elif unit == 'd' and n == 1:
            unit = request.translate(_("day"))

        elif unit == 'd' and n > 1:
            unit = request.translate(_("days"))

        else:
            raise NotImplementedError()

        err = request.translate(
            _("Reservations must be made ${n} ${unit} in advance", mapping={
                'n': n,
                'unit': unit
            })
        )

        return respond_with_error(request, err)

    # if the allocation is in the past, disable it for anonymous users...
    if not request.is_manager and end < sedate.utcnow():
        err = request.translate(_("This date lies in the past"))

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
def delete_reservation(self, request):

    # anonymous users do not get a csrf token (it's bound to the identity)
    # therefore we can't check for it -> this is not a problem since
    # anonymous users do not really have much to lose here
    if request.is_logged_in:
        request.assert_valid_csrf_token()

    resource = request.app.libres_resources.by_reservation(self)

    # this view is public, but only for a limited time
    assert_anonymous_access_only_temporary(resource, self, request)
    tickets = TicketCollection(request.session)
    ticket = tickets.by_handler_id(self.token.hex)

    try:
        if ticket:
            ticket.create_snapshot(request)
        resource.scheduler.remove_reservation(self.token, self.id)
    except LibresError as e:
        message = {
            'message': utils.get_libres_error(e, request),
            'success': False
        }

        @request.after
        def trigger_calendar_update(response):
            response.headers.add('X-IC-Trigger', 'rc-reservation-error')
            response.headers.add('X-IC-Trigger-Data', json.dumps(message))

        return message
    else:

        @request.after
        def trigger_calendar_update(response):
            response.headers.add('X-IC-Trigger', 'rc-reservations-changed')

        return {
            'success': True
        }


def get_reservation_form_class(resource, request):
    if resource.definition:
        return merge_forms(ReservationForm, resource.form_class)
    else:
        return ReservationForm


@OrgApp.form(model=Resource, name='form', template='reservation_form.pt',
             permission=Public, form=get_reservation_form_class)
def handle_reservation_form(self, request, form, layout=None):
    """ Asks the user for the form data required to complete one or many
    reservations on a resource.

    """
    reservations_query = self.bound_reservations(request)
    reservations = tuple(reservations_query)

    assert_access_only_if_there_are_reservations(reservations)

    # all reservations share a single token
    token = reservations[0].token

    # the submission shares the reservation token
    forms = FormCollection(request.session)
    submission = forms.submissions.by_id(token)

    # update the data if the form is submitted (even if invalid)
    if request.POST:

        # update the e-mail data
        for reservation in reservations:
            reservation.email = form.email.data

        # while we re at it, remove all expired sessions
        self.remove_expired_reservation_sessions()

        # add the submission if it doesn't yet exist
        if self.definition and not submission:
            submission = forms.submissions.add_external(
                form=self.form_class(),
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
    # set defaults based on remembered submissions from session
    else:
        remembered = request.browser_session.get('remembered_submissions', {})
        for field_name in form.data:
            if field_name not in remembered:
                continue
            getattr(form, field_name).default = remembered[field_name]

    # enforce the zip-code block if configured
    if request.POST:
        blocked = blocked_by_zipcode(request, self, form, reservations)
    else:
        blocked = ()

    # go to the next step if the submitted data is valid
    if form.submitted(request) and not blocked:
        # also remember submitted form data
        remembered = request.browser_session.get('remembered_submissions', {})
        remembered.update(form.data)
        # but don't remember submitted csrf_token
        if 'csrf_token' in remembered:
            del remembered['csrf_token']
        # only remember the data if we can pickle the data
        if pickles(remembered, recurse=True, safe=True):
            request.browser_session.remembered_submissions = remembered
        return morepath.redirect(request.link(self, 'confirmation'))
    else:
        data = {}

        # the email is the same for all reservations
        # Todo: This entry created remained after a reservation
        if reservations[0].email != '0xdeadbeef@example.org':
            data['email'] = reservations[0].email

        if submission:
            data.update(submission.data)

        form.process(data=data)

    if not form.errors and blocked:
        request.alert(_(
            "The form contains errors. Please check the marked fields."
        ))

    layout = layout or layout or ReservationLayout(self, request)
    layout.breadcrumbs.append(Link(_("Reserve"), '#'))

    title = _("New dates for ${title}", mapping={
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
        'button_text': _("Continue")
    }


def get_next_resource_context(reservations):
    # pick the resource with the most reservations, but if there
    # is a tie, pick the one with the earliest reservation
    selected = None
    for item in reservations.items():
        if selected is None:
            selected = item
            continue

        max_len = len(selected[1])
        cur_len = len(item[1])
        if cur_len > max_len:
            selected = item
        elif cur_len == max_len:
            if selected[1][0].start > item[1][0].start:
                selected = item
    return selected[0]


@OrgApp.view(model=FindYourSpotCollection, name='form', permission=Public)
def handle_find_your_spot_reservation_form(self, request):
    """ This is a convenience view that redirects to the appropriate
    resource specific reservation form.

    """
    reservations = {
        resource: bound
        for resource in request.exclude_invisible(self.query())
        if (bound := list(resource.bound_reservations(request)))
    }

    assert_access_only_if_there_are_reservations(reservations)

    resource = get_next_resource_context(reservations)
    return morepath.redirect(request.link(resource, 'form'))


def blocked_by_zipcode(request, resource, form, reservations):
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
        dt = reservation.display_start().date()

        if resource.is_zip_blocked(dt):
            blocked[reservation.id] = dt - timedelta(days=days)

    return blocked


@OrgApp.html(model=Resource, name='confirmation', permission=Public,
             template='reservation_confirmation.pt')
def confirm_reservation(self, request, layout=None):
    reservations = self.bound_reservations(request).all()
    assert_access_only_if_there_are_reservations(reservations)

    token = reservations[0].token.hex

    forms = FormCollection(request.session)
    submission = forms.submissions.by_id(token)

    if submission:
        form = request.get_form(submission.form_class, data=submission.data)
    else:
        form = None

    layout = layout or ReservationLayout(self, request)
    layout.breadcrumbs.append(Link(_("Confirm"), '#'))

    failed_reservations = {
        int(failed)
        for failed in request.params.get('failed_reservations', '').split(',')
        if failed
    }

    price = request.app.adjust_price(self.price_of_reservation(
        token, submission and submission.form_obj.total()))

    return {
        'title': _("Confirm your reservation"),
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
        'checkout_button': price and request.app.checkout_button(
            button_label=request.translate(_("Pay Online and Complete")),
            title=self.title,
            price=price,
            email=reservations[0].email,
            locale=request.locale
        )
    }


@OrgApp.html(model=Resource, name='finish', permission=Public,
             template='layout.pt', request_method='POST')
def finalize_reservation(self, request):
    reservations = self.bound_reservations(request).all()
    assert_access_only_if_there_are_reservations(reservations)

    session_id = self.bound_session_id(request)
    token = reservations[0].token.hex

    forms = FormCollection(request.session)
    submission = forms.submissions.by_id(token)

    try:
        provider = request.app.default_payment_provider
        payment_token = request.params.get('payment_token')

        price = request.app.adjust_price(self.price_of_reservation(
            token, submission and submission.form_obj.total()))

        payment = self.process_payment(price, provider, payment_token)

        if not payment:
            request.alert(_("Your payment could not be processed"))
            return morepath.redirect(request.link(self))

        elif payment is not True:
            for reservation in reservations:
                reservation.payment = payment

        self.scheduler.queries.confirm_reservations_for_session(session_id)
        self.scheduler.approve_reservations(token)

    except LibresError as e:
        transaction.abort()
        utils.show_libres_error(e, request)

        url = URL(request.link(self, name='confirmation'))
        url = url.query_param('failed_reservations', e.reservation.id)

        return morepath.redirect(url.as_string())
    else:
        if submission:
            forms.submissions.complete_submission(submission)
        with forms.session.no_autoflush:
            ticket = TicketCollection(request.session).open_ticket(
                handler_code='RSV', handler_id=token
            )
            TicketMessage.create(ticket, request, 'opened')

        show_submission = request.params.get('send_by_email') == 'yes'

        if submission and show_submission:
            form = submission.form_obj
        else:
            form = None

        send_ticket_mail(
            request=request,
            template='mail_ticket_opened.pt',
            subject=_("Your request has been registered"),
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
        if request.email_for_new_tickets:
            send_ticket_mail(
                request=request,
                template='mail_ticket_opened_info.pt',
                subject=_("New ticket"),
                ticket=ticket,
                receivers=(request.email_for_new_tickets, ),
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
            }
        )

        if request.auto_accept(ticket):
            try:
                ticket.accept_ticket(request.auto_accept_user)
                request.view(reservations[0], name='accept')
            except Exception:
                request.warning(_("Your request could not be "
                                  "accepted automatically!"))
            else:
                close_ticket(ticket, request.auto_accept_user, request)

        collection = FindYourSpotCollection(
            request.app.libres_context, self.group)
        pending = {
            resource: bound
            for resource in request.exclude_invisible(collection.query())
            if (bound := list(resource.bound_reservations(request)))
        }

        # by default we will redirect to the created ticket
        message = _("Thank you for your reservation!")
        url = request.link(ticket, 'status')

        # retrieve remembered tickets
        tickets = request.browser_session.get('reservation_tickets', {})

        # continue to the next resource in this group with pending reservations
        if pending:
            resource = get_next_resource_context(pending)

            # remember ticket so we can show them all at the end
            tickets.setdefault(self.group, []).append(str(ticket.id))
            request.browser_session.reservation_tickets = tickets

            message = _(
                "Your reservation for ${room} has been submitted. "
                "Please continue with your reservation for ${next_room}.",
                mapping={'room': self.title, 'next_room': resource.title})
            url = request.link(resource, 'form')

        # if we remembered tickets for this group that means
        # we never showed them so now we need to show them all
        elif self.group in tickets:
            tickets[self.group].append(ticket.id)
            request.browser_session.reservation_tickets = tickets
            url = request.link(collection, 'tickets')

        request.success(message)

        return morepath.redirect(url)


@OrgApp.view(model=Reservation, name='accept', permission=Private)
def accept_reservation(self, request, text=None, notify=False):
    if not self.data or not self.data.get('accepted'):
        resource = request.app.libres_resources.by_reservation(self)
        reservations = resource.scheduler.reservations_by_token(self.token)
        reservations = reservations.order_by(Reservation.start)

        token = self.token.hex
        tickets = TicketCollection(request.session)
        ticket = tickets.by_handler_id(token)

        forms = FormCollection(request.session)
        submission = forms.submissions.by_id(token)

        if submission:
            form = submission.form_obj
        else:
            form = None

        # Include all the forms details to be able to print it out
        show_submission = True

        for reservation in reservations:
            reservation.data = reservation.data or {}
            reservation.data['accepted'] = True

            # libres does not automatically detect changes yet
            flag_modified(reservation, 'data')

        ReservationMessage.create(reservations, ticket, request, 'accepted')

        message = None
        if text:
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
            subject=_("Your reservations were accepted"),
            receivers=(self.email,),
            ticket=ticket,
            content={
                'model': self,
                'resource': resource,
                'reservations': reservations,
                'show_submission': show_submission,
                'form': form,
                'message': message,
            },
        )

        def recipients_which_have_registered_for_mail():
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
                "${org} New Reservation(s)",
                mapping={'org': request.app.org.title},
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
                'resource': resource,
                'reservations': reservations,
                'show_submission': show_submission,
                'message': message,
            },
        )
        plaintext = html_to_text(content)

        def email_iter():
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

        request.success(_("The reservations were accepted"))
    else:
        request.warning(_("The reservations have already been accepted"))

    return request.redirect(request.link(self))


@OrgApp.form(model=Reservation, name='accept-with-message', permission=Private,
             form=InternalTicketChatMessageForm, template='form.pt')
def accept_reservation_with_message(self, request, form, layout=None):
    recipient = self.email
    if not recipient:
        request.alert(_("The submitter email is not available"))
        return request.redirect(request.link(self))

    if form.submitted(request):
        return accept_reservation(
            self, request, text=form.text.data, notify=form.notify.data)

    return {
        'title': _("Accept all reservation with message"),
        'layout': layout or TicketChatMessageLayout(self, request),
        'form': form,
        'helptext': _(
            "The following message will be sent to ${address} and it will be "
            "recorded for future reference.", mapping={
                'address': recipient
            }
        )
    }


@OrgApp.view(model=Reservation, name='reject', permission=Private)
def reject_reservation(self, request, text=None, notify=False):
    resource = request.app.libres_resources.by_reservation(self)
    token = self.token.hex
    reservation_id = int(request.params.get('reservation-id', '0')) or None

    all_reservations = resource.scheduler.reservations_by_token(token)
    all_reservations = all_reservations.order_by(Reservation.start).all()

    targeted = tuple(r for r in all_reservations if r.id == reservation_id)
    targeted = targeted or all_reservations
    excluded = tuple(r for r in all_reservations if r.id not in {
        r.id for r in targeted
    })

    forms = FormCollection(request.session)
    submission = forms.submissions.by_id(token)

    tickets = TicketCollection(request.session)
    ticket = tickets.by_handler_id(token)

    # if there's a acptured payment we cannot continue
    payment = ticket.handler.payment
    if payment and payment.state == 'paid':
        request.alert(_(
            "The payment associated with this reservation needs "
            "to be refunded before the reservation can be rejected"
        ))

        if not request.headers.get('X-IC-Request'):
            return request.redirect(request.link(self))

        return None

    # we need to delete the payment at the same time
    if payment:
        request.session.delete(payment)

    ReservationMessage.create(targeted, ticket, request, 'rejected')

    message = None
    if text:
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
        subject=_("The following reservations were rejected"),
        receivers=(self.email, ),
        ticket=ticket,
        content={
            'model': self,
            'resource': resource,
            'reservations': targeted,
            'message': message
        }
    )

    def recipients_with_mail_for_reservation():
        # all recipients which want to receive e-mail for rejected reservations
        q = ResourceRecipientCollection(request.session).query()
        q = q.filter(ResourceRecipient.medium == 'email')
        q = q.order_by(None).order_by(ResourceRecipient.address)
        q = q.with_entities(ResourceRecipient.address,
                            ResourceRecipient.content)

        for res in q:
            if self.resource.hex in res.content['resources'] \
                    and res.content.get('rejected_reservations', {}):
                yield res.address

    forms = FormCollection(request.session)
    submission = forms.submissions.by_id(token)
    if submission:
        title = request.translate(
            _(
                "${org} Rejected Reservation",
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

        def email_iter():
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
        ticket.create_snapshot(request)

    for reservation in targeted:
        resource.scheduler.remove_reservation(token, reservation.id)

    if len(excluded) == 0 and submission:
        forms.submissions.delete(submission)

    if len(targeted) > 1:
        request.success(_("The reservations were rejected"))
    else:
        request.success(_("The reservation was rejected"))

    # return none on intercooler js requests
    if not request.headers.get('X-IC-Request'):
        return request.redirect(request.link(self))


@OrgApp.form(model=Reservation, name='reject-with-message', permission=Private,
             form=InternalTicketChatMessageForm, template='form.pt')
def reject_reservation_with_message(self, request, form, layout=None):
    recipient = self.email
    if not recipient:
        request.alert(_("The submitter email is not available"))
        return request.redirect(request.link(self))

    if form.submitted(request):
        return reject_reservation(
            self, request, text=form.text.data, notify=form.notify.data)

    return {
        'title': _("Reject all reservations with message"),
        'layout': layout or TicketChatMessageLayout(self, request),
        'form': form,
        'helptext': _(
            "The following message will be sent to ${address} and it will be "
            "recorded for future reference.", mapping={
                'address': recipient
            }
        )
    }
