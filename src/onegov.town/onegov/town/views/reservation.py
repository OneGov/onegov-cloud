import morepath

from libres.db.models import Allocation, Reservation
from libres.modules.errors import LibresError
from onegov.core.security import Public
from onegov.form import FormCollection
from onegov.libres import ResourceCollection
from onegov.town import TownApp, _, utils
from onegov.town.elements import Link
from onegov.town.forms import ReservationForm
from onegov.town.layout import ResourceLayout
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

            # if extra form data is required, this is the first step.
            # together with the unconfirmed, session-bound reservation,
            # we create a new external submission without any data in it.
            # the user is then redirected to the reservation data edit form
            # where the reservation is finalized and a ticket is opened.
            if resource.definition:
                FormCollection(request.app.session()).submissions.add_external(
                    form=resource.form_class(),
                    state='pending',
                    id=reservation.id
                )

                next_view = 'daten'
            else:
                next_view = 'abschluss'

            return morepath.redirect(request.link(reservation, next_view))

    layout = ResourceLayout(resource, request)
    layout.breadcrumbs.append(Link(_("Reserve"), '#'))

    title = _("New reservation for ${title}", mapping={
        'title': resource.title,
    })

    return {
        'layout': layout,
        'title': title,
        'form': form,
        'allocation': self,
        'available': self.is_available,
        'button_text': _("Continue")
    }


@TownApp.html(model=Reservation, name='abschluss', permission=Public,
              template='layout.pt')
def finalize_reservation(self, request):
    # this view is public, but only for reservations with a session id
    if not self.session_id:
        raise exc.HTTPForbidden()

    if self.session_id != get_libres_session_id(request):
        raise exc.HTTPForbidden()

    if self.status == 'approved':
        raise exc.HTTPForbidden()

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
            'title': _("The reservation could not be finalized"),
            'layout': ResourceLayout(resource, request),
        }
    else:
        # TODO create ticket

        request.success(_("Your reservation was completed"))
        return morepath.redirect(request.link(resource))
