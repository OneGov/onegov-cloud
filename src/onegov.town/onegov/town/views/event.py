""" The onegov town collection of images uploaded to the site. """
import morepath

from morepath.request import Response
from onegov.core.security import Private, Public
from onegov.event import Event, EventCollection, OccurrenceCollection
from onegov.ticket import TicketCollection
from onegov.town import _
from onegov.town.app import TownApp
from onegov.town.elements import Link
from onegov.town.forms import EventForm
from onegov.town.layout import EventLayout
from onegov.town.mail import send_html_mail
from sedate import utcnow
from purl import URL
from uuid import uuid4
from webob import exc


def get_session_id(request):
    if not request.browser_session.has('event_session_id'):
        request.browser_session.event_session_id = uuid4()

    return str(request.browser_session.event_session_id)


def assert_anonymous_access_only_temporary(request, event):
    """ Raises exceptions if the current user is anonymous and no longer
    should be given access to the event.

    This could probably be done using morepath's security system, but it would
    not be quite as straight-forward. This approach is, though we have
    to manually add this function to all public views the anonymous user
    should be able to access when creating a new event, but not anymore
    after that.

    """
    if request.is_logged_in:
        return

    if event.state != 'initiated':
        raise exc.HTTPForbidden()

    session_id = event.meta.get('session_id') if event.meta else None
    if not session_id:
        raise exc.HTTPForbidden()

    if session_id != get_session_id(request):
        raise exc.HTTPForbidden()


@TownApp.view(model=Event, name='publish', permission=Private)
def publish_event(self, request):
    """ Publish an event. """

    self.publish()

    request.success(_(u"You have accepted the event ${title}", mapping={
        'title': self.title
    }))

    if self.meta.get('submitter_email'):
        send_html_mail(
            request=request,
            template='mail_event_accepted.pt',
            subject=_("Your event was accepted"),
            receivers=(self.meta.get('submitter_email'), ),
            content={
                'model': self,
            }
        )

    if 'return-to' in request.GET:
        return morepath.redirect(request.GET['return-to'])

    return morepath.redirect(request.link(self))


@TownApp.form(model=OccurrenceCollection, name='neu', template='form.pt',
              form=EventForm, permission=Public)
def handle_new_event(self, request, form):
    """ Add a new event.

    The event is created and the user is redirected to a view where he can
    review his submission and submit it finally.

    """

    self.title = _("Submit an event")

    if form.submitted(request):
        model = Event()
        form.update_model(model)
        meta = model.meta
        meta.update({'session_id': get_session_id(request)})

        event = EventCollection(self.session).add(
            title=model.title,
            start=model.start,
            end=model.end,
            timezone=model.timezone,
            recurrence=model.recurrence,
            tags=model.tags,
            location=model.location,
            content=model.content,
            meta=meta
        )

        return morepath.redirect(request.link(event))

    layout = EventLayout(self, request)
    layout.editbar_links = []

    return {
        'layout': layout,
        'title': self.title,
        'form': form,
        'form_width': 'large'
    }


@TownApp.html(model=Event, template='event.pt', permission=Public,
              request_method='GET')
@TownApp.html(model=Event, template='event.pt', permission=Public,
              request_method='POST')
def view_event(self, request):
    """ View an event.

    If the event is not already submitted, the submit form is displayed.

    A logged-in user can view all events and might edit them, an anonymous user
    will be redirected.
    """

    assert_anonymous_access_only_temporary(request, self)

    if 'complete' in request.POST and self.state == 'initiated':
        if self.meta and 'session_id' in self.meta:
            del self.meta['session_id']

        self.submit()

        session = request.app.session()
        with session.no_autoflush:
            ticket = TicketCollection(session).open_ticket(
                handler_code='EVN', handler_id=self.id.hex
            )

        send_html_mail(
            request=request,
            template='mail_ticket_opened.pt',
            subject=_("A ticket has been opened"),
            receivers=(self.meta.get('submitter_email'), ),
            content={
                'model': ticket
            }
        )

        request.success(_("Thank you for your submission!"))
        request.app.update_ticket_count()

        return morepath.redirect(request.link(ticket, 'status'))

    session = request.app.session()
    ticket = TicketCollection(session).by_handler_id(self.id.hex)

    return {
        'completable': self.state == 'initiated',
        'edit_url': request.link(self, 'bearbeiten'),
        'event': self,
        'layout': EventLayout(self, request),
        'ticket': ticket,
        'title': self.title,
    }


@TownApp.form(model=Event, name='bearbeiten', template='form.pt',
              permission=Public, form=EventForm)
def handle_edit_event(self, request, form):
    """ Edit an event.

    An anonymous user might edit an initiated event, a logged in user can also
    edit all events.

    """

    assert_anonymous_access_only_temporary(request, self)

    if form.submitted(request):
        form.update_model(self)

        request.success(_(u"Your changes were saved"))

        if 'return-to' in request.GET:
            return morepath.redirect(request.GET['return-to'])

        return morepath.redirect(request.link(self))

    form.apply_model(self)

    if 'return-to' in request.GET:
        action = URL(form.action)
        action = action.query_param('return-to', request.GET['return-to'])
        form.action = action.as_string()

    layout = EventLayout(self, request)
    layout.breadcrumbs.append(Link(_("Edit"), '#'))
    layout.editbar_links = []

    return {
        'layout': layout,
        'title': self.title,
        'form': form,
        'form_width': 'large'
    }


@TownApp.view(model=Event, request_method='DELETE', permission=Private)
def handle_delete_event(self, request):
    """ Delete an event. """

    request.assert_valid_csrf_token()

    # Create a snapshot of the ticket to keep the useful information.
    tickets = TicketCollection(request.app.session())
    ticket = tickets.by_handler_id(self.id.hex)
    if ticket:
        ticket.create_snapshot(request)

    if self.meta.get('submitter_email'):
        send_html_mail(
            request=request,
            template='mail_event_rejected.pt',
            subject=_("Your event was rejected"),
            receivers=(self.meta.get('submitter_email'), ),
            content={
                'model': self,
            }
        )

    EventCollection(request.app.session()).delete(self)


@TownApp.view(model=Event, name='ical', permission=Public)
def ical_export_event(self, request):
    """ Returns the event with all occurrences as ics. """

    try:
        url = request.link(self.occurrences[0])
    except IndexError:
        url = EventLayout(self, request).events_url

    return Response(
        self.as_ical(url=url),
        content_type='text/calendar',
        content_disposition='inline; filename=calendar.ics'
    )


@TownApp.view(model=Event, permission=Public, name='latest')
def view_latest_event(self, request):
    """ Redirects to the latest occurrence of an event that is, either the
    next future event or the last event in the past if there are no more
    future events.

    """

    now = utcnow()

    for occurrence in self.occurrences:
        if now < occurrence.start:
            return morepath.redirect(request.link(occurrence))

    return morepath.redirect(request.link(occurrence))
