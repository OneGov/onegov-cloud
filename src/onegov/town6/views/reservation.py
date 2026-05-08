from __future__ import annotations

from onegov.core.security import Public, Private
from onegov.org.forms import (
    AddReservationForm,
    KabaEditForm,
    InternalTicketChatMessageForm,
    ReservationAdjustmentForm,
)
from onegov.org.models.ticket import ReservationTicket
from onegov.org.views.reservation import (
    add_reservation,
    add_reservation_from_ticket,
    handle_reservation_form,
    confirm_reservation,
    get_reservation_form_class,
    finalize_reservation,
    accept_reservation_with_message,
    accept_reservation_with_message_from_ticket,
    adjust_reservation,
    adjust_reservation_from_ticket,
    edit_kaba,
    edit_kaba_from_ticket,
    reject_reservation_with_message,
    reject_reservation_with_message_from_ticket,
)
from onegov.town6 import TownApp

from onegov.reservation import Reservation, Resource
from onegov.town6.layout import (
    ReservationLayout,
    TicketChatMessageLayout,
    TicketLayout,
)


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
    request: TownRequest,
    form: ReservationForm
) -> RenderData | Response:
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
    request: TownRequest
) -> RenderData:
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
    request: TownRequest
) -> Response:
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
    request: TownRequest,
    form: InternalTicketChatMessageForm
) -> RenderData | Response:
    layout = TicketChatMessageLayout(self, request)  # type:ignore
    return accept_reservation_with_message(self, request, form, layout)


@TownApp.form(
    model=ReservationTicket,
    name='accept-reservation-with-message',
    permission=Private,
    form=InternalTicketChatMessageForm,
    template='form.pt'
)
def town_accept_reservation_with_message_from_ticket(
    self: ReservationTicket,
    request: TownRequest,
    form: InternalTicketChatMessageForm,
    layout: TicketChatMessageLayout | None = None
) -> RenderData | Response | None:
    layout = TicketChatMessageLayout(self, request, internal=True)
    return accept_reservation_with_message_from_ticket(
        self, request, form, layout)


@TownApp.form(
    model=Reservation,
    name='reject-with-message',
    permission=Private,
    form=InternalTicketChatMessageForm,
    template='form.pt'
)
def town_reject_reservation_with_message(
    self: Reservation,
    request: TownRequest,
    form: InternalTicketChatMessageForm
) -> RenderData | Response | None:
    layout = TicketChatMessageLayout(self, request)  # type:ignore
    return reject_reservation_with_message(self, request, form, layout)


@TownApp.form(
    model=ReservationTicket,
    name='reject-reservation-with-message',
    permission=Private,
    form=InternalTicketChatMessageForm,
    template='form.pt'
)
def town_reject_reservation_with_message_from_ticket(
    self: ReservationTicket,
    request: TownRequest,
    form: InternalTicketChatMessageForm,
    layout: TicketChatMessageLayout | None = None
) -> RenderData | Response | None:
    layout = TicketChatMessageLayout(self, request, internal=True)
    return reject_reservation_with_message_from_ticket(
        self, request, form, layout)


@TownApp.form(
    model=Reservation,
    name='add',
    permission=Private,
    form=AddReservationForm,
    template='form.pt'
)
def town_add_reservation(
    self: Reservation,
    request: TownRequest,
    form: AddReservationForm
) -> RenderData | Response | None:
    layout = ReservationLayout(self, request)  # type:ignore
    return add_reservation(self, request, form, None, layout)


@TownApp.form(
    model=ReservationTicket,
    name='add-reservation',
    permission=Private,
    form=AddReservationForm,
    template='form.pt'
)
def town_add_reservation_from_ticket(
    self: ReservationTicket,
    request: TownRequest,
    form: AddReservationForm,
    layout: TicketLayout | None = None
) -> RenderData | Response | None:
    layout = TicketLayout(self, request)
    return add_reservation_from_ticket(
        self, request, form, layout)


@TownApp.form(
    model=Reservation,
    name='adjust',
    permission=Private,
    form=ReservationAdjustmentForm,
    template='form.pt'
)
def town_adjust_reservation(
    self: Reservation,
    request: TownRequest,
    form: ReservationAdjustmentForm
) -> RenderData | Response | None:
    layout = ReservationLayout(self, request)  # type:ignore
    return adjust_reservation(self, request, form, None, layout)


@TownApp.form(
    model=ReservationTicket,
    name='adjust-reservation',
    permission=Private,
    form=ReservationAdjustmentForm,
    template='form.pt'
)
def town_adjust_reservation_from_ticket(
    self: ReservationTicket,
    request: TownRequest,
    form: ReservationAdjustmentForm,
    layout: TicketLayout | None = None
) -> RenderData | Response | None:
    layout = TicketLayout(self, request)
    return adjust_reservation_from_ticket(
        self, request, form, layout)


@TownApp.form(
    model=Reservation,
    name='edit-kaba',
    permission=Private,
    form=KabaEditForm,
    template='form.pt'
)
def town_edit_kaba(
    self: Reservation,
    request: TownRequest,
    form: KabaEditForm
) -> RenderData | Response | None:
    layout = ReservationLayout(self, request)  # type:ignore
    return edit_kaba(self, request, form, None, layout)


@TownApp.form(
    model=ReservationTicket,
    name='edit-kaba',
    permission=Private,
    form=KabaEditForm,
    template='form.pt'
)
def town_edit_kaba_from_ticket(
    self: ReservationTicket,
    request: TownRequest,
    form: KabaEditForm,
    layout: TicketLayout | None = None
) -> RenderData | Response | None:
    layout = TicketLayout(self, request)
    return edit_kaba_from_ticket(
        self, request, form, layout)
