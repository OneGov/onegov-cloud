""" The onegov org collection of images uploaded to the site. """
from __future__ import annotations

from datetime import date
from markupsafe import Markup
from morepath import redirect
from morepath.request import Response
from onegov.core.security import Public, Private
from onegov.core.utils import linkify, normalize_for_url
from onegov.event import Occurrence, OccurrenceCollection
from onegov.org import _, OrgApp
from onegov.org.elements import Link
from onegov.core.elements import Link as CoreLink
from onegov.org.forms import ExportForm, EventImportForm
from onegov.org.layout import OccurrenceLayout, OccurrencesLayout
from onegov.org.views.utils import show_tags, show_filters
from onegov.ticket import TicketCollection
from operator import itemgetter
from sedate import as_datetime, replace_timezone


from typing import NamedTuple, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Mapping
    from onegov.core.types import JSON_ro, RenderData
    from onegov.event.collections.occurrences import DateRange
    from onegov.org.request import OrgRequest
    from webob import Response as BaseResponse


class Filter(NamedTuple):
    title: str
    tags: tuple[CoreLink, ...]


def get_filters(
    request: OrgRequest,
    self: OccurrenceCollection,
    keyword_counts: Mapping[str, Mapping[str, int]],
    view_name: str = ''
) -> list[Filter]:

    filters = []

    radio_fields = {
        f_id
        for f_id, f in request.app.org.event_filter_fields.items()
        if f.type == 'radio'
    }

    def get_count(keyword: str, value: str) -> int:
        return keyword_counts.get(keyword, {}).get(value, 0)

    def link_title(field_id: str, value: str) -> str:
        count = keyword_counts.get(field_id, {}).get(value, 0)
        return f'{value} ({count})'

    for keyword, title, values in self.available_filters(sort_choices=False):
        selected = self.filter_keywords.getall(keyword)
        options = tuple(
            CoreLink(
                text=link_title(keyword, value),
                active=value in selected,
                url=request.link(
                    self.for_toggled_keyword_value(
                        keyword,
                        value,
                        singular=keyword in radio_fields,
                    ),
                    name=view_name
                ),
                rounded=keyword in radio_fields
            ) for value in values if get_count(keyword, value)
        )
        if not options:
            continue
        filters.append(Filter(title=title, tags=options))

    return filters


@OrgApp.html(model=OccurrenceCollection, template='occurrences.pt',
             permission=Public)
def view_occurrences(
    self: OccurrenceCollection,
    request: OrgRequest,
    layout: OccurrencesLayout | None = None
) -> RenderData:
    """ View all occurrences of all events. """

    filters = None
    tags = None
    filter_type = request.app.org.event_filter_type
    filter_config = request.app.org.event_filter_configuration

    layout = layout or OccurrencesLayout(self, request)

    custom_tags = bool(request.app.custom_event_tags)

    used_tags = sorted((
        (tag, (tag if custom_tags else request.translate(_(tag))))
        for tag in self.used_tags
    ), key=itemgetter(1))

    if (
        filter_type in ('filters', 'tags_and_filters')
        and filter_config.get('keywords', None)
    ):
        self.set_event_filter_configuration(filter_config)
        self.set_event_filter_fields(request.app.org.event_filter_fields)

        keyword_counts = self.keyword_counts()
        filters = get_filters(request, self, keyword_counts)

    if filter_type in ('tags', 'tags_and_filters'):
        tags = [
            Link(
                text=translation + f' ({self.tag_counts[tag]})',
                url=request.link(self.for_filter(tag=tag)),
                active=tag in self.tags
            ) for tag, translation in used_tags if self.tag_counts[tag]
        ]

    locations = [
        Link(
            text=location,
            url=request.link(self.for_filter(location=location)),
            active=location in self.locations
        ) for location in sorted(
            request.app.org.event_locations,
            key=lambda l: normalize_for_url(l)
        )
    ]

    range_labels: tuple[tuple[DateRange, str], ...] = (
        ('today', _('Today')),
        ('tomorrow', _('Tomorrow')),
        ('weekend', _('This weekend')),
        ('week', _('This week')),
        ('month', _('This month')),
        ('past', _('Past events')),
    )
    ranges = [
        Link(
            text=_('All'),
            url=request.link(self.for_filter(start=None, end=None)),
            active=not (self.range or self.start or self.end)
        )
    ] + [
        Link(
            text=label,
            url=request.link(
                self.for_filter(range=range, start=None, end=None)
            ),
            active=range == self.range
        ) for range, label in range_labels
    ]

    files = list(request.app.org.event_files)

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
        'files': files,
        'filters': filters,
        'locations': locations,
        'title': _('Events'),
        'search_widget': self.search_widget,
        'show_tags': show_tags(request),
        'show_filters': show_filters(request),
        'no_event_link': request.link(
            self.for_filter(range='past', start=None, end=None)
        ),
        'header_html': request.app.org.event_header_html,
        'footer_html': request.app.org.event_footer_html,
    }


@OrgApp.html(model=Occurrence, template='occurrence.pt', permission=Public)
def view_occurrence(
    self: Occurrence,
    request: OrgRequest,
    layout: OccurrenceLayout | None = None
) -> RenderData:
    """ View a single occurrence of an event. """

    layout = layout or OccurrenceLayout(self, request)
    today = replace_timezone(as_datetime(date.today()), self.timezone)
    occurrences = self.event.occurrence_dates(localize=True)
    occurrences = list(filter(lambda x: x >= today, occurrences))
    description = linkify(
        self.event.description or '').replace('\n', Markup('<br>'))
    session = request.session
    ticket = TicketCollection(session).by_handler_id(self.event.id.hex)
    framed = request.GET.get('framed')

    return {
        'description': description,
        'framed': framed,
        'filter_names': request.app.org.event_filter_names,
        'organizer': self.event.organizer,
        'organizer_email': self.event.organizer_email,
        'organizer_phone': self.event.organizer_phone,
        'external_event_url': self.event.external_event_url,
        'layout': layout,
        'occurrence': self,
        'occurrences': occurrences,
        'ticket': ticket,
        'title': self.title,
        'show_tags': show_tags(request),
        'show_filters': show_filters(request),
    }


@OrgApp.view(model=Occurrence, name='ical', permission=Public)
def ical_export_occurence(self: Occurrence, request: OrgRequest) -> Response:
    """ Returns the occurrence as ics. """

    return Response(
        self.as_ical(url=request.link(self)),
        content_type='text/calendar',
        content_disposition='inline; filename=calendar.ics'
    )


@OrgApp.view(model=OccurrenceCollection, name='ical', permission=Public)
def ical_export_occurences(
    self: OccurrenceCollection,
    request: OrgRequest
) -> Response:
    """ Returns the occurrences as ics. """

    return Response(
        self.as_ical(request),
        content_type='text/calendar',
        content_disposition='inline; filename=calendar.ics'
    )


@OrgApp.form(model=OccurrenceCollection, name='export', permission=Public,
             form=ExportForm, template='export.pt')
def export_occurrences(
    self: OccurrenceCollection,
    request: OrgRequest,
    form: ExportForm,
    layout: OccurrencesLayout | None = None
) -> RenderData | BaseResponse:
    """ Export the occurrences in various formats. """

    layout = layout or OccurrencesLayout(self, request)
    layout.breadcrumbs.append(Link(_('Export'), '#'))
    layout.editbar_links = None  # type:ignore[assignment]

    if form.submitted(request):
        import_form = EventImportForm()
        import_form.request = request
        results = import_form.run_export()

        return form.as_export_response(results, title=request.translate(_(
            'Events'
        )))

    return {
        'layout': layout,
        'title': _('Event Export'),
        'form': form,
        'explanation': _('Exports all future events.')
    }


@OrgApp.json(
    model=OccurrenceCollection,
    name='json',
    permission=Public,
    open_data=False
)
def json_export_occurrences(
    self: OccurrenceCollection,
    request: OrgRequest
) -> JSON_ro:
    """ Returns the occurrences as JSON.

    This is used for the senantis.dir.eventsportlet.

    """

    query = self.for_filter(
        tags=request.params.getall('cat1'),  # type:ignore[arg-type]
        locations=request.params.getall('cat2')  # type:ignore[arg-type]
    ).query()

    limit = request.params.get('max')
    if isinstance(limit, str) and limit.isdigit():
        query = query.limit(int(limit))

    return [
        {
            'start': occurrence.start.isoformat(),
            'title': occurrence.title,
            'url': request.link(occurrence),
        } for occurrence in query
    ]


@OrgApp.view(
    model=OccurrenceCollection,
    name='xml',
    permission=Public
)
def xml_export_all_occurrences(
    self: OccurrenceCollection,
    request: OrgRequest
) -> Response:
    """
    Returns events as xml.
    Url for xml view: ../events/xml

    """
    collection = OccurrenceCollection(request.session)
    return Response(
        collection.as_xml(),
        content_type='text/xml',
        content_disposition='inline; filename=events.xml'
    )


@OrgApp.form(
    model=OccurrenceCollection,
    name='import',
    template='form.pt',
    form=EventImportForm,
    permission=Private
)
def import_occurrences(
    self: OccurrenceCollection,
    request: OrgRequest,
    form: EventImportForm,
    layout: OccurrencesLayout | None = None
) -> RenderData | BaseResponse:

    if form.submitted(request):
        count, errors = form.run_import()
        if errors:
            request.alert(_(
                'The following line(s) contain invalid data: ${lines}',
                mapping={'lines': ', '.join(errors)}
            ))
        elif form.dry_run.data:
            request.success(_(
                '${count} events will be imported',
                mapping={'count': count}
            ))
        else:
            request.success(_(
                '${count} events imported',
                mapping={'count': count}
            ))
            return redirect(request.link(self))

    layout = layout or OccurrencesLayout(self, request)

    return {
        'layout': layout,
        'callout': _(
            'The same format as the export (XLSX) can be used for the '
            'import.'
        ),
        'title': _('Import'),
        'form': form,
        'form_width': 'large',
    }
