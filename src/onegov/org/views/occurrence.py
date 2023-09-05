""" The onegov org collection of images uploaded to the site. """
from collections import namedtuple, defaultdict
from datetime import date
from morepath import redirect
from morepath.request import Response
from onegov.core.security import Public, Private, Secret
from onegov.core.utils import linkify, normalize_for_url
from onegov.event import Occurrence, OccurrenceCollection
from onegov.event.models.event_filter import EventFilter
from onegov.form import as_internal_id
from onegov.form.errors import InvalidFormSyntax, MixedTypeError, \
    DuplicateLabelError
from onegov.org import _, OrgApp
from onegov.winterthur import WinterthurApp
from onegov.org.elements import Link
from onegov.org.forms import ExportForm, EventImportForm
from onegov.org.forms.event import EventConfigurationForm
from onegov.org.layout import OccurrenceLayout, OccurrencesLayout
from onegov.ticket import TicketCollection
from sedate import as_datetime, replace_timezone


def get_filters(request, self, keyword_counts=None, view_name=None):
    from onegov.core.elements import Link

    Filter = namedtuple('Filter', ('title', 'tags'))
    filters = []
    empty = tuple()

    radio_fields = set(
        f.id for f in self.event_config.fields if f.type == 'radio'
    )

    def get_count(title, value):
        return keyword_counts.get(title, {}).get(value, 0)

    def link_title(field_id, value):
        if keyword_counts is None:
            return value
        count = keyword_counts.get(field_id, {}).get(value, 0)
        return f'{value} ({count})'

    for keyword, title, values in self.available_filters(sort_choices=False):
        filters.append(Filter(title=title, tags=tuple(
            Link(
                text=link_title(keyword, value),
                active=value in self.filter_keywords.get(keyword, empty),
                url=request.link(self.for_filter(
                    singular=keyword in radio_fields,
                    ** {keyword: value}
                ), name=view_name),
                rounded=keyword in radio_fields
            ) for value in values if get_count(keyword, value)
        )))

    return filters


def keyword_count(request, collection):
    self = collection

    keywords = tuple(
        as_internal_id(k) for k in (
            self.event_config.configuration.keywords.split('\r\n') or tuple()
        )
    )

    fields = {f.id: f for f in self.event_config.fields if f.id in keywords}

    counts = {}
    for model in request.exclude_invisible(self.without_keywords().query()):
        for keyword in model.filter_keywords:
            field_id, value = keyword.split(':', 1)
            if field_id in fields:
                f_count = counts.setdefault(field_id, defaultdict(int))
                f_count[value] += 1
    return counts


@OrgApp.html(model=OccurrenceCollection, template='occurrences.pt',
             permission=Public)
def view_occurrences(self, request, layout=None):
    """ View all occurrences of all events. """

    layout = layout or OccurrencesLayout(self, request)

    translated_tags = [
        (tag, request.translate(_(tag))) for tag in self.used_tags
    ]
    translated_tags.sort(key=lambda i: i[1])

    filters = None
    tags = None

    if isinstance(request.app, WinterthurApp) and self.event_config:
        keyword_counts = keyword_count(request, self)
        filters = get_filters(request, self, keyword_counts)
    else:
        tags = [
            Link(
                text=translation + f' ({self.tag_counts[tag]})',
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
            ('past', _("Past events")),
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
        'filters': filters,
        'locations': locations,
        'title': _('Events'),
        'search_widget': self.search_widget,
        'winti': isinstance(request.app, WinterthurApp),
    }


@OrgApp.html(model=Occurrence, template='occurrence.pt', permission=Public)
def view_occurrence(self, request, layout=None):
    """ View a single occurrence of an event. """

    layout = layout or OccurrenceLayout(self, request)
    today = replace_timezone(as_datetime(date.today()), self.timezone)
    occurrences = self.event.occurrence_dates(localize=True)
    occurrences = list(filter(lambda x: x >= today, occurrences))
    description = linkify(self.event.description).replace('\n', '<br>')
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
        'winti': isinstance(request.app, WinterthurApp),
    }


@OrgApp.form(model=OccurrenceCollection, name='edit',
             template='directory_form.pt', permission=Secret,
             form=EventConfigurationForm)
def handle_edit_event_filters(self, request, form, layout=None):
    try:
        if form.submitted(request):
            if self.session.query(EventFilter).count():
                # update existing event configuration
                event_filter = self.event_config
                event_filter.update(form.structure.data,
                                    form.keyword_fields.data)
            else:
                # add new event configuration
                event_filter = EventFilter()
                event_filter.update(form.structure.data,
                                    form.keyword_fields.data)
                self.session.add(event_filter)

            self.session.flush()

            form.populate_obj(event_filter)
            request.success(_("Your changes were saved"))
            return request.redirect(request.link(self))

        elif not request.POST:
            event_filter = self.session.query(EventFilter).first()
            form.process(obj=event_filter)

    except InvalidFormSyntax as e:
        request.warning(
            _("Syntax Error in line ${line}", mapping={'line': e.line})
        )
    except AttributeError:
        request.warning(_("Syntax error in form"))

    except MixedTypeError as e:
        request.warning(
            _("Syntax error in field ${field_name}",
              mapping={'field_name': e.field_name})
        )
    except DuplicateLabelError as e:
        request.warning(
            _("Error: Duplicate label ${label}", mapping={'label': e.label})
        )

    layout = layout or OccurrencesLayout(self, request)
    layout.include_code_editor()
    layout.breadcrumbs.append(Link(_("Edit"), '#'))
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


@OrgApp.form(model=OccurrenceCollection, name='export', permission=Public,
             form=ExportForm, template='export.pt')
def export_occurrences(self, request, form, layout=None):
    """ Export the occurrences in various formats. """

    layout = layout or OccurrencesLayout(self, request)
    layout.breadcrumbs.append(Link(_("Export"), '#'))
    layout.editbar_links = None

    if form.submitted(request):
        import_form = EventImportForm()
        import_form.request = request
        results = import_form.run_export()

        return form.as_export_response(results, title=request.translate(_(
            "Events"
        )))

    return {
        'layout': layout,
        'title': _("Event Export"),
        'form': form,
        'explanation': _("Exports all future events.")
    }


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


@OrgApp.view(model=OccurrenceCollection, name='xml', permission=Public)
def xml_export_all_occurrences(self, request):
    """
    Returns events as xml.
    Url for xml view: ../events/xml

    """
    collection = OccurrenceCollection(request.session)
    return Response(
        collection.as_xml(),
        content_type='text/xml',
        content_disposition='inline; filename=occurrences.xml'
    )


@OrgApp.form(
    model=OccurrenceCollection,
    name='import',
    template='form.pt',
    form=EventImportForm,
    permission=Private
)
def import_occurrences(self, request, form, layout=None):

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
