
from onegov.core.security import Public
from onegov.event import Event, OccurrenceCollection
from onegov.org.views.event import event_form as org_event_form, \
    handle_new_event, view_event, handle_edit_event
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
    request.include('many')
    return handle_new_event(self, request, form, layout)


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
    return view_event(self, request, EventLayout(self, request))


@TownApp.form(
    model=Event,
    name='edit',
    template='form.pt',
    permission=Public,
    form=event_form
)
def town_handle_edit_event(self, request, form):
    layout = EventLayout(self, request)
    request.include('many')
    return handle_edit_event(self, request, form, layout)
