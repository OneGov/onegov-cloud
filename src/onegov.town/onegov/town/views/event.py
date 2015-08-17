""" The onegov town collection of images uploaded to the site. """
from datetime import date
from onegov.town import _
from onegov.town.app import TownApp
from onegov.town.elements import Link
from onegov.town.layout import EventLayout, EventsLayout
from onegov.event import Occurrence, OccurrenceCollection


@TownApp.html(model=OccurrenceCollection, template='events.pt')
def view_occurrences(self, request):
    """ View all occurrences of all events. """

    request.include('common')
    request.include('events')

    layout = EventsLayout(self, request)

    tags = (
        Link(
            text=tag,
            url=request.link(self.for_filter(tag=tag)),
            active=tag in self.tags and 'active' or ''
        ) for tag in self.used_tags
    )

    return {
        'layout': layout,
        'title': _(u'Events'),
        'events': self.batch,
        'tags': tags,
        'active_tags': self.tags,
        'number_of_events': self.subset().count(),
        'start': self.start.isoformat() if self.start else '',
        'end': self.end.isoformat() if self.end else '',
        'date_placeholder': date.today().isoformat()
    }


@TownApp.html(model=Occurrence, template='event.pt')
def view_get_occurrence(self, request):
    """ View a single occurrence of an event. """

    layout = EventLayout(self, request)
    occurrences = self.event.occurrence_dates(localize=True)

    return {
        'layout': layout,
        'event': self,
        'occurrences': occurrences,
        'title': self.title,
    }
