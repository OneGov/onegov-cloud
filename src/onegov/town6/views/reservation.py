from onegov.core.security import Public
from onegov.org.views.reservation import handle_reservation_form, \
    confirm_reservation, get_reservation_form_class, finalize_reservation
from onegov.town6 import TownApp

from onegov.reservation import Resource
from onegov.town6.layout import ReservationLayout


@TownApp.form(model=Resource, name='form', template='reservation_form.pt',
              permission=Public, form=get_reservation_form_class)
def town_handle_reservation_form(self, request, form):
    return handle_reservation_form(
        self, request, form, ReservationLayout(self, request))


@TownApp.html(model=Resource, name='confirmation', permission=Public,
              template='reservation_confirmation.pt')
def town_confirm_reservation(self, request):
    return confirm_reservation(self, request, ReservationLayout(self, request))


@TownApp.html(model=Resource, name='finish', permission=Public,
              template='layout.pt', request_method='POST')
def town_finalize_reservation(self, request):
    """Returns a redirect, no layout passed"""
    return finalize_reservation(self, request)
