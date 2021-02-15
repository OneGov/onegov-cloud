""" The onegov org collection of images uploaded to the site. """
import morepath

from morepath.request import Response
from onegov.core.security import Private, Public
from onegov.event import Event, EventCollection, OccurrenceCollection
from onegov.org.views.event import event_form, handle_new_event, view_event, \
    handle_edit_event
from onegov.town6 import _, TownApp
from onegov.org.cli import close_ticket
from onegov.org.elements import Link
from onegov.org.forms import EventForm
from onegov.org.layout import EventLayout
from onegov.org.mail import send_ticket_mail
from onegov.org.models import TicketMessage, EventMessage
from onegov.org.models.extensions import AccessExtension
from onegov.ticket import TicketCollection
from sedate import utcnow
from uuid import uuid4
from webob import exc


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
