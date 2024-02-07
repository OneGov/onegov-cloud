
from onegov.core.security import Public, Private
from onegov.event import Event, OccurrenceCollection
from onegov.org.views.event import (
    event_form as org_event_form, handle_new_event, view_event,
    handle_edit_event, handle_new_event_without_workflow)
from onegov.town6 import TownApp
from onegov.town6.forms.event import EventForm
from onegov.town6.layout import EventLayout


def event_form(model, request):
    return org_event_form(model, request, EventForm)


@TownApp.form(
    model=OccurrenceCollection,
    name='new',
    template='form.pt',
    form=event_form,
    permission=Public
)
def town_handle_new_event(self, request, form):
    layout = EventLayout(self, request)
    return handle_new_event(self, request, form, layout)


@TownApp.form(
    model=OccurrenceCollection,
    name='enter-event',
    template='form.pt',
    form=event_form,
    permission=Private
)
def town_handle_new_event_without_workflow(self, request, form):
    layout = EventLayout(self, request)
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
def town_view_event(self, request):
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
def town_handle_edit_event(self, request, form):
    layout = EventLayout(self, request)
    return handle_edit_event(self, request, form, layout)
