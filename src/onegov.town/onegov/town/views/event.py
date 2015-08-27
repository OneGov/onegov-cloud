""" The onegov town collection of images uploaded to the site. """
import morepath

from onegov.core.security import Private, Public
from onegov.event import Event, EventCollection, OccurrenceCollection
from onegov.ticket import TicketCollection
from onegov.town import _
from onegov.town.app import TownApp
from onegov.town.elements import Link
from onegov.town.forms import EventForm
from onegov.town.layout import DefaultLayout, EventLayout
from onegov.user import UserCollection
from purl import URL
from sedate import replace_timezone, to_timezone


@TownApp.html(model=EventCollection, template='events.pt', permission=Private)
def view_events(self, request):
    """ Display all events in a list.

    This view is not actually used and may be removed later.
    """

    layout = DefaultLayout(self, request)
    layout.breadcrumbs = [
        Link(_("Homepage"), layout.homepage_url),
        Link(_("Events"), layout.events_url),
        Link(_("List"), '#')
    ]

    def get_filters():
        states = (
            ('initiated', _("Initiated")),
            ('submitted', _("Submitted")),
            ('published', _("Published")),
            ('withdrawn', _("Withdrawn"))
        )

        for id, text in states:
            yield Link(
                text=text,
                url=request.link(self.for_state(id)),
                active=self.state == id
            )

    if self.state == 'initiated':
        events_title = _("Initiated events")
    elif self.state == 'submitted':
        events_title = _("Submitted events")
    elif self.state == 'published':
        events_title = _("Published events")
    elif self.state == 'withdrawn':
        events_title = _("Withdrawn events")
    else:
        raise NotImplementedError

    return {
        'title': _("Events"),
        'layout': layout,
        'events': self.batch,
        'filters': tuple(get_filters()),
        'events_title': events_title,
    }


@TownApp.view(model=Event, name='publish', permission=Private)
def publish_event(self, request):
    """ Publish an event. """

    self.publish()

    request.success(_(u"You have published the event ${title}", mapping={
        'title': self.title
    }))

    if 'return-to' in request.GET:
        return morepath.redirect(request.GET['return-to'])

    return morepath.redirect(request.link(self))


@TownApp.view(model=Event, name='withdraw', permission=Private)
def withdraw_event(self, request):
    """ Withdraw an event. """

    self.withdraw()

    request.success(_(u"You have withdrawn the event ${title}", mapping={
        'title': self.title
    }))

    if 'return-to' in request.GET:
        return morepath.redirect(request.GET['return-to'])

    return morepath.redirect(request.link(self))


@TownApp.form(model=OccurrenceCollection, name='neu', template='form.pt',
              form=EventForm)
def handle_new_event(self, request, form):
    """ Add a new event.

    As an anonymous user, the event is created and the user is redirected to
    a view where he can review his submission and submit it finally.

    As a logged-in user, the event is created and submitted, a ticket is opened
    and the user redirected to the ticket.

    """

    if request.is_logged_in:
        self.title = _("Add an event")
    else:
        self.title = _("Submit an event")

    if form.submitted(request):
        model = Event()
        form.update_model(model)

        event = EventCollection(self.session).add(
            title=model.title,
            start=model.start,
            end=model.end,
            timezone=model.timezone,
            recurrence=model.recurrence,
            tags=model.tags,
            location=model.location,
            content=model.content,
        )

        if request.is_logged_in:
            event.submit()

            with self.session.no_autoflush:
                user = UserCollection(self.session).by_username(
                    request.identity.userid
                )
                ticket = TicketCollection(self.session).open_ticket(
                    handler_code='EVN', handler_id=event.id.hex
                )
                ticket.accept_ticket(user)
                request.app.update_ticket_count()

            request.success(_("Event added"))
            return morepath.redirect(request.link(ticket))
        else:
            return morepath.redirect(request.link(event))

    layout = EventLayout(self, request)
    layout.editbar_links = []

    return {
        'layout': layout,
        'title': self.title,
        'form': form,
        'form_width': 'large'
    }


def get_anon_redirection(request, event):
    """ Returns a redirect depeding on the event state for anonymous users. """

    if event.state == 'published':
        return morepath.redirect(request.link(event.occurrences[0]))
    else:
        return morepath.redirect(request.link(
            OccurrenceCollection(request.app.session())
        ))


@TownApp.html(model=Event, template='event.pt', permission=Public,
              request_method='GET')
@TownApp.html(model=Event, template='event.pt', permission=Public,
              request_method='POST')
def view_event(self, request):
    """ View an event.

    An anonymous user can only view initiated events (assuming its theirs), the
    form to finally submit the event is renderer.

    A logged-in user can view all events and might edit them.

    """

    if self.state != 'initiated' and not request.is_logged_in:
        return get_anon_redirection(request, self)

    if 'complete' in request.POST and self.state == 'initiated':
        self.submit()

        session = request.app.session()
        with session.no_autoflush:
            ticket = TicketCollection(session).open_ticket(
                handler_code='EVN', handler_id=self.id.hex
            )
        request.app.update_ticket_count()

        # todo: the ticket status page does not really fit (there is no email)
        return morepath.redirect(request.link(ticket, 'status'))

    completable = self.state == 'initiated' and not request.is_logged_in
    return {
        'completable': completable,
        'edit_url': request.link(self, 'bearbeiten'),
        'event': self,
        'layout': EventLayout(self, request),
        'title': self.title,
    }


@TownApp.form(model=Event, name='bearbeiten', template='form.pt',
              permission=Public, form=EventForm)
def handle_edit_event(self, request, form):
    """ Edit an event.

    An anonymous user might edit an initiated event.

    A logged in user can edit all events.

    """

    if self.state != 'initiated' and not request.is_logged_in:
        return get_anon_redirection(request, self)

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

    EventCollection(request.app.session()).delete(self)
