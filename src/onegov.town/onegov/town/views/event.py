""" The onegov town collection of images uploaded to the site. """
from datetime import date
from onegov.core.security import Private
from onegov.event import Event, EventCollection, OccurrenceCollection
from onegov.town import _
from onegov.town.app import TownApp
from onegov.town.elements import Link
from onegov.town.layout import DefaultLayout


@TownApp.html(model=EventCollection, template='events.pt', permission=Private)
def view_events(self, request):

    layout = DefaultLayout(self, request)
    layout.breadcrumbs = [
        Link(_("Homepage"), layout.homepage_url),
        Link(_("Events"), layout.events_url),
        Link(_("List"), '#')
    ]

    def get_filters():
        states = (
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

    if self.state == 'submitted':
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


@TownApp.html(model=Event, template='event.pt', permission=Private)
def view_event(self, request):
    event_url = request.link(
        EventCollection(request.app.session()).for_state(self.state)
    )
    if self.occurrences:
        event_url = request.link(self.occurrences[0])

    layout = DefaultLayout(self, request)
    layout.breadcrumbs = [
        Link(_("Homepage"), layout.homepage_url),
        Link(_("Events"), layout.events_url),
        Link(self.title, event_url),
        Link(_("Edit"), '#')
    ]

    return {
        'title': self.title,
        'layout': layout,
        'ticket': self
    }
