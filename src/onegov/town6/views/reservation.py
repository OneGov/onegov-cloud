from onegov.core.security import Public, Private
from onegov.org.forms import InternalTicketChatMessageForm
from onegov.org.views.reservation import (
    handle_reservation_form, confirm_reservation, get_reservation_form_class,
    finalize_reservation, accept_reservation_with_message,
    reject_reservation_with_message)
from onegov.town6 import TownApp

from onegov.reservation import Reservation, Resource
from onegov.town6.layout import ReservationLayout, TicketChatMessageLayout


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.org.forms import ReservationForm
    from onegov.town6.request import TownRequest
    from webob import Response


@TownApp.form(
    model=Resource,
    name='form',
    template='reservation_form.pt',
    permission=Public,
    form=get_reservation_form_class
)
def town_handle_reservation_form(
    self: Resource,
    request: 'TownRequest',
    form: 'ReservationForm'
) -> 'RenderData | Response':
    return handle_reservation_form(
        self, request, form, ReservationLayout(self, request))


@TownApp.html(
    model=Resource,
    name='confirmation',
    permission=Public,
    template='reservation_confirmation.pt'
)
def town_confirm_reservation(
    self: Resource,
    request: 'TownRequest'
) -> 'RenderData':
    return confirm_reservation(self, request, ReservationLayout(self, request))


# FIXME: Why are we even overriding this view...
@TownApp.html(
    model=Resource,
    name='finish',
    permission=Public,
    template='layout.pt',
    request_method='POST'
)
def town_finalize_reservation(
    self: Resource,
    request: 'TownRequest'
) -> 'Response':
    """Returns a redirect, no layout passed"""
    return finalize_reservation(self, request)


@TownApp.form(
    model=Reservation,
    name='accept-with-message',
    permission=Private,
    form=InternalTicketChatMessageForm,
    template='form.pt'
)
def town_accept_reservation_with_message(
    self: Reservation,
    request: 'TownRequest',
    form: InternalTicketChatMessageForm
) -> 'RenderData | Response':
    layout = TicketChatMessageLayout(self, request)  # type:ignore
    return accept_reservation_with_message(self, request, form, layout)


@TownApp.form(
    model=Reservation,
    name='reject-with-message',
    permission=Private,
    form=InternalTicketChatMessageForm,
    template='form.pt'
)
def town_reject_reservation_with_message(
    self: Reservation,
    request: 'TownRequest',
    form: InternalTicketChatMessageForm
) -> 'RenderData | Response | None':
    layout = TicketChatMessageLayout(self, request)  # type:ignore
    return reject_reservation_with_message(self, request, form, layout)
