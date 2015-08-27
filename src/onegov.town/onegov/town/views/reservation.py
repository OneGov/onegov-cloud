import morepath

from libres.db.models import Allocation, Reservation
from libres.modules.errors import LibresError
from onegov.core.security import Public
from onegov.form import FormCollection
from onegov.libres import ResourceCollection
from onegov.ticket import TicketCollection
from onegov.town import TownApp, _, utils
from onegov.town.elements import Link
from onegov.town.forms import ReservationForm
from onegov.town.layout import ResourceLayout
from onegov.town.mail import send_html_mail
from purl import URL
from uuid import uuid4
from webob import exc


def get_reservation_form_class(allocation, request):
    return ReservationForm.for_allocation(allocation)


def get_libres_session_id(request):
    if not request.browser_session.has('libres_session_id'):
        request.browser_session.libres_session_id = uuid4()

    return request.browser_session.libres_session_id


@TownApp.form(model=Allocation, name='reservieren', template='reservation.pt',
              permission=Public, form=get_reservation_form_class)
def handle_reserve_allocation(self, request, form):
    """ Creates a new reservation for the given allocation.
    """

    collection = ResourceCollection(request.app.libres_context)
    resource = collection.by_id(self.resource)

    if form.submitted(request):

        if self.partly_available:
            start, end = form.data['start'], form.data['end']
        else:
            start, end = self.start, self.end

        try:
            scheduler = resource.get_scheduler(request.app.libres_context)
            token = scheduler.reserve(
                email=form.data['e_mail'],
                dates=(start, end),
                quota=int(form.data.get('quota', 1)),
                session_id=get_libres_session_id(request)
            )
        except LibresError as e:
            utils.show_libres_error(e, request)
        else:
            # though it's possible for a token to have multiple reservations,
            # it is not something that can happen here -> therefore one!
            reservation = scheduler.reservations_by_token(token).one()
            finalize_link = request.link(reservation, 'abschluss')

            if not resource.definition:
                return morepath.redirect(finalize_link)

            # if extra form data is required, this is the first step.
            # together with the unconfirmed, session-bound reservation,
            # we create a new external submission without any data in it.
            # the user is then redirected to the reservation data edit form
            # where the reservation is finalized and a ticket is opened.
            forms = FormCollection(request.app.session())
            submission = forms.submissions.add_external(
                form=resource.form_class(),
                state='pending',
                id=reservation.token
            )

            url = URL(request.link(submission))
            url = url.query_param('return-to', finalize_link)
            url = url.query_param('title', request.translate(
                _("Further information about the reservation"))
            )
            url = url.query_param('edit', 1)
            url = url.query_param('quiet', 1)

            return morepath.redirect(url.as_string())

    layout = ResourceLayout(resource, request)
    layout.breadcrumbs.append(Link(_("Reserve"), '#'))

    if resource.definition:
        button_text = _("Continue")
    else:
        button_text = _("Submit")

    title = _("New reservation for ${title}", mapping={
        'title': resource.title,
    })

    return {
        'layout': layout,
        'title': title,
        'form': form,
        'allocation': self,
        'button_text': button_text
    }


def assert_anonymous_access_only_temporary(self, request):
    """ Raises exceptions if the current user is anonymous and no longer
    should be given access to the reservation models.

    This could probably be done using morepath's security system, but it would
    not be quite as straight-forward. This approach is, though we have
    to manually add this function to all reservation views the anonymous user
    should be able to access when creating a new reservatin, but not anymore
    after that.

    """
    if request.is_logged_in:
        return

    if not self.session_id:
        raise exc.HTTPForbidden()

    if self.status == 'approved':
        raise exc.HTTPForbidden()

    if self.session_id != get_libres_session_id(request):
        raise exc.HTTPForbidden()


@TownApp.html(model=Reservation, name='abschluss', permission=Public,
              template='layout.pt')
def finalize_reservation(self, request):

    # this view is public, but only for a limited time
    assert_anonymous_access_only_temporary(self, request)

    collection = ResourceCollection(request.app.libres_context)
    resource = collection.by_id(self.resource)
    scheduler = resource.get_scheduler(request.app.libres_context)

    try:
        scheduler.approve_reservations(self.token)
    except LibresError as e:
        utils.show_libres_error(e, request)

        layout = ResourceLayout(resource, request)
        layout.breadcrumbs.append(Link(_("Error"), '#'))

        return {
            'title': _("The reservation could not be completed"),
            'layout': ResourceLayout(resource, request),
        }
    else:
        forms = FormCollection(request.app.session())
        submission = forms.submissions.by_id(self.token)

        if submission:
            forms.submissions.complete_submission(submission)

        with forms.session.no_autoflush:
            ticket = TicketCollection(request.app.session()).open_ticket(
                handler_code='RSV', handler_id=self.token
            )

        send_html_mail(
            request=request,
            template='mail_ticket_opened.pt',
            subject=_("A ticket has been opened"),
            receivers=(self.email, ),
            content={
                'model': ticket
            }
        )

        request.app.update_ticket_count()
        request.success(_("Your reservation was completed"))
        return morepath.redirect(request.link(resource))
