""" The onegov town collection of images uploaded to the site. """
from datetime import date
from onegov.core.utils import linkify
from onegov.town import _
from onegov.town.app import TownApp
from onegov.town.elements import Link
from onegov.town.layout import OccurrenceLayout, OccurrencesLayout
from onegov.event import Occurrence, OccurrenceCollection


@TownApp.html(model=OccurrenceCollection, template='occurrences.pt')
def view_occurrences(self, request):
    """ View all occurrences of all events. """

    request.include('common')
    request.include('events')

    layout = OccurrencesLayout(self, request)

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
        'occurrences': self.batch,
        'tags': tags,
        'active_tags': self.tags,
        'number_of_occurrences': self.subset().count(),
        'start': self.start.isoformat() if self.start else '',
        'end': self.end.isoformat() if self.end else '',
        'date_placeholder': date.today().isoformat(),
        'add_link': request.link(self, name='neu')
    }


@TownApp.html(model=Occurrence, template='occurrence.pt')
def view_get_occurrence(self, request):
    """ View a single occurrence of an event. """

    layout = OccurrenceLayout(self, request)
    occurrences = self.event.occurrence_dates(localize=True)
    description = linkify(self.event.description).replace('\n', '<br>')

    return {
        'layout': layout,
        'occurrence': self,
        'occurrences': occurrences,
        'title': self.title,
        'description': description
    }
