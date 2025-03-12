from __future__ import annotations

from onegov.core.security import Public, Private
from onegov.event import Event, OccurrenceCollection
from onegov.org.models.ticket import EventSubmissionTicket
from onegov.org.views.event import (
    event_form as org_event_form,
    handle_new_event,
    view_event,
    handle_edit_event,
    handle_edit_event_from_ticket,
    handle_new_event_without_workflow,
)
from onegov.town6 import TownApp
from onegov.town6.forms.event import EventForm
from onegov.town6.layout import EventLayout, TicketLayout


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest
    from webob import Response


def event_form(model: object, request: TownRequest) -> type[EventForm]:
    return org_event_form(model, request, EventForm)


@TownApp.form(
    model=OccurrenceCollection,
    name='new',
    template='form.pt',
    form=event_form,
    permission=Public
)
def town_handle_new_event(
    self: OccurrenceCollection,
    request: TownRequest,
    form: EventForm
) -> RenderData | Response:
    layout = EventLayout(self, request)  # type:ignore
    return handle_new_event(self, request, form, layout)


@TownApp.form(
    model=OccurrenceCollection,
    name='enter-event',
    template='form.pt',
    form=event_form,
    permission=Private
)
def town_handle_new_event_without_workflow(
    self: OccurrenceCollection,
    request: TownRequest,
    form: EventForm
) -> RenderData | Response:
    layout = EventLayout(self, request)  # type:ignore
    layout.hide_steps = True
    return handle_new_event_without_workflow(self, request, form, layout)


@TownApp.html(
    model=Event,
    template='event.pt',
    permission=Public,
    request_method='GET'
)
@TownApp.html(
    model=Event,
    template='event.pt',
    permission=Public,
    request_method='POST'
)
def town_view_event(
    self: Event,
    request: TownRequest
) -> RenderData | Response:
    layout = EventLayout(self, request)
    layout.get_step_sequence()
    return view_event(self, request, layout)


@TownApp.form(
    model=Event,
    name='edit',
    template='form.pt',
    permission=Public,
    form=event_form
)
def town_handle_edit_event(
    self: Event,
    request: TownRequest,
    form: EventForm
) -> RenderData | Response:
    layout = EventLayout(self, request)
    return handle_edit_event(self, request, form, layout)


@TownApp.form(
    model=EventSubmissionTicket,
    name='edit-event',
    template='form.pt',
    permission=Public,
    form=event_form
)
def town_handle_edit_event_from_ticket(
    self: EventSubmissionTicket,
    request: TownRequest,
    form: EventForm,
    layout: TicketLayout | None = None
) -> RenderData | Response:
    layout = TicketLayout(self, request)
    return handle_edit_event_from_ticket(self, request, form, layout)
