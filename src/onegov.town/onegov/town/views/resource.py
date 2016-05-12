import morepath
import sedate

from collections import OrderedDict, namedtuple
from datetime import datetime, timedelta
from isodate import parse_date, ISO8601Error
from itertools import groupby
from libres.db.models import Reservation
from onegov.core.orm.types import UUID
from onegov.core.security import Public, Private
from onegov.libres import ResourceCollection
from onegov.libres.models import Resource
from onegov.ticket import Ticket
from onegov.town import TownApp, _
from onegov.town import utils
from onegov.town.elements import Link
from onegov.town.forms import ResourceForm, ResourceCleanupForm
from onegov.town.layout import ResourcesLayout, ResourceLayout
from onegov.town.models.resource import DaypassResource, RoomResource
from sqlalchemy.sql.expression import cast, nullsfirst
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


@TownApp.html(model=ResourceCollection, template='resources.pt',
              permission=Public)
def view_resources(self, request):
    resources = self.query().order_by(nullsfirst(Resource.group)).all()
    resources = request.exclude_invisible(resources)
    grouped = OrderedDict()

    for group, items in groupby(resources, lambda r: r.group or _("General")):
        grouped[group] = sorted(tuple(items), key=lambda r: r.title)

    if len(grouped) == 1:
        grouped = {None: tuple(grouped.values())[0]}

    return {
        'title': _("Reservations"),
        'resources': grouped,
        'layout': ResourcesLayout(self, request)
    }


@TownApp.form(model=ResourceCollection, name='neuer-raum',
              template='form.pt', permission=Private, form=get_room_form)
def handle_new_room(self, request, form):
    return handle_new_resource(self, request, form, 'room')


@TownApp.form(model=ResourceCollection, name='neue-tageskarte',
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


@TownApp.form(model=Resource, name='bearbeiten', template='form.pt',
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


@TownApp.html(model=Resource, template='resource.pt', permission=Public)
def view_resource(self, request):
    return {
        'title': self.title,
        'resource': self,
        'layout': ResourceLayout(self, request),
        'feed': request.link(self, name='slots')
    }


@TownApp.view(model=Resource, request_method='DELETE', permission=Private)
def handle_delete_resource(self, request):

    if not self.deletable:
        raise exc.HTTPMethodNotAllowed()

    collection = ResourceCollection(request.app.libres_context)
    collection.delete(self, including_reservations=False)


@TownApp.form(model=Resource, permission=Private, name='cleanup',
              form=ResourceCleanupForm, template='resource_cleanup.pt')
def handle_cleanup_allocations(self, request, form):
    """ Removes all unused allocations between the given dates. """

    if form.submitted(request):
        start, end = form.data['start'], form.data['end']

        scheduler = self.get_scheduler(request.app.libres_context)
        count = scheduler.remove_unused_allocations(start, end)

        request.success(
            _("Successfully removed ${count} unused allocations", mapping={
                'count': count
            })
        )

        return morepath.redirect(request.link(self))

    layout = ResourceLayout(self, request)
    layout.breadcrumbs.append(Link(_("Clean up"), '#'))
    layout.editbar_links = None

    return {
        'layout': layout,
        'title': _("Clean up"),
        'form': form
    }


@TownApp.json(model=Resource, name='reservations', permission=Public)
def get_reservations(self, request):
    return [
        utils.ReservationInfo(reservation, request).as_dict() for reservation
        in self.bound_reservations(request)
    ]


def get_date(text, default):
    try:
        date = parse_date(text)
        return datetime(date.year, date.month, date.day, tzinfo=default.tzinfo)
    except (ISO8601Error, TypeError):
        return default


def get_date_range(resource, params):
    now = sedate.align_date_to_day(sedate.utcnow(), resource.timezone, 'down')
    date = sedate.replace_timezone(
        get_date(params.get('date'), now), resource.timezone)

    if resource.view == 'month':
        default_start, default_end = sedate.align_range_to_month(
            date, date, resource.timezone)
    elif resource.view == 'agendaWeek':
        default_start, default_end = sedate.align_range_to_week(
            date, date, resource.timezone)
    elif resource.view == 'agendaDay':
        default_start, default_end = sedate.align_range_to_day(
            date, date, resource.timezone)

    start = get_date(params.get('start'), default_start)
    end = get_date(params.get('end'), default_end)

    start = sedate.replace_timezone(
        datetime(start.year, start.month, start.day), resource.timezone)

    end = sedate.replace_timezone(
        datetime(end.year, end.month, end.day), resource.timezone)

    return sedate.align_range_to_day(start, end, resource.timezone)


@TownApp.html(model=Resource, permission=Private, name='belegung',
              template='resource_occupancy.pt')
def view_occupancy(self, request):

    # infer the default start/end date from the calendar view parameters
    start, end = get_date_range(self, request.params)

    query = self.scheduler.managed_reservations()
    query = query.filter(start <= Reservation.start)
    query = query.filter(Reservation.end <= end)

    query = query.join(
        Ticket, Reservation.token == cast(Ticket.handler_id, UUID))

    query = query.order_by(Reservation.start)
    query = query.order_by(Ticket.subtitle)
    query = query.filter(Reservation.status == 'approved')
    query = query.filter(Reservation.data != None)

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

    return {
        'layout': layout,
        'title': _("Occupancy"),
        'occupancy': occupancy,
        'resource': self,
        'start': sedate.to_timezone(start, self.timezone).date(),
        'end': sedate.to_timezone(end, self.timezone).date(),
        'count': count,
    }
