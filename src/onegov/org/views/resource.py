import icalendar
import morepath
import sedate
import collections

from collections import OrderedDict, namedtuple
from datetime import date as date_t, datetime, time, timedelta
from isodate import parse_date, ISO8601Error
from itertools import groupby, islice
from morepath.request import Response
from onegov.core.security import Public, Private, Personal
from onegov.core.utils import module_path
from onegov.core.orm import as_selectable_from_path
from onegov.form import FormSubmission
from onegov.org.cli import close_ticket
from onegov.org.forms.resource import AllResourcesExportForm
from onegov.org import _, OrgApp, utils
from onegov.org.elements import Link
from onegov.org.forms import (
    FindYourSpotForm, ResourceForm, ResourceCleanupForm, ResourceExportForm)
from onegov.org.layout import (
    FindYourSpotLayout, ResourcesLayout, ResourceLayout)
from onegov.org.models.resource import (
    DaypassResource, FindYourSpotCollection, RoomResource, ItemResource)
from onegov.org.models.external_link import (
    ExternalLinkCollection, ExternalLink)
from onegov.org.utils import group_by_column, keywords_first
from onegov.reservation import ResourceCollection, Resource, Reservation
from onegov.ticket import Ticket, TicketCollection
from onegov.pay import PaymentCollection
from operator import attrgetter, itemgetter
from purl import URL
from sedate import utcnow, standardize_date
from sqlalchemy import and_, select
from sqlalchemy.orm import object_session
from webob import exc


from typing import cast, Any, TYPE_CHECKING
if TYPE_CHECKING:
    from _typeshed import SupportsRichComparison
    from collections.abc import Callable, Iterable, Iterator, Mapping
    from libres.db.models import Reservation as BaseReservation
    from onegov.core.types import JSON_ro, RenderData
    from onegov.org.request import OrgRequest
    from onegov.reservation import Allocation
    from sedate.types import DateLike
    from sqlalchemy.orm import Query
    from typing import TypedDict, TypeVar
    from typing_extensions import TypeAlias
    from uuid import UUID
    from webob import Response as BaseResponse

    T = TypeVar('T')
    KT = TypeVar('KT')
    RoomSlots: TypeAlias = dict[UUID, list[utils.FindYourSpotEventInfo]]
    ReservationTicketRow: TypeAlias = tuple[
        datetime,               # Reservation.start
        datetime,               # Reservation.end
        int,                    # Reservation.quota
        dict[str, Any] | None,  # Reservation.data
        str | None,             # Ticket.subtitle
        UUID                    # Ticket.id
    ]
    ReservationExportRow: TypeAlias = tuple[
        datetime,       # Reservation.start
        datetime,       # Reservation.end
        int,            # Reservation.quota
        str,            # Reservation.email
        str,            # Ticket.number
        str | None,     # Ticket.subtitle
        dict[str, Any]  # FormSubmission.data
    ]

    ResourceDict = TypedDict('ResourceDict', {
        'success': str,
        'title': str,
        'class': type[DaypassResource | RoomResource | ItemResource]
    })


RESOURCE_TYPES: dict[str, 'ResourceDict'] = {
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


# NOTE: This function is inherently not type safe since we modify the original
#       items that have been passed in, but this way is more memory efficient
def combine_grouped(
    items: dict['KT', list['T']],
    external_links: dict['KT', list[ExternalLink]],
    sort: 'Callable[[T | ExternalLink], SupportsRichComparison] | None' = None
) -> dict['KT', list['T | ExternalLink']]:

    combined = cast('dict[KT, list[T | ExternalLink]]', items)
    values: list[T | ExternalLink]
    for key, values in external_links.items():  # type:ignore
        if key not in combined:
            combined[key] = values
        else:
            if sort:
                combined[key] = sorted(combined[key] + values, key=sort)
            else:
                combined[key] += values
    return collections.OrderedDict(sorted(combined.items()))


def get_daypass_form(
    self: ResourceCollection,
    request: 'OrgRequest'
) -> type[ResourceForm]:
    return get_resource_form(self, request, 'daypass')


def get_room_form(
    self: ResourceCollection,
    request: 'OrgRequest'
) -> type[ResourceForm]:
    return get_resource_form(self, request, 'room')


def get_item_form(
    self: ResourceCollection,
    request: 'OrgRequest'
) -> type[ResourceForm]:
    return get_resource_form(self, request, 'daily-item')


def get_resource_form(
    self: ResourceCollection | DaypassResource | RoomResource | ItemResource,
    request: 'OrgRequest',
    type: str | None = None
) -> type[ResourceForm]:

    if isinstance(self, ResourceCollection):
        assert type is not None
        model = RESOURCE_TYPES[type]['class']()
    else:
        model = self

    return model.with_content_extensions(ResourceForm, request)


@OrgApp.html(
    model=ResourceCollection,
    template='resources.pt',
    permission=Public
)
def view_resources(
    self: ResourceCollection,
    request: 'OrgRequest',
    layout: ResourcesLayout | None = None
) -> 'RenderData':

    if layout is None:
        layout = ResourcesLayout(self, request)

    default_group = request.translate(_("General"))
    # this is a bit of a white lie, we insert those later on
    resources: dict[str, list[Resource | FindYourSpotCollection]]
    resources = group_by_column(
        request=request,
        query=self.query(),  # type:ignore[arg-type]
        default_group=default_group,
        group_column=Resource.group,
        sort_column=Resource.title
    )

    def contains_at_least_one_room(
        resources: 'Iterable[object]'
    ) -> bool:
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

    def link_func(
        model: Resource | FindYourSpotCollection | ExternalLink
    ) -> str:

        if isinstance(model, ExternalLink):
            return model.url
        return request.link(model)

    def edit_link(
        model: Resource | FindYourSpotCollection | ExternalLink
    ) -> str | None:

        if isinstance(model, ExternalLink) and request.is_manager:
            title = request.translate(_("Edit resource"))
            to = request.class_link(ResourceCollection)
            return request.link(
                model,
                query_params={'title': title, 'to': to},
                name='edit'
            )
        return None

    def lead_func(
        model: Resource | FindYourSpotCollection | ExternalLink
    ) -> str:

        lead = model.meta.get('lead')
        if not lead:
            lead = ''
        lead = layout.linkify(lead)
        return lead

    return {
        'title': _("Reservations"),
        'resources': grouped,
        'layout': layout,
        'link_func': link_func,
        'edit_link': edit_link,
        'lead_func': lead_func,
    }


@OrgApp.form(
    model=FindYourSpotCollection,
    template='find_your_spot.pt',
    permission=Public,
    form=FindYourSpotForm
)
def view_find_your_spot(
    self: FindYourSpotCollection,
    request: 'OrgRequest',
    form: FindYourSpotForm,
    layout: FindYourSpotLayout | None = None
) -> 'RenderData':

    # HACK: Focus results
    form.action += '#results'
    room_slots: dict[date_t, RoomSlots] | None = None
    rooms = sorted(
        request.exclude_invisible(self.query()),
        key=attrgetter('title')
    )
    if not rooms:
        # we'll treat categories without rooms as non-existant
        raise exc.HTTPNotFound()

    form.apply_rooms(rooms)
    if form.submitted(request):
        assert form.start.data is not None
        assert form.end.data is not None
        start_time = form.start_time.data
        end_time = form.end_time.data
        assert start_time is not None
        assert end_time is not None
        start = datetime.combine(form.start.data, start_time)
        end = datetime.combine(form.end.data, end_time)

        if form.rooms:
            assert form.rooms.data is not None
            # filter rooms according to the form selection
            rooms = [room for room in rooms if room.id in form.rooms.data]

        def included_dates() -> 'Iterator[date_t]':
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
                    start, end, days=form.weekdays.data, strict=True
                )
            ):
                # FIXME: libres isn't super careful about polymorphism yet
                #        whenever we clean that up we can make Scheduler
                #        generic and bind our subclass, so we don't have to
                #        cast here, right now this is only safe because we
                #        don't insert any allocations with the base class'
                #        polymorphic identity
                allocation = cast('Allocation', allocation)
                assert allocation.timezone is not None

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


@OrgApp.json(
    model=FindYourSpotCollection,
    name='reservations',
    permission=Public
)
def get_find_your_spot_reservations(
    self: FindYourSpotCollection,
    request: 'OrgRequest'
) -> 'JSON_ro':

    reservations = sorted(
        (utils.ReservationInfo(resource, reservation, request).as_dict()
            for resource in request.exclude_invisible(self.query())
            # FIXME: Maybe we should move bound_reservations to the base
            #        Resource class?
            if hasattr(resource, 'bound_reservations')
            for reservation in resource.bound_reservations(request)),
        key=itemgetter('date')
    )

    return {
        'reservations': reservations,
        # no predictions in the list
        'prediction': None
    }


@OrgApp.json(model=ResourceCollection, permission=Public, name='json')
def view_resources_json(
    self: ResourceCollection,
    request: 'OrgRequest'
) -> 'JSON_ro':

    def transform(resource: Resource) -> 'JSON_ro':
        return {
            'name': resource.name,
            'title': resource.title,
            'url': request.link(resource),
        }

    @request.after
    def cache(response: 'BaseResponse') -> None:
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


@OrgApp.form(
    model=ResourceCollection,
    name='new-room',
    template='form.pt',
    permission=Private,
    form=get_room_form
)
def handle_new_room(
    self: ResourceCollection,
    request: 'OrgRequest',
    form: ResourceForm,
    layout: ResourcesLayout | None = None
) -> 'RenderData | BaseResponse':
    return handle_new_resource(self, request, form, 'room', layout)


@OrgApp.form(
    model=ResourceCollection,
    name='new-daypass',
    template='form.pt',
    permission=Private,
    form=get_daypass_form
)
def handle_new_daypass(
    self: ResourceCollection,
    request: 'OrgRequest',
    form: ResourceForm,
    layout: ResourcesLayout | None = None
) -> 'RenderData | BaseResponse':
    return handle_new_resource(self, request, form, 'daypass', layout)


@OrgApp.form(
    model=ResourceCollection,
    name='new-daily-item',
    template='form.pt',
    permission=Private,
    form=get_item_form
)
def handle_new_resource_item(
    self: ResourceCollection,
    request: 'OrgRequest',
    form: ResourceForm,
    layout: ResourcesLayout | None = None
) -> 'RenderData | BaseResponse':
    return handle_new_resource(self, request, form, 'daily-item', layout)


def handle_new_resource(
    self: ResourceCollection,
    request: 'OrgRequest',
    form: ResourceForm,
    type: str,
    layout: ResourcesLayout | None = None
) -> 'RenderData | BaseResponse':

    if form.submitted(request):
        assert form.title.data is not None
        resource = self.add(
            title=form.title.data,
            type=type,
            timezone='Europe/Zurich'
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


@OrgApp.form(
    model=Resource,
    name='edit',
    template='form.pt',
    permission=Private,
    form=get_resource_form
)
def handle_edit_resource(
    self: Resource,
    request: 'OrgRequest',
    form: ResourceForm,
    layout: ResourceLayout | None = None
) -> 'RenderData | BaseResponse':

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
    layout.edit_mode = True

    return {
        'layout': layout,
        'title': self.title,
        'form': form,
        'form_width': 'large'
    }


@OrgApp.html(model=Resource, template='resource.pt', permission=Public)
def view_resource(
    self: Resource,
    request: 'OrgRequest',
    layout: ResourceLayout | None = None
) -> 'RenderData':

    return {
        'title': self.title,
        'files': getattr(self, 'files', None),
        'resource': self,
        'layout': layout or ResourceLayout(self, request),
        'feed': request.link(self, name='slots'),
        'resources_url': request.class_link(ResourceCollection, name='json')
    }


@OrgApp.view(model=Resource, request_method='DELETE', permission=Private)
def handle_delete_resource(self: Resource, request: 'OrgRequest') -> None:

    request.assert_valid_csrf_token()
    tickets = TicketCollection(request.session)

    def handle_reservation_tickets(reservation: 'BaseReservation') -> None:
        ticket = tickets.by_handler_id(reservation.token.hex)
        if ticket:
            assert request.current_user is not None

            close_ticket(ticket, request.current_user, request)
            ticket.create_snapshot(request)

            payment = ticket.handler.payment
            if (payment and PaymentCollection(request.session).query()
                    .filter_by(id=payment.id).first()):
                PaymentCollection(request.session).delete(payment)

    collection = ResourceCollection(request.app.libres_context)
    collection.delete(
        self,
        including_reservations=True,
        handle_reservation=handle_reservation_tickets
    )


@OrgApp.form(model=Resource, permission=Private, name='cleanup',
             form=ResourceCleanupForm, template='resource_cleanup.pt')
def handle_cleanup_allocations(
    self: Resource,
    request: 'OrgRequest',
    form: ResourceCleanupForm,
    layout: ResourceLayout | None = None
) -> 'RenderData | BaseResponse':
    """ Removes all unused allocations between the given dates. """

    if form.submitted(request):
        start, end, days = form.start.data, form.end.data, form.weekdays.data
        assert start is not None and end is not None
        count = self.scheduler.remove_unused_allocations(start, end, days=days)

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


def predict_next_reservation(
    resource: Resource,
    request: 'OrgRequest',
    reservations: 'Iterable[BaseReservation]'
) -> 'RenderData | None':

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
def get_reservations(self: Resource, request: 'OrgRequest') -> 'RenderData':

    # FIXME: Maybe we should move bound_reservations to the base
    #        Resource class?
    assert hasattr(self, 'bound_reservations')
    reservations = tuple(self.bound_reservations(request))
    prediction = predict_next_reservation(self, request, reservations)

    return {
        'reservations': [
            utils.ReservationInfo(self, reservation, request).as_dict()
            for reservation in reservations
        ],
        'prediction': prediction
    }


def get_date(text: object, default: datetime) -> datetime:
    try:
        date = parse_date(text)
        return datetime(date.year, date.month, date.day, tzinfo=default.tzinfo)
    except (ISO8601Error, TypeError):
        return default


def get_date_range(
    resource: Resource,
    params: 'Mapping[str, Any]'
) -> tuple[datetime, datetime]:

    # FIXME: should we move this to the base class?
    assert hasattr(resource, 'calendar_date_range')
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


@OrgApp.html(
    model=Resource,
    permission=Personal,
    name='occupancy',
    template='resource_occupancy.pt'
)
def view_occupancy(
    self: Resource,
    request: 'OrgRequest',
    layout: ResourceLayout | None = None
) -> 'RenderData':

    # for members check if they're actually allowed to see this
    if (
        request.has_role('member')
        and not getattr(self, 'occupancy_is_visible_to_members', False)
    ):
        raise exc.HTTPForbidden()

    # infer the default start/end date from the calendar view parameters
    start, end = get_date_range(self, request.params)

    # include pending reservations
    query: Query[ReservationTicketRow]
    # FIXME: Should this view only work on a common base class of our own
    #        Resources? We can insert an intermediary abstract class, this
    #        may clean up some other things here as well
    query = self.reservations_with_tickets_query(  # type:ignore[attr-defined]
        start, end, exclude_pending=False)
    query = query.with_entities(
        Reservation.start, Reservation.end, Reservation.quota,
        Reservation.data, Ticket.subtitle, Ticket.id
    )

    def group_key(record: 'ReservationTicketRow') -> date_t:
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


@OrgApp.html(
    model=Resource,
    template='resource-subscribe.pt',
    permission=Private,
    name='subscribe'
)
def view_resource_subscribe(
    self: Resource,
    request: 'OrgRequest',
    layout: ResourceLayout | None = None
) -> 'RenderData':

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
def view_ical(self: Resource, request: 'OrgRequest') -> Response:
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


@OrgApp.form(
    model=Resource,
    permission=Private,
    name='export',
    template='export.pt',
    form=ResourceExportForm
)
def view_export(
    self: Resource,
    request: 'OrgRequest',
    form: ResourceExportForm,
    layout: ResourceLayout | None = None
) -> 'RenderData | BaseResponse':

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


@OrgApp.form(
    model=ResourceCollection,
    permission=Private,
    name='export-all',
    template='export.pt',
    form=AllResourcesExportForm
)
def view_export_all(
    self: ResourceCollection,
    request: 'OrgRequest',
    form: AllResourcesExportForm,
    layout: ResourceLayout | None = None
) -> 'RenderData | BaseResponse':

    # FIXME: Why are we using ResouceLayout and not ResourcesLayout?
    #        this is a weird hack, if you want to be able to use the
    #        ResourceLayout with ResourceCollection, then make it work
    #        in the Layout, not by patching the collection...
    self.title = _("Export All")  # type:ignore
    layout = layout or ResourceLayout(self, request)  # type:ignore
    layout.editbar_links = None

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
                if isinstance(resource, ExternalLink):
                    continue

                resource.bind_to_libres_context(request.app.libres_context)

                field_order, results = run_export(
                    resource=resource,
                    start=form.data['start'],
                    end=form.data['end'],
                    nested=form.format == 'json',
                    formatter=layout.
                    export_formatter(form.format)
                )

                if results:
                    all_results.append(results)
                    all_titles.append(resource.title)
                    all_field_order.append(field_order)

        if not all_results:
            request.alert(_("No reservations found for the given date range."))
            return request.redirect(request.url)

        return Response(
            form.as_multiple_export_response(
                results=all_results, titles=all_titles, keys=all_field_order
            ),
            content_type=(
                'application/vnd.openxmlformats'
                '-officedocument.spreadsheetml.sheet'
            ),
            content_disposition='inline; filename={}.xlsx'.format(
                'All-Reservations-Export'
            )
        )

    if request.method == 'GET':

        # FIXME: This has a weird singularity on saturday where the interval
        #        goes backwards one day, the original code had the same issue
        #        Technically nobody should be exportings things on a Saturday
        #        but it probably still makes sense to handle this better
        start = date_t.today()
        day_idx = (start.weekday() + 1) % 7  # turn sunday into 0, monday
        friday = start + timedelta(days=5 - day_idx)

        form.start.data, form.end.data = start, friday

    return {
        'layout': layout,
        'title': _("Export"),
        'form': form,
        'explanation': _(
            "Exports the reservations of all resources in"
            " a given date range."
        )
    }


def run_export(
    resource: Resource,
    start: 'DateLike',
    end: 'DateLike',
    nested: bool,
    formatter: 'Callable[[Any], object]'
) -> tuple['Callable[[str], tuple[int, str]]', list[dict[str, Any]]]:

    start = sedate.replace_timezone(
        datetime(start.year, start.month, start.day),
        resource.timezone
    )
    end = sedate.replace_timezone(
        datetime(end.year, end.month, end.day),
        resource.timezone
    )

    start, end = sedate.align_range_to_day(start, end, resource.timezone)

    query: Query[ReservationExportRow]
    query = resource.reservations_with_tickets_query(start, end)  # type:ignore
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
        result: dict[str, Any] = OrderedDict()

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
