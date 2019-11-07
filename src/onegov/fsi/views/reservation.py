from onegov.fsi import FsiApp
from onegov.fsi.collections.reservation import ReservationCollection
from onegov.fsi.layouts.reservation import ReservationLayout
from onegov.org.forms import ReservationForm
from onegov.fsi import _


@FsiApp.html(
    model=ReservationCollection,
    template='reservation.pt')
def view_reservations(self, request):
    layout = ReservationLayout(self, request)
    return {
            'title': _('Reservations'),
            'layout': layout,
            'model': self,
            'reservations': self.query().all()
    }


@FsiApp.html(
    model=ReservationCollection,
    template='form.pt',
    name='add',
    form=ReservationForm
)
def view_add_reservation_confirmation(self, request):
    layout = ReservationLayout(self, request)
    return {
            'title': _('Add Reservation'),
            'layout': layout,
            'model': self,
    }


@FsiApp.html(
    model=ReservationCollection,
    request_method='POST',
    name='add-from-course-event'
)
def view_add_reservation_confirmation(self, request):
    request.assert_valid_csrf_token()
    self.add(attendee_id=self.attendee_id,
             course_event_id=self.course_event_id
    )
    request.success(_('New reservation successfully added'))