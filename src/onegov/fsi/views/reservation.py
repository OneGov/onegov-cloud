from onegov.fsi import FsiApp
from onegov.fsi.collections.reservation import ReservationCollection
from onegov.fsi.layout import ReservationLayout
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


@FsiApp.form(
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