""" The onegov town collection of images uploaded to the site. """
from datetime import date
from onegov.core.security import Public
from onegov.core.utils import linkify
from onegov.event import Occurrence, OccurrenceCollection
from onegov.town import _
from onegov.town.app import TownApp
from onegov.town.elements import Link
from onegov.town.layout import OccurrenceLayout, OccurrencesLayout


@TownApp.html(model=OccurrenceCollection, template='occurrences.pt',
              permission=Public)
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

    lead = _(
        "${town} offers a versatile and colorful social life thanks to its "
        "generous and open culture. Whether exhibition, concert, village "
        "market or theater performance - there's an attractive event for "
        "everybody. You have the possibility to a submit to our event "
        "calendar.",
        mapping={'town': request.app.town.name}
    )

    return {
        'active_tags': self.tags,
        'add_link': request.link(self, name='neu'),
        'date_placeholder': date.today().isoformat(),
        'end': self.end.isoformat() if self.end else '',
        'layout': layout,
        'lead': lead,
        'number_of_occurrences': self.subset().count(),
        'occurrences': self.batch,
        'start': self.start.isoformat() if self.start else '',
        'tags': tags,
        'title': _(u'Events'),
    }


@TownApp.html(model=Occurrence, template='occurrence.pt', permission=Public)
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
