""" The onegov town collection of images uploaded to the site. """
from onegov.town import _
from onegov.town.app import TownApp
from onegov.town.elements import Link
from onegov.town.layout import EventLayout, EventsLayout
from onegov.event import Occurrence, OccurrenceCollection


@TownApp.html(model=OccurrenceCollection, template='events.pt')
def view_occurrences(self, request):
    layout = EventsLayout(self, request)

    return {
        'layout': layout,
        'title': _(u'Events'),
        'events': self.batch,
        'used_tags': self.used_tags,
        'number_events': self.query().count()
    }


@TownApp.html(model=Occurrence, template='event.pt')
def view_get_occurrence(self, request):
    layout = EventLayout(self, request)

    return {
        'layout': layout,
        'event': self,
        'title': self.title,
    }
