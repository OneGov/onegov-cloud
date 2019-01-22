""" The onegov org collection of images uploaded to the site. """

from collections import OrderedDict
from datetime import date
from morepath.request import Response
from onegov.core.security import Public, Private
from onegov.core.utils import linkify, normalize_for_url
from onegov.event import Occurrence, OccurrenceCollection
from onegov.org import _, OrgApp
from onegov.org.elements import Link
from onegov.org.forms import ExportForm
from onegov.org.layout import OccurrenceLayout, OccurrencesLayout
from onegov.ticket import TicketCollection
from sedate import as_datetime, replace_timezone
from sqlalchemy.orm import joinedload


@OrgApp.html(model=OccurrenceCollection, template='occurrences.pt',
             permission=Public)
def view_occurrences(self, request):
    """ View all occurrences of all events. """

    layout = OccurrencesLayout(self, request)

    translated_tags = [
        (tag, request.translate(_(tag))) for tag in self.used_tags
    ]
    translated_tags.sort(key=lambda i: i[1])

    tags = [
        Link(
            text=translation,
            url=request.link(self.for_filter(tag=tag)),
            active=tag in self.tags and 'active' or ''
        ) for tag, translation in translated_tags
    ]

    locations = [
        Link(
            text=location,
            url=request.link(self.for_filter(location=location)),
            active=location in self.locations and 'active' or ''
        ) for location in sorted(
            request.app.org.event_locations,
            key=lambda l: normalize_for_url(l)
        )
    ]

    ranges = [
        Link(
            text=_("All"),
            url=request.link(
                self.for_filter(range=range, start=None, end=None)
            ),
            active=(
                not self.range and not self.start and not self.end
            ) and 'active' or ''
        )
    ] + [
        Link(
            text=translation,
            url=request.link(
                self.for_filter(range=range, start=None, end=None)
            ),
            active=range == self.range and 'active' or ''
        ) for range, translation in (
            ('today', _("Today")),
            ('tomorrow', _("Tomorrow")),
            ('weekend', _("This weekend")),
            ('week', _("This week")),
            ('month', _("This month")),
        )
    ]

    return {
        'active_tags': self.tags,
        'add_link': request.link(self, name='new'),
        'date_placeholder': date.today().isoformat(),
        'end': self.end.isoformat() if self.end else '',
        'layout': layout,
        'occurrences': self.batch,
        'start': self.start.isoformat() if self.start else '',
        'ranges': ranges,
        'tags': tags,
        'locations': locations,
        'title': _('Events'),
    }


@OrgApp.html(model=Occurrence, template='occurrence.pt', permission=Public)
def view_occurrence(self, request):
    """ View a single occurrence of an event. """

    layout = OccurrenceLayout(self, request)
    today = replace_timezone(as_datetime(date.today()), self.timezone)
    occurrences = self.event.occurrence_dates(localize=True)
    occurrences = list(filter(lambda x: x >= today, occurrences))
    description = linkify(self.event.description).replace('\n', '<br>')
    session = request.session
    ticket = TicketCollection(session).by_handler_id(self.event.id.hex)

    return {
        'description': description,
        'organizer': self.event.organizer,
        'layout': layout,
        'occurrence': self,
        'occurrences': occurrences,
        'ticket': ticket,
        'title': self.title,
    }


@OrgApp.view(model=Occurrence, name='ical', permission=Public)
def ical_export_occurence(self, request):
    """ Returns the occurrence as ics. """

    return Response(
        self.as_ical(url=request.link(self)),
        content_type='text/calendar',
        content_disposition='inline; filename=calendar.ics'
    )


@OrgApp.view(model=OccurrenceCollection, name='ical', permission=Public)
def ical_export_occurences(self, request):
    """ Returns the occurrences as ics. """

    return Response(
        self.as_ical(request),
        content_type='text/calendar',
        content_disposition='inline; filename=calendar.ics'
    )


@OrgApp.form(model=OccurrenceCollection, name='export', permission=Private,
             form=ExportForm, template='export.pt')
def export_occurrences(self, request, form):
    """ Export the occurrences in various formats. """

    layout = OccurrencesLayout(self, request)
    layout.breadcrumbs.append(Link(_("Export"), '#'))
    layout.editbar_links = None

    if form.submitted(request):
        results = run_export(
            request,
            layout.export_formatter(form.format)
        )

        return form.as_export_response(results, title=request.translate(_(
            "Events"
        )))

    return {
        'layout': layout,
        'title': _("Event Export"),
        'form': form,
        'explanation': _("Exports all future events.")
    }


def run_export(request, formatter):
    occasions = OccurrenceCollection(request.session, outdated=False)

    query = occasions.query()
    query = query.options(joinedload(Occurrence.event))
    query = query.order_by(Occurrence.start)

    attributes = (
        'title', 'location', 'event.organizer', 'tags',
        'start', 'end', 'event.description'
    )

    def get(obj, attr):

        if attr == 'tags':
            return [request.translate(_(tag)) for tag in obj.tags]

        for a in attr.split('.'):
            obj = value = getattr(obj, a)

        return value

    return [
        OrderedDict(
            (attr, formatter(get(occasion, attr))) for attr in attributes)
        for occasion in query.all()
    ]


@OrgApp.json(model=OccurrenceCollection, name='json', permission=Public)
def json_export_occurences(self, request):
    """ Returns the occurrences as JSON.

    This is used for the senantis.dir.eventsportlet.

    """

    @request.after
    def cors(response):
        response.headers.add('Access-Control-Allow-Origin', '*')

    query = self.for_filter(
        tags=request.params.getall('cat1'),
        locations=request.params.getall('cat2')
    ).query()

    limit = request.params.get('max')
    if limit and limit.isdigit():
        query = query.limit(int(limit))

    return [
        {
            'start': occurrence.start.isoformat(),
            'title': occurrence.title,
            'url': request.link(occurrence),
        } for occurrence in query
    ]
