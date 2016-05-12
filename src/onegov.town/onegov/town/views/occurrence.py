""" The onegov town collection of images uploaded to the site. """
from csv import writer
from datetime import date
from io import StringIO
from morepath.request import Response
from onegov.core.security import Public
from onegov.core.utils import linkify
from onegov.event import Event, Occurrence, OccurrenceCollection
from onegov.ticket import TicketCollection
from onegov.town import _
from onegov.town.app import TownApp
from onegov.town.elements import Link
from onegov.town.layout import OccurrenceLayout, OccurrencesLayout
from sedate import as_datetime, replace_timezone
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import JSON


@TownApp.html(model=OccurrenceCollection, template='occurrences.pt',
              permission=Public)
def view_occurrences(self, request):
    """ View all occurrences of all events. """

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
        'title': _('Events'),
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


@TownApp.view(model=OccurrenceCollection, name='csv', permission=Public)
def csv_export_occurences(self, request):
    """ Returns all occurrence as csv. """

    session = request.app.session()

    # requires postgres >= 9.3
    events = session.query(
        Occurrence.title,
        Occurrence.location,
        func.array_to_string(func.akeys(Occurrence._tags), ','),
        func.to_char(Occurrence.start, 'YYYY-MM-DD"T"HH24:MI:SS"Z"'),
        func.to_char(Occurrence.end, 'YYYY-MM-DD"T"HH24:MI:SS"Z"'),
        Occurrence.timezone,
        func.json_extract_path_text(
            func.cast(Event.content, JSON), 'description'
        )
    )
    events = events.outerjoin(Event)
    events = events.filter(
        Occurrence.start >= replace_timezone(as_datetime(date.today()), 'UTC')
    )
    events = events.order_by(Occurrence.start)

    output = StringIO()
    csv_writer = writer(output)
    csv_writer.writerow((
        'title',
        'location',
        'tags',
        'start',
        'end',
        'timezone',
        'description'
    ))
    writer(output).writerows(events)
    output.seek(0)

    return Response(
        output.read(),
        content_type='text/csv',
        content_disposition='inline; filename=events.csv'
    )
