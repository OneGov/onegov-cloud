import json
import morepath
import sedate
import transaction

from datetime import time
from libres.db.models import Allocation, Reservation
from libres.modules.errors import LibresError
from onegov.core.security import Public, Private
from onegov.form import FormCollection, merge_forms
from onegov.reservation import Resource
from onegov.org import utils
from onegov.org.elements import Link
from onegov.org.forms import ReservationForm
from onegov.org.layout import ReservationLayout
from onegov.ticket import TicketCollection
from onegov.org import _, OrgApp
from onegov.org.mail import send_html_mail
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


@OrgApp.json(model=Allocation, name='reserve', request_method='POST',
             permission=Public)
def reserve_allocation(self, request):
    """ Adds a single reservation to the list of reservations bound to the
    current browser session.

    Does not actually reserve anything, just keeps a list of things to
    reserve later. Though it will still check if the reservation is
    feasable.

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

        start, end = sedate.get_date_range(
            sedate.to_timezone(self.start, self.timezone), start, end
        )
    else:
        start = self.start, self.end

    resource = request.app.libres_resources.by_allocation(self)

    try:
        resource.scheduler.reserve(
            email='0xdeadbeef@example.org',  # will be set later
            dates=(start, end),
            quota=quota,
            session_id=resource.bound_session_id(request),
            single_token_per_session=True
        )
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

    try:
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


@OrgApp.form(model=Resource, name='formular', template='reservation_form.pt',
             permission=Public, form=get_reservation_form_class)
def handle_reservation_form(self, request, form):
    """ Asks the user for the form data required to complete one or many
    reservations on a resource.

    """
    reservations_query = self.bound_reservations(request)
    reservations = reservations_query.all()
    assert_access_only_if_there_are_reservations(reservations)

    # all reservations share a single token
    token = reservations[0].token

    # the submission shares the reservation token
    forms = FormCollection(request.app.session())
    submission = forms.submissions.by_id(token)

    # update the data if the form is submitted (even if invalid)
    if request.POST:
        # update the e-mail data
        reservations_query.order_by(False).update(
            {Reservation.email: form.email.data}
        )

        # while we re at it, remove all expired sessions
        self.remove_expired_reservation_sessions()

        # add the submission if it doesn't yet exist
        if self.definition and not submission:
            submission = forms.submissions.add_external(
                form=self.form_class(),
                state='pending',
                id=token
            )

        # update the data on the submission
        if submission:
            forms.submissions.update(
                submission, form, exclude=form.reserved_fields
            )

    # go to the next step if the submitted data is valid
    if form.submitted(request):
        return morepath.redirect(request.link(self, 'bestaetigung'))
    else:
        data = {}

        # the email is the same for all reservations
        if reservations[0].email != '0xdeadbeef@example.org':
            data['email'] = reservations[0].email

        if submission:
            data.update(submission.data)

        form.process(data=data)

    layout = ReservationLayout(self, request)
    layout.breadcrumbs.append(Link(_("Reserve"), '#'))

    title = _("New dates for ${title}", mapping={
        'title': self.title,
    })

    return {
        'layout': layout,
        'title': title,
        'form': form,
        'reservation_infos': [
            utils.ReservationInfo(r, request) for r in reservations
        ],
        'resource': self,
        'button_text': _("Continue")
    }


@OrgApp.html(model=Resource, name='bestaetigung', permission=Public,
             template='reservation_confirmation.pt')
def confirm_reservation(self, request):
    reservations = self.bound_reservations(request).all()
    assert_access_only_if_there_are_reservations(reservations)

    token = reservations[0].token.hex

    forms = FormCollection(request.app.session())
    submission = forms.submissions.by_id(token)

    if submission:
        form = request.get_form(submission.form_class, data=submission.data)
    else:
        form = None

    layout = ReservationLayout(self, request)
    layout.breadcrumbs.append(Link(_("Confirm"), '#'))

    failed_reservations = set(
        int(failed) for failed
        in request.params.get('failed_reservations', '').split(',')
        if failed
    )

    return {
        'title': _("Confirm your reservation"),
        'layout': layout,
        'form': form,
        'resource': self,
        'reservation_infos': [
            utils.ReservationInfo(r, request) for r in reservations
        ],
        'failed_reservations': failed_reservations,
        'finalize_link': request.link(self, 'abschluss'),
        'edit_link': request.link(self, 'formular'),
    }


@OrgApp.html(model=Resource, name='abschluss', permission=Public,
             template='layout.pt')
def finalize_reservation(self, request):
    reservations = self.bound_reservations(request).all()
    assert_access_only_if_there_are_reservations(reservations)

    session_id = self.bound_session_id(request)
    token = reservations[0].token.hex

    try:
        self.scheduler.queries.confirm_reservations_for_session(session_id)
        self.scheduler.approve_reservations(token)

    except LibresError as e:
        transaction.abort()
        utils.show_libres_error(e, request)

        url = URL(request.link(self, name='bestaetigung'))
        url = url.query_param('failed_reservations', e.reservation.id)

        return morepath.redirect(url.as_string())
    else:
        forms = FormCollection(request.app.session())
        submission = forms.submissions.by_id(token)

        if submission:
            forms.submissions.complete_submission(submission)

        with forms.session.no_autoflush:
            ticket = TicketCollection(request.app.session()).open_ticket(
                handler_code='RSV', handler_id=token
            )

        if reservations[0].email != request.current_username:
            send_html_mail(
                request=request,
                template='mail_ticket_opened.pt',
                subject=_("A ticket has been opened"),
                receivers=(reservations[0].email, ),
                content={
                    'model': ticket
                }
            )

        request.success(_("Thank you for your reservation!"))

        return morepath.redirect(request.link(ticket, 'status'))


@OrgApp.view(model=Reservation, name='annehmen', permission=Private)
def accept_reservation(self, request):
    if not self.data or not self.data.get('accepted'):
        resource = request.app.libres_resources.by_reservation(self)
        reservations = resource.scheduler.reservations_by_token(self.token)
        reservations = reservations.order_by(Reservation.start)

        if self.email != request.current_username:
            send_html_mail(
                request=request,
                template='mail_reservation_accepted.pt',
                subject=_("Your reservations were accepted"),
                receivers=(self.email, ),
                content={
                    'model': self,
                    'resource': resource,
                    'reservations': reservations
                }
            )

        for reservation in reservations:
            reservation.data = reservation.data or {}
            reservation.data['accepted'] = True

            # libres does not automatically detect changes yet
            flag_modified(reservation, 'data')

        request.success(_("The reservations were accepted"))
    else:
        request.warning(_("The reservations have already been accepted"))

    return request.redirect(request.link(self))


@OrgApp.view(model=Reservation, name='absagen', permission=Private)
def reject_reservation(self, request):
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

    forms = FormCollection(request.app.session())
    submission = forms.submissions.by_id(token)

    if self.email != request.current_username:
        send_html_mail(
            request=request,
            template='mail_reservation_rejected.pt',
            subject=_("The following reservations were rejected"),
            receivers=(self.email, ),
            content={
                'model': self,
                'resource': resource,
                'reservations': targeted
            }
        )

    # create a snapshot of the ticket to keep the useful information
    if len(excluded) == 0:
        tickets = TicketCollection(request.app.session())
        ticket = tickets.by_handler_id(token)
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
