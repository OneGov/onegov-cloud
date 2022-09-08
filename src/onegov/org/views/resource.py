import icalendar
import morepath
import sedate
import collections

from collections import OrderedDict, namedtuple
from datetime import datetime, time, timedelta
from isodate import parse_date, ISO8601Error
from itertools import groupby, islice
from morepath.request import Response
from onegov.core.security import Public, Private, Personal
from onegov.core.utils import module_path, normalize_for_url
from onegov.core.orm import as_selectable_from_path
from onegov.form import FormSubmission
from onegov.org.cli import close_ticket
from onegov.org.forms.resource import AllResourcesExportForm
from onegov.reservation import ResourceCollection, Resource, Reservation
from onegov.org import _, OrgApp, utils
from onegov.org.elements import Link
from onegov.org.forms import (
    FindYourSpotForm, ResourceForm, ResourceCleanupForm, ResourceExportForm
)
from onegov.org.layout import (
    FindYourSpotLayout, ResourcesLayout, ResourceLayout
)
from onegov.org.models.resource import (
    DaypassResource, FindYourSpotCollection, RoomResource, ItemResource
)
from onegov.org.models.external_link import ExternalLinkCollection, \
    ExternalLink
from onegov.org.utils import group_by_column, keywords_first
from onegov.ticket import Ticket, TicketCollection
from operator import attrgetter, itemgetter
from purl import URL
from sedate import utcnow, standardize_date
from sqlalchemy import and_, select
from sqlalchemy.orm import object_session
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
    },
    'daily-item': {
        'success': _("Added a new item"),
        'title': _("New Item"),
        'class': ItemResource
    }
}


def combine_grouped(items, external_links, sort=None):
    for key, values in external_links.items():
        if key not in items:
            items[key] = values
        else:
            if sort:
                items[key] = sorted(items[key] + values, key=sort)
            else:
                items[key] += values
    return collections.OrderedDict(sorted(items.items()))


def get_daypass_form(self, request):
    return get_resource_form(self, request, 'daypass')


def get_room_form(self, request):
    return get_resource_form(self, request, 'room')


def get_item_form(self, request):
    return get_resource_form(self, request, 'daily-item')


def get_resource_form(self, request, type=None):
    if isinstance(self, ResourceCollection):
        assert type is not None
        model = RESOURCE_TYPES[type]['class']()
    else:
        model = self

    return model.with_content_extensions(ResourceForm, request)


@OrgApp.html(model=ResourceCollection, template='resources.pt',
             permission=Public)
def view_resources(self, request, layout=None):
    default_group = request.translate(_("General"))
    resources = group_by_column(
        request=request,
        query=self.query(),
        default_group=default_group,
        group_column=Resource.group,
        sort_column=Resource.title
    )

    def contains_at_least_one_room(resources):
        for resource in resources:
            if isinstance(resource, Resource):
                if resource.type == 'room':
                    return True
        return False

    ext_resources = group_by_column(
        request,
        query=ExternalLinkCollection.for_model(
            request.session, ResourceCollection
        ).query(),
        group_column=ExternalLink.group,
        sort_column=ExternalLink.order
    )

    grouped = combine_grouped(
        resources, ext_resources, sort=lambda x: x.title
    )

    for group, entries in grouped.items():
        # don't include find-your-spot link for categories with
        # no rooms
        if not contains_at_least_one_room(entries):
            continue
        entries.insert(0, FindYourSpotCollection(
            request.app.libres_context,
            group=None if group == default_group else group
        ))

    def link_func(model):
        if isinstance(model, ExternalLink):
            return model.url
        return request.link(model)

    def edit_link(model):
        if isinstance(model, ExternalLink) and request.is_manager:
            title = request.translate(_("Edit resource"))
            to = request.class_link(ResourceCollection)
            return request.link(
                model,
                query_params={'title': title, 'to': to},
                name='edit'
            )

    def lead_func(model):
        lead = model.meta.get('lead')
        if not lead:
            lead = ''
        lead = layout.linkify(lead)
        return lead

    return {
        'title': _("Reservations"),
        'resources': grouped,
        'layout': layout or ResourcesLayout(self, request),
        'link_func': link_func,
        'edit_link': edit_link,
        'lead_func': lead_func,
    }


@OrgApp.form(model=FindYourSpotCollection, template='find_your_spot.pt',
             permission=Public, form=FindYourSpotForm)
def view_find_your_spot(self, request, form, layout=None):
    # HACK: Focus results
    form.action += '#results'
    room_slots = None
    rooms = sorted(
        request.exclude_invisible(self.query()),
        key=attrgetter('title')
    )
    if not rooms:
        # we'll treat categories without rooms as non-existant
        raise exc.HTTPNotFound()

    form.apply_rooms(rooms)
    if form.submitted(request):
        if form.rooms:
            # filter rooms according to the form selection
            rooms = [room for room in rooms if room.id in form.rooms.data]

        start_time = form.start_time.data
        end_time = form.end_time.data
        start = datetime.combine(form.start.data, start_time)
        end = datetime.combine(form.end.data, end_time)

        def included_dates():
            # yields all the dates that should be part of our result set
            current = start.date()
            max_date = end.date()
            while current <= max_date:
                if not form.is_excluded(current):
                    yield current
                current += timedelta(days=1)

        # initialize the room slots with all the included dates and rooms
        room_slots = {
            d: {room.id: [] for room in rooms}
            for d in included_dates()
        }
        for room in rooms:
            room.bind_to_libres_context(request.app.libres_context)
            for allocation in request.exclude_invisible(
                    room.scheduler.search_allocations(
                        start, end, days=form.weekdays.data, strict=True)):

                date = allocation.display_start().date()
                if date not in room_slots:
                    continue

                slots = room_slots[date][room.id]
                target_start, target_end = sedate.get_date_range(
                    allocation.display_start(),
                    start_time,
                    end_time
                )

                if not allocation.partly_available:
                    quota_left = allocation.quota_left
                    slots.append(utils.FindYourSpotEventInfo(
                        allocation,
                        None,  # won't be displayed
                        quota_left / allocation.quota,
                        quota_left,
                        request
                    ))
                    continue
                elif target_start >= target_end:
                    # this can happen for non-existent times, we
                    # just treat it as not available in this case
                    continue

                free = allocation.free_slots(target_start, target_end)
                if not free:
                    continue

                # FIXME: The availability calculation should probably be
                #        normalized when a daylight savings shift occurs
                target_range = (target_end - target_start)
                slot_start, slot_end = free[0]
                slot_end += time.resolution
                for next_slot_start, next_slot_end in islice(free, 1, None):
                    if slot_end != next_slot_start:
                        availability = (slot_end - slot_start) / target_range
                        availability *= 100.0
                        slots.append(utils.FindYourSpotEventInfo(
                            allocation,
                            (sedate.to_timezone(
                                slot_start, allocation.timezone),
                                sedate.to_timezone(
                                    slot_end, allocation.timezone)),
                            availability,
                            1 if availability >= 5.0 else 0,
                            request
                        ))
                        slot_start = next_slot_start

                    # expand slot end
                    slot_end = next_slot_end + time.resolution

                # add final slot
                availability = (slot_end - slot_start) / target_range
                availability *= 100.0
                slots.append(utils.FindYourSpotEventInfo(
                    allocation,
                    (sedate.to_timezone(slot_start, allocation.timezone),
                     sedate.to_timezone(slot_end, allocation.timezone)),
                    availability,
                    1 if availability >= 5.0 else 0,
                    request
                ))

    if room_slots:
        request.include('reservationlist')

    return {
        'title': _("Find Your Spot"),
        'form': form,
        'rooms': rooms,
        'room_slots': room_slots,
        'layout': layout or FindYourSpotLayout(self, request)
    }


@OrgApp.json(model=FindYourSpotCollection, name='reservations',
             permission=Public)
def get_find_your_spot_reservations(self, request):
    return {
        'reservations': sorted(
            (utils.ReservationInfo(resource, reservation, request).as_dict()
                for resource in request.exclude_invisible(self.query())
                for reservation in resource.bound_reservations(request)),
            key=itemgetter('date')
        ),
        # no predictions in the list
        'prediction': None
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
def handle_new_room(self, request, form, layout=None):
    return handle_new_resource(self, request, form, 'room', layout)


@OrgApp.form(model=ResourceCollection, name='new-daypass',
             template='form.pt', permission=Private, form=get_daypass_form)
def handle_new_daypass(self, request, form, layout=None):
    return handle_new_resource(self, request, form, 'daypass', layout)


@OrgApp.form(model=ResourceCollection, name='new-daily-item',
             template='form.pt', permission=Private, form=get_item_form)
def handle_new_resource_item(self, request, form, layout=None):
    return handle_new_resource(self, request, form, 'daily-item', layout)


def handle_new_resource(self, request, form, type, layout=None):
    if form.submitted(request):

        resource = self.add(
            title=form.title.data, type=type, timezone='Europe/Zurich'
        )
        form.populate_obj(resource)

        request.success(RESOURCE_TYPES[type]['success'])
        return morepath.redirect(request.link(resource))

    layout = layout or ResourcesLayout(self, request)
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
def handle_edit_resource(self, request, form, layout=None):
    if form.submitted(request):
        form.populate_obj(self)

        request.success(_("Your changes were saved"))
        return morepath.redirect(request.link(self))

    elif not request.POST:
        form.process(obj=self)

    layout = layout or ResourceLayout(self, request)
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
def view_resource(self, request, layout=None):
    return {
        'title': self.title,
        'resource': self,
        'layout': layout or ResourceLayout(self, request),
        'feed': request.link(self, name='slots'),
        'resources_url': request.class_link(ResourceCollection, name='json')
    }


@OrgApp.view(model=Resource, request_method='DELETE', permission=Private)
def handle_delete_resource(self, request):

    request.assert_valid_csrf_token()

    if not self.deletable:
        raise exc.HTTPMethodNotAllowed()

    tickets = TicketCollection(request.session)

    def handle_reservation_tickets(reservation):
        ticket = tickets.by_handler_id(reservation.token.hex)
        if ticket:
            close_ticket(ticket, request.current_user, request)
            ticket.create_snapshot(request)

    collection = ResourceCollection(request.app.libres_context)
    collection.delete(
        self,
        including_reservations=True,
        handle_reservation=handle_reservation_tickets
    )


@OrgApp.form(model=Resource, permission=Private, name='cleanup',
             form=ResourceCleanupForm, template='resource_cleanup.pt')
def handle_cleanup_allocations(self, request, form, layout=None):
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

    layout = layout or ResourceLayout(self, request)
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


@OrgApp.html(model=Resource, permission=Personal, name='occupancy',
             template='resource_occupancy.pt')
def view_occupancy(self, request, layout=None):
    # for members check if they're actually allowed to see this
    if request.has_role('member') and not self.occupancy_is_visible_to_members:
        raise exc.HTTPForbidden()

    # infer the default start/end date from the calendar view parameters
    start, end = get_date_range(self, request.params)

    # include pending reservations
    query = self.reservations_with_tickets_query(
        start, end, exclude_pending=False)
    query = query.with_entities(
        Reservation.start, Reservation.end, Reservation.quota,
        Reservation.data, Ticket.subtitle, Ticket.id
    )

    def group_key(record):
        return sedate.to_timezone(record[0], self.timezone).date()

    occupancy = OrderedDict()
    grouped = groupby(query.all(), group_key)
    Entry = namedtuple(
        'Entry', ('start', 'end', 'title', 'quota', 'pending', 'url'))
    count = 0
    pending_count = 0

    for date, records in grouped:
        occupancy[date] = tuple(
            Entry(
                start=sedate.to_timezone(start, self.timezone),
                end=sedate.to_timezone(
                    end + timedelta(microseconds=1), self.timezone),
                quota=quota,
                title=title,
                pending=not data or not data.get('accepted'),
                url=request.class_link(Ticket, {
                    'handler_code': 'RSV',
                    'id': ticket_id
                })
            ) for start, end, quota, data, title, ticket_id in records
        )
        count += len(occupancy[date])
        pending_count += sum(1 for entry in occupancy[date] if entry.pending)

    layout = layout or ResourceLayout(self, request)
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
        'pending_count': pending_count,
        'utilisation': utilisation
    }


@OrgApp.html(model=Resource, template='resource-subscribe.pt',
             permission=Private, name='subscribe')
def view_resource_subscribe(self, request, layout=None):
    url = URL(request.link(self, 'ical'))
    url = url.scheme('webcal')

    if url.has_query_param('view'):
        url = url.remove_query_param('view')

    url = url.query_param('access-token', self.access_token)
    url = url.as_string()

    layout = layout or ResourceLayout(self, request)
    layout.breadcrumbs.append(Link(_("Subscribe"), '#'))

    return {
        'title': self.title,
        'resource': self,
        'layout': layout,
        'url': url
    }


@OrgApp.view(model=Resource, permission=Public, name='ical')
def view_ical(self, request):
    assert self.access_token is not None

    if request.params.get('access-token') != self.access_token:
        raise exc.HTTPForbidden()

    s = utcnow() - timedelta(days=30)
    e = utcnow() + timedelta(days=30 * 12)

    cal = icalendar.Calendar()
    cal.add('prodid', '-//OneGov//onegov.org//')
    cal.add('version', '2.0')
    cal.add('method', 'PUBLISH')

    cal.add('x-wr-calname', self.title)
    cal.add('x-wr-relcalid', self.id.hex)

    # refresh every 120 minutes by default (Outlook and maybe others)
    cal.add('x-published-ttl', 'PT120M')

    # add allocations/reservations
    date = utcnow()
    path = module_path('onegov.org', 'queries/resource-ical.sql')
    stmt = as_selectable_from_path(path)

    records = object_session(self).execute(select(stmt.c).where(and_(
        stmt.c.resource == self.id, s <= stmt.c.start, stmt.c.start <= e
    )))

    for r in records:
        start = r.start
        end = r.end + timedelta(microseconds=1)

        evt = icalendar.Event()
        evt.add('uid', r.token)
        evt.add('summary', r.title)
        evt.add('location', self.title)
        evt.add('description', r.description)
        evt.add('dtstart', standardize_date(start, 'UTC'))
        evt.add('dtend', standardize_date(end, 'UTC'))
        evt.add('dtstamp', date)
        evt.add('url', request.class_link(Ticket, {
            'handler_code': r.handler_code,
            'id': r.ticket_id
        }))

        cal.add_component(evt)

    return Response(
        cal.to_ical(),
        content_type='text/calendar',
        content_disposition=f'inline; filename={self.name}.ics'
    )


@OrgApp.form(model=Resource, permission=Private, name='export',
             template='export.pt', form=ResourceExportForm)
def view_export(self, request, form, layout=None):

    layout = layout or ResourceLayout(self, request)
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


@OrgApp.form(model=ResourceCollection, permission=Private, name='export-all',
             template='export.pt', form=AllResourcesExportForm)
def view_export_all(self, request, form, layout=None):
    self.title = _("Export All")
    layout = layout or ResourceLayout(self, request)
    layout.editbar_links = None

    def no_reservations_for_date(reservations):
        return not reservations

    if form.submitted(request):

        default_group = request.translate(_("General"))
        resources = group_by_column(request=request, query=self.query(),
                                    default_group=default_group,
                                    group_column=Resource.group,
                                    sort_column=Resource.title)

        ext_resources = group_by_column(request,
                                        query=ExternalLinkCollection.for_model(
                                            request.session,
                                            ResourceCollection).query(),
                                        group_column=ExternalLink.group,
                                        sort_column=ExternalLink.order)

        grouped = combine_grouped(resources, ext_resources,
                                  sort=lambda x: x.title)

        all_results = []
        all_titles = []
        all_field_order = []

        for entries in grouped.values():
            for resource in entries:
                resource.bind_to_libres_context(request.app.libres_context)

                field_order, results = run_export(resource=resource,
                                                  start=form.data['start'],
                                                  end=form.data['end'],
                                                  nested=form.format == 'json',
                                                  formatter=layout.
                                                  export_formatter(
                                                      form.format))

                if results:
                    all_results.append(results)
                    all_titles.append(normalize_for_url(resource.title)[:31])
                    all_field_order.append(field_order)

        if no_reservations_for_date(all_results):
            request.alert(_("No reservations found for the given date range."))
            return request.redirect(request.url)

        return form.as_multiple_export_response(results=all_results,
                                                titles=all_titles,
                                                keys=all_field_order)

    if request.method == 'GET':

        def get_week(date):
            """Return the full week (Sunday first) of the week containing
            the given date.
            """
            one_day = timedelta(days=1)
            day_idx = (date.weekday() + 1) % 7  # turn sunday into 0, monday
            # into 1, etc.
            sunday = date - timedelta(days=day_idx)
            date = sunday
            for n in range(7):
                yield date
                date += one_day

        friday = list(get_week(datetime.now().date()))[5]

        form.start.data, form.end.data = datetime.now().date(), friday

    return {'layout': layout, 'title': _("Export"), 'form': form,
            'explanation': _("Exports the reservations of all resources in"
                             " a given date range.")}


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
