import morepath

from libres.db.models import Allocation
from libres.modules.errors import LibresError
from onegov.core.security import Public
from onegov.libres import ResourceCollection
from onegov.town import TownApp, _, utils
from onegov.town.elements import Link
from onegov.town.layout import ResourceLayout
from onegov.town.forms import ReservationForm
from uuid import uuid4


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
            return morepath.redirect(request.link(reservation), 'daten')

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
