""" The onegov org collection of images uploaded to the site. """
from __future__ import annotations

from collections import defaultdict
from datetime import date
from markupsafe import Markup
from morepath import redirect
from morepath.request import Response
from onegov.core.security import Public, Private, Secret
from onegov.core.utils import linkify, normalize_for_url
from onegov.event import Occurrence, OccurrenceCollection
from onegov.form import as_internal_id
from onegov.form.errors import (InvalidFormSyntax, MixedTypeError,
                                DuplicateLabelError)
from onegov.org import _, OrgApp
from onegov.org.elements import Link
from onegov.core.elements import Link as CoreLink
from onegov.org.forms import ExportForm, EventImportForm
from onegov.org.forms.event import EventConfigurationForm
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
    empty = ()

    radio_fields = {
        f.id for f in request.app.org.event_filter_fields if f.type == 'radio'
    }

    def get_count(keyword: str, value: str) -> int:
        return keyword_counts.get(keyword, {}).get(value, 0)

    def link_title(field_id: str, value: str) -> str:
        count = keyword_counts.get(field_id, {}).get(value, 0)
        return f'{value} ({count})'

    for keyword, title, values in self.available_filters(sort_choices=False):
        filters.append(Filter(title=title, tags=tuple(
            CoreLink(
                text=link_title(keyword, value),
                active=value in self.filter_keywords.get(keyword, empty),
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
        )))

    return filters


def keyword_count(
    request: OrgRequest,
    collection: OccurrenceCollection
) -> dict[str, dict[str, int]]:

    self = collection

    filter_config = request.app.org.event_filter_configuration
    keywords = tuple(
        as_internal_id(keyword)
        for keyword in filter_config.get('keywords', set())
    )

    fields = {
        field.id: field
        for field in request.app.org.event_filter_fields
        if field.id in keywords
    }

    counts: dict[str, dict[str, int]] = {}

    # NOTE: The counting can get incredibly expensive with many entries
    #       so we should skip it when we know we can skip it
    if not fields:
        return counts

    # FIXME: This is incredibly slow. We need to think of a better way.
    for model in self.without_keywords_and_tags().query():
        if not request.is_visible(model):
            continue

        for keyword, values in model.filter_keywords.items() if (
                model.filter_keywords) else ():
            if keyword in fields:
                if not isinstance(values, list):
                    values = [values]

                for value in values:
                    f_count = counts.setdefault(keyword, defaultdict(int))
                    f_count[value] += 1

    return counts


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

        keyword_counts = keyword_count(request, self)
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
        'time_suffix': request.translate(_("o'clock")),
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
        'organizer': self.event.organizer,
        'organizer_email': self.event.organizer_email,
        'organizer_phone': self.event.organizer_phone,
        'external_event_url': self.event.external_event_url,
        'layout': layout,
        'occurrence': self,
        'occurrences': occurrences,
        'overview': request.class_link(OccurrenceCollection),
        'ticket': ticket,
        'title': self.title,
        'show_tags': show_tags(request),
        'show_filters': show_filters(request),
        'time_suffix': request.translate(_("o'clock")),
    }


@OrgApp.form(model=OccurrenceCollection, name='edit',
             template='directory_form.pt', permission=Secret,
             form=EventConfigurationForm)
def handle_edit_event_filters(
    self: OccurrenceCollection,
    request: OrgRequest,
    form: EventConfigurationForm,
    layout: OccurrencesLayout | None = None
) -> RenderData | BaseResponse:

    try:
        if form.submitted(request):
            keywords = (form.keyword_fields.data or '').splitlines()
            request.app.org.event_filter_configuration = {
                'order': [],
                'keywords': keywords
            }
            request.app.org.event_filter_definition = form.definition.data

            request.success(_('Your changes were saved'))
            return request.redirect(request.link(self))

        elif not request.POST:
            # Store the model data on the form
            form.definition.data = request.app.org.event_filter_definition
            form.keyword_fields.data = '\r\n'.join(
                request.app.org.event_filter_configuration.get('keywords', []))

    except InvalidFormSyntax as e:
        request.warning(
            _('Syntax Error in line ${line}', mapping={'line': e.line})
        )
    except AttributeError:
        request.warning(_('Syntax error in form'))

    except MixedTypeError as e:
        request.warning(
            _('Syntax error in field ${field_name}',
              mapping={'field_name': e.field_name})
        )
    except DuplicateLabelError as e:
        request.warning(
            _('Error: Duplicate label ${label}', mapping={'label': e.label})
        )

    layout = layout or OccurrencesLayout(self, request)
    layout.include_code_editor()
    layout.breadcrumbs.append(Link(_('Edit'), '#'))
    layout.editbar_links = []

    return {
        'layout': layout,
        'title': 'Edit Event Filter Configuration',
        'form': form,
        'form_width': 'large',
        'migration': None,
        'model': self,
        'error': None,
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


@OrgApp.json(model=OccurrenceCollection, name='json', permission=Public)
def json_export_occurences(
    self: OccurrenceCollection,
    request: OrgRequest
) -> JSON_ro:
    """ Returns the occurrences as JSON.

    This is used for the senantis.dir.eventsportlet.

    """

    @request.after
    def cors(response: BaseResponse) -> None:
        response.headers.add('Access-Control-Allow-Origin', '*')

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
