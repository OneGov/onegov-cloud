
from onegov.core.security import Public
from onegov.event import Event, OccurrenceCollection
from onegov.org.views.event import event_form, handle_new_event, view_event, \
    handle_edit_event
from onegov.town6 import TownApp


@TownApp.form(
    model=OccurrenceCollection,
    name='new',
    template='form.pt',
    form=event_form,
    permission=Public
)
def town_handle_new_event(self, request, form):
    return handle_new_event(self, request, form)


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
    return view_event(self, request)


@TownApp.form(
    model=Event,
    name='edit',
    template='form.pt',
    permission=Public,
    form=event_form
)
def town_handle_edit_event(self, request, form):
    return handle_edit_event(self, request, form)
