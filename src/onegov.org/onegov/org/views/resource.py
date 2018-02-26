import morepath
import sedate

from collections import OrderedDict, namedtuple
from datetime import datetime, timedelta
from isodate import parse_date, ISO8601Error
from itertools import groupby
from onegov.core.security import Public, Private
from onegov.form import FormSubmission
from onegov.reservation import ResourceCollection, Resource, Reservation
from onegov.org import _, OrgApp, utils
from onegov.org.elements import Link
from onegov.org.forms import (
    ResourceForm, ResourceCleanupForm, ResourceExportForm
)
from onegov.org.layout import ResourcesLayout, ResourceLayout
from onegov.org.models.resource import DaypassResource, RoomResource
from onegov.org.utils import group_by_column, keywords_first
from onegov.ticket import Ticket
from webob import exc


RESOURCE_TYPES = {
    'daypass': {
        'success': _("Added a new daypass"),
        'title': _("New daypass"),
        'class': DaypassResource
    },
    'room': {
        'success': _("Added a new room"),
        'title': _("New room"),
        'class': RoomResource
    }
}


def get_daypass_form(self, request):
    return get_resource_form(self, request, 'daypass')


def get_room_form(self, request):
    return get_resource_form(self, request, 'room')


def get_resource_form(self, request, type=None):
    if isinstance(self, ResourceCollection):
        assert type is not None
        model = RESOURCE_TYPES[type]['class']()
    else:
        model = self

    return model.with_content_extensions(ResourceForm, request)


@OrgApp.html(model=ResourceCollection, template='resources.pt',
             permission=Public)
def view_resources(self, request):
    return {
        'title': _("Reservations"),
        'resources': group_by_column(
            request=request,
            query=self.query(),
            group_column=Resource.group,
            sort_column=Resource.title
        ),
        'layout': ResourcesLayout(self, request)
    }


@OrgApp.json(model=ResourceCollection, permission=Public, name='json')
def view_resources_json(self, request):

    def transform(resource):
        return {
            'name': resource.name,
            'title': resource.title,
            'url': request.link(resource),
        }

    @request.after
    def cache(response):
        # only update once every minute
        response.cache_control.max_age = 60

    return group_by_column(
        request=request,
        query=self.query(),
        group_column=Resource.group,
        sort_column=Resource.title,
        transform=transform,
        default_group=request.translate(_("Reservations"))
    )


@OrgApp.form(model=ResourceCollection, name='new-room',
             template='form.pt', permission=Private, form=get_room_form)
def handle_new_room(self, request, form):
    return handle_new_resource(self, request, form, 'room')


@OrgApp.form(model=ResourceCollection, name='new-daypass',
             template='form.pt', permission=Private, form=get_daypass_form)
def handle_new_daypass(self, request, form):
    return handle_new_resource(self, request, form, 'daypass')


def handle_new_resource(self, request, form, type):
    if form.submitted(request):

        resource = self.add(
            title=form.title.data, type=type, timezone='Europe/Zurich'
        )
        form.populate_obj(resource)

        request.success(RESOURCE_TYPES[type]['success'])
        return morepath.redirect(request.link(resource))

    layout = ResourcesLayout(self, request)
    layout.include_editor()
    layout.include_code_editor()
    layout.breadcrumbs.append(Link(RESOURCE_TYPES[type]['title'], '#'))

    return {
        'layout': layout,
        'title': _(RESOURCE_TYPES[type]['title']),
        'form': form,
        'form_width': 'large'
    }


@OrgApp.form(model=Resource, name='edit', template='form.pt',
             permission=Private, form=get_resource_form)
def handle_edit_resource(self, request, form):
    if form.submitted(request):
        form.populate_obj(self)

        request.success(_("Your changes were saved"))
        return morepath.redirect(request.link(self))

    elif not request.POST:
        form.process(obj=self)

    layout = ResourceLayout(self, request)
    layout.include_editor()
    layout.include_code_editor()
    layout.breadcrumbs.append(Link(_("Edit"), '#'))

    return {
        'layout': layout,
        'title': self.title,
        'form': form,
        'form_width': 'large'
    }


@OrgApp.html(model=Resource, template='resource.pt', permission=Public)
def view_resource(self, request):
    return {
        'title': self.title,
        'resource': self,
        'layout': ResourceLayout(self, request),
        'feed': request.link(self, name='slots'),
        'resources_url': request.class_link(ResourceCollection, name='json')
    }


@OrgApp.view(model=Resource, request_method='DELETE', permission=Private)
def handle_delete_resource(self, request):

    request.assert_valid_csrf_token()

    if not self.deletable:
        raise exc.HTTPMethodNotAllowed()

    collection = ResourceCollection(request.app.libres_context)
    collection.delete(self, including_reservations=False)


@OrgApp.form(model=Resource, permission=Private, name='cleanup',
             form=ResourceCleanupForm, template='resource_cleanup.pt')
def handle_cleanup_allocations(self, request, form):
    """ Removes all unused allocations between the given dates. """

    if form.submitted(request):
        start, end = form.data['start'], form.data['end']
        count = self.scheduler.remove_unused_allocations(start, end)

        request.success(
            _("Successfully removed ${count} unused allocations", mapping={
                'count': count
            })
        )

        return morepath.redirect(request.link(self))

    if request.method == 'GET':
        form.start.data, form.end.data = get_date_range(self, request.params)

    layout = ResourceLayout(self, request)
    layout.breadcrumbs.append(Link(_("Clean up"), '#'))
    layout.editbar_links = None

    return {
        'layout': layout,
        'title': _("Clean up"),
        'form': form
    }


def predict_next_reservation(resource, request, reservations):

    prediction = utils.predict_next_daterange(
        tuple((r.display_start(), r.display_end()) for r in reservations)
    )

    if not prediction:
        return None

    allocation = resource.scheduler.allocations_in_range(*prediction).first()

    if not allocation:
        return None

    whole_day = sedate.is_whole_day(*prediction, timezone=resource.timezone)
    quota = utils.predict_next_value(tuple(r.quota for r in reservations)) or 1

    if whole_day:
        time = request.translate(_("Whole day"))
    else:
        time = utils.render_time_range(*prediction)

    return {
        'url': request.link(allocation, name='reserve'),
        'start': prediction[0].isoformat(),
        'end': prediction[1].isoformat(),
        'quota': quota,
        'wholeDay': whole_day,
        'time': time
    }


@OrgApp.json(model=Resource, name='reservations', permission=Public)
def get_reservations(self, request):

    reservations = tuple(self.bound_reservations(request))
    prediction = predict_next_reservation(self, request, reservations)

    return {
        'reservations': [
            utils.ReservationInfo(self, reservation, request).as_dict()
            for reservation in reservations
        ],
        'prediction': prediction
    }


def get_date(text, default):
    try:
        date = parse_date(text)
        return datetime(date.year, date.month, date.day, tzinfo=default.tzinfo)
    except (ISO8601Error, TypeError):
        return default


def get_date_range(resource, params):
    default_start, default_end = resource.calendar_date_range

    start = get_date(params.get('start'), default_start)
    end = get_date(params.get('end'), default_end)

    start = sedate.replace_timezone(
        datetime(start.year, start.month, start.day), resource.timezone)

    end = sedate.replace_timezone(
        datetime(end.year, end.month, end.day), resource.timezone)

    if end < start:
        start = end

    return sedate.align_range_to_day(start, end, resource.timezone)


@OrgApp.html(model=Resource, permission=Private, name='occupancy',
             template='resource_occupancy.pt')
def view_occupancy(self, request):

    # infer the default start/end date from the calendar view parameters
    start, end = get_date_range(self, request.params)

    query = self.reservations_with_tickets_query(start, end)
    query = query.with_entities(
        Reservation.start, Reservation.end, Reservation.quota,
        Ticket.subtitle, Ticket.id
    )

    def group_key(record):
        return sedate.to_timezone(record[0], self.timezone).date()

    occupancy = OrderedDict()
    grouped = groupby(query.all(), group_key)
    Entry = namedtuple('Entry', ('start', 'end', 'title', 'quota', 'url'))
    count = 0

    for date, records in grouped:
        occupancy[date] = tuple(
            Entry(
                start=sedate.to_timezone(r[0], self.timezone),
                end=sedate.to_timezone(
                    r[1] + timedelta(microseconds=1), self.timezone),
                quota=r[2],
                title=r[3],
                url=request.class_link(Ticket, {
                    'handler_code': 'RSV',
                    'id': r[4]
                })
            ) for r in records
        )
        count += len(occupancy[date])

    layout = ResourceLayout(self, request)
    layout.breadcrumbs.append(Link(_("Occupancy"), '#'))
    layout.editbar_links = None

    utilisation = 100 - self.scheduler.queries.availability_by_range(
        start, end, (self.id, )
    )

    return {
        'layout': layout,
        'title': _("Occupancy"),
        'occupancy': occupancy,
        'resource': self,
        'start': sedate.to_timezone(start, self.timezone).date(),
        'end': sedate.to_timezone(end, self.timezone).date(),
        'count': count,
        'utilisation': utilisation
    }


@OrgApp.form(model=Resource, permission=Private, name='export',
             template='export.pt', form=ResourceExportForm)
def view_export(self, request, form):

    layout = ResourceLayout(self, request)
    layout.breadcrumbs.append(Link(_("Occupancy"), '#'))
    layout.editbar_links = None

    # XXX this could be turned into a redirect to a GET view, which would
    # make it easier for scripts to get this data, but since we don't have
    # a good API story anyway we don't have spend to much energy on it here
    # - instead we should do this in a comprehensive fashion
    if form.submitted(request):
        field_order, results = run_export(
            resource=self,
            start=form.data['start'],
            end=form.data['end'],
            nested=form.format == 'json',
            formatter=layout.export_formatter(form.format)
        )

        return form.as_export_response(results, self.title, key=field_order)

    if request.method == 'GET':
        form.start.data, form.end.data = get_date_range(self, request.params)

    return {
        'layout': layout,
        'title': _("Export"),
        'form': form,
        'explanation': _("Exports the reservations of the given date range.")
    }


def run_export(resource, start, end, nested, formatter):
    start = sedate.replace_timezone(
        datetime(start.year, start.month, start.day),
        resource.timezone
    )
    end = sedate.replace_timezone(
        datetime(end.year, end.month, end.day),
        resource.timezone
    )

    start, end = sedate.align_range_to_day(start, end, resource.timezone)

    query = resource.reservations_with_tickets_query(start, end)
    query = query.join(FormSubmission, Reservation.token == FormSubmission.id)
    query = query.with_entities(
        Reservation.start,
        Reservation.end,
        Reservation.quota,
        Reservation.email,
        Ticket.number,
        Ticket.subtitle,
        FormSubmission.data,
    )

    results = []
    keywords = ('start', 'end', 'quota', 'email', 'ticket', 'title')

    for record in query:
        result = OrderedDict()

        start = sedate.to_timezone(record[0], resource.timezone)
        end = sedate.to_timezone(record[1], resource.timezone)
        end += timedelta(microseconds=1)

        result['start'] = formatter(start)
        result['end'] = formatter(end)
        result['quota'] = formatter(record[2])
        result['email'] = formatter(record[3])
        result['ticket'] = formatter(record[4])
        result['title'] = formatter(record[5])

        if nested:
            result['form'] = {
                k: formatter(v)
                for k, v in record[6].items()
            }
        else:
            for key, value in record[6].items():
                result['form_' + key] = formatter(value)

        results.append(result)

    return keywords_first(keywords), results
