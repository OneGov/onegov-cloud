""" The onegov town collection of images uploaded to the site. """
from datetime import date
from morepath.request import Response
from onegov.core.security import Public
from onegov.core.utils import linkify
from onegov.event import Occurrence, OccurrenceCollection
from onegov.ticket import TicketCollection
from onegov.town import _
from onegov.town.app import TownApp
from onegov.town.elements import Link
from onegov.town.layout import OccurrenceLayout, OccurrencesLayout
from sedate import as_datetime, replace_timezone


@TownApp.html(model=OccurrenceCollection, template='occurrences.pt',
              permission=Public)
def view_occurrences(self, request):
    """ View all occurrences of all events. """

    request.include('common')
    request.include('events')

    layout = OccurrencesLayout(self, request)

    tags = (
        Link(
            text=request.translate(_(tag)),
            url=request.link(self.for_filter(tag=tag)),
            active=tag in self.tags and 'active' or ''
        ) for tag in self.used_tags
    )

    return {
        'active_tags': self.tags,
        'add_link': request.link(self, name='neu'),
        'date_placeholder': date.today().isoformat(),
        'end': self.end.isoformat() if self.end else '',
        'layout': layout,
        'number_of_occurrences': self.subset_count,
        'occurrences': self.batch,
        'start': self.start.isoformat() if self.start else '',
        'tags': tags,
        'title': _(u'Events'),
    }


@TownApp.html(model=Occurrence, template='occurrence.pt', permission=Public)
def view_get_occurrence(self, request):
    """ View a single occurrence of an event. """

    layout = OccurrenceLayout(self, request)
    today = replace_timezone(as_datetime(date.today()), self.timezone)
    occurrences = self.event.occurrence_dates(localize=True)
    occurrences = list(filter(lambda x: x >= today, occurrences))
    description = linkify(self.event.description).replace('\n', '<br>')
    session = request.app.session()
    ticket = TicketCollection(session).by_handler_id(self.event.id.hex)

    return {
        'description': description,
        'layout': layout,
        'occurrence': self,
        'occurrences': occurrences,
        'ticket': ticket,
        'title': self.title,
    }


@TownApp.view(model=Occurrence, name='ical', permission=Public)
def ical_export_occurence(self, request):
    """ Returns the occurrence as ics. """

    return Response(
        self.as_ical(url=request.link(self)),
        content_type='text/calendar',
        content_disposition='inline; filename=calendar.ics'
    )
