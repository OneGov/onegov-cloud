from __future__ import annotations

import collections
import hashlib
import icalendar
import morepath
import secrets
import sedate

from collections import OrderedDict
from datetime import date as date_t, datetime, time, timedelta
from isodate import parse_date, ISO8601Error
from itertools import islice
from libres.modules.errors import LibresError
from morepath.request import Response
from onegov.core.security import Public, Private, Personal
from onegov.core.utils import module_path, Bunch
from onegov.core.orm import as_selectable_from_path
from onegov.core.orm.types import UUID as UUIDType
from onegov.form import as_internal_id, FormSubmission
from onegov.org.cli import close_ticket
from onegov.org.forms.resource import AllResourcesExportForm
from onegov.org import _, OrgApp, utils
from onegov.org.elements import Link
from onegov.org.forms import (
    FindYourSpotForm, ResourceForm, ResourceCleanupForm, ResourceExportForm)
from onegov.org.layout import (
    DefaultLayout, FindYourSpotLayout, ResourcesLayout, ResourceLayout)
from onegov.org.models.dashboard import CitizenDashboard
from onegov.org.models.resource import (
    DaypassResource, FindYourSpotCollection, RoomResource, ItemResource)
from onegov.org.models.external_link import (
    ExternalLinkCollection, ExternalLink)
from onegov.org.pdf.my_reservations import MyReservationsPdf
from onegov.org.utils import group_by_column, keywords_first
from onegov.org.views.utils import assert_citizen_logged_in
from onegov.reservation import ResourceCollection, Resource, Reservation
from onegov.ticket import Ticket
from operator import attrgetter, itemgetter
from purl import URL
from sedate import utcnow, standardize_date
from sqlalchemy import and_, func, select, cast as sa_cast, Boolean
from sqlalchemy.orm import undefer
from webob import exc


from typing import cast, Any, NamedTuple, Self, TYPE_CHECKING
if TYPE_CHECKING:
    from _typeshed import SupportsRichComparison
    from collections.abc import Callable, Iterable, Iterator, Mapping
    from libres.db.models import Reservation as BaseReservation
    from onegov.core.types import JSON_ro, RenderData
    from onegov.org.models.ticket import ReservationTicket
    from onegov.org.request import OrgRequest
    from onegov.reservation import Allocation
    from sedate.types import DateLike
    from sqlalchemy.orm import Query
    from typing import TypeAlias, TypedDict, TypeVar
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


class OccupancyEntry(NamedTuple):
    start: datetime
    end: datetime
    title: str | None
    quota: int
    pending: bool
    url: str


RESOURCE_TYPES: dict[str, ResourceDict] = {
    'daypass': {
        'success': _('Added a new daypass'),
        'title': _('New daypass'),
        'class': DaypassResource
    },
    'room': {
        'success': _('Added a new room'),
        'title': _('New room'),
        'class': RoomResource
    },
    'daily-item': {
        'success': _('Added a new item'),
        'title': _('New Item'),
        'class': ItemResource
    }
}


# NOTE: This function is inherently not type safe since we modify the original
#       items that have been passed in, but this way is more memory efficient
def combine_grouped(
    items: dict[KT, list[T]],
    external_links: dict[KT, list[ExternalLink]],
    sort: Callable[[T | ExternalLink], SupportsRichComparison] | None = None
) -> dict[KT, list[T | ExternalLink]]:

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
    request: OrgRequest
) -> type[ResourceForm]:
    return get_resource_form(self, request, 'daypass')


def get_room_form(
    self: ResourceCollection,
    request: OrgRequest
) -> type[ResourceForm]:
    return get_resource_form(self, request, 'room')


def get_item_form(
    self: ResourceCollection,
    request: OrgRequest
) -> type[ResourceForm]:
    return get_resource_form(self, request, 'daily-item')


def get_resource_form(
    self: ResourceCollection | DaypassResource | RoomResource | ItemResource,
    request: OrgRequest,
    type: str | None = None
) -> type[ResourceForm]:

    if isinstance(self, ResourceCollection):
        assert type is not None
        model = RESOURCE_TYPES[type]['class']()
    else:
        model = self

    return model.with_content_extensions(ResourceForm, request)


class ResourceGroup(NamedTuple):
    title: str
    entries: list[Resource | ExternalLink | ResourceSubgroup]
    find_your_spot: FindYourSpotCollection | None

    @classmethod
    def from_grouped(
        cls,
        request: OrgRequest,
        grouped: dict[str, list[Resource | ExternalLink]],
        default_group: str,
    ) -> list[Self]:

        result: list[Self] = []
        for group, items in grouped.items():
            entries: dict[str, Any] = {}
            group_has_find_your_spot = False
            for item in items:
                is_room = isinstance(item, Resource) and item.type == 'room'
                if is_room:
                    group_has_find_your_spot = True

                if subgroup_name := getattr(item, 'subgroup', None):
                    (
                        subgroup_has_find_your_spot,
                        subentries
                    ) = entries.setdefault(subgroup_name, (is_room, []))
                    if is_room and not subgroup_has_find_your_spot:
                        entries[subgroup_name] = (True, subentries)

                    subentries.append(item)
                else:
                    # avoid collisions
                    title = item.title
                    while title in entries:
                        title = f'{title} '
                    entries[title] = item

            result.append(cls(
                title=group,
                entries=[
                    ResourceSubgroup(
                        title=subgroup,
                        entries=sorted(entry[1], key=attrgetter('title')),
                        find_your_spot=FindYourSpotCollection(
                            request.app.libres_context,
                            group=None if group == default_group else group,
                            subgroup=subgroup
                        ) if entry[0] else None,
                    ) if isinstance(entry, tuple) else entry
                    for subgroup, entry in sorted(
                        entries.items(),
                        key=itemgetter(0)
                    )
                ],
                find_your_spot=FindYourSpotCollection(
                    request.app.libres_context,
                    group=None if group == default_group else group
                ) if group_has_find_your_spot else None,
            ))
        return result


class ResourceSubgroup(NamedTuple):
    title: str
    # NOTE: External links don't yet support subgroups, but we
    #       may add support for it, if there is a demand
    entries: list[Resource | ExternalLink]
    find_your_spot: FindYourSpotCollection | None


@OrgApp.html(
    model=ResourceCollection,
    template='resources.pt',
    permission=Public
)
def view_resources(
    self: ResourceCollection,
    request: OrgRequest,
    layout: ResourcesLayout | None = None
) -> RenderData:

    if layout is None:
        layout = ResourcesLayout(self, request)

    default_group = request.translate(_('General'))
    resources = group_by_column(
        request=request,
        query=self.query(),
        default_group=default_group,
        group_column=Resource.group,
        sort_column=Resource.title
    )

    ext_resources = group_by_column(
        request,
        query=ExternalLinkCollection.for_model(
            request.session, ResourceCollection
        ).query(),
        default_group=default_group,
        group_column=ExternalLink.group,
        sort_column=ExternalLink.order
    )

    grouped = combine_grouped(
        resources, ext_resources, sort=attrgetter('title')
    )

    def link_func(
        model: Resource | FindYourSpotCollection | ExternalLink
    ) -> str:

        if isinstance(model, ExternalLink):
            return model.url
        return request.link(model)

    def edit_link(model: Resource | ExternalLink) -> str | None:
        if isinstance(model, ExternalLink) and request.is_manager:
            title = request.translate(_('Edit resource'))
            to = request.class_link(ResourceCollection)
            return request.link(
                model,
                query_params={'title': title, 'to': to},
                name='edit'
            )
        return None

    def lead_func(model: Resource | ExternalLink) -> str:
        lead = model.meta.get('lead')
        if not lead:
            lead = ''
        lead = layout.linkify(lead)
        return lead

    return {
        'title': _('Reservations'),
        'resources': ResourceGroup.from_grouped(
            request,
            grouped,
            default_group
        ),
        'layout': layout,
        'link_func': link_func,
        'edit_link': edit_link,
        'lead_func': lead_func,
        'header_html': request.app.org.resource_header_html,
        'footer_html': request.app.org.resource_footer_html,
    }


@OrgApp.form(
    model=FindYourSpotCollection,
    template='find_your_spot.pt',
    permission=Public,
    form=FindYourSpotForm
)
def view_find_your_spot(
    self: FindYourSpotCollection,
    request: OrgRequest,
    form: FindYourSpotForm,
    layout: FindYourSpotLayout | None = None
) -> RenderData:

    # HACK: Focus results
    form.action += '#results'
    room_slots: dict[date_t, RoomSlots] | None = None
    missing_dates: dict[date_t, list[Resource] | None] | None = None
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
        assert form.duration.data is not None
        duration = form.duration.data
        step = (
            timedelta(minutes=10)
            if duration.total_seconds() < 600
            else duration
        )

        if form.rooms:
            assert form.rooms.data is not None
            # filter rooms according to the form selection
            rooms = [room for room in rooms if room.id in form.rooms.data]

        def included_dates() -> Iterator[date_t]:
            # yields all the dates that should be part of our result set
            current = start.date()
            max_date = end.date()
            while current <= max_date:
                if not form.is_excluded(current):
                    yield current
                current += timedelta(days=1)

        def spot_infos_for_free_slots(
            allocation: Allocation,
            free: list[tuple[datetime, datetime]],
            target_range: timedelta,
            *,
            adjustable: bool = False,
            availability_threshold: float = 5.0
        ) -> Iterator[utils.FindYourSpotEventInfo]:

            # FIXME: The availability calculation should probably be
            #        normalized when a daylight savings shift occurs
            assert allocation.timezone is not None
            slot_start, slot_end = free[0]
            slot_end += time.resolution
            for next_slot_start, next_slot_end in islice(free, 1, None):

                if slot_end != next_slot_start:
                    availability = (slot_end - slot_start) / target_range
                    availability *= 100.0
                    yield utils.FindYourSpotEventInfo(
                        allocation,
                        (sedate.to_timezone(
                            slot_start, allocation.timezone),
                            sedate.to_timezone(
                                slot_end, allocation.timezone)),
                        availability,
                        1 if availability >= availability_threshold else 0,
                        request,
                        adjustable=adjustable
                    )
                    slot_start = next_slot_start

                # expand slot end
                slot_end = next_slot_end + time.resolution

            # add final slot
            availability = (slot_end - slot_start) / target_range
            availability *= 100.0
            yield utils.FindYourSpotEventInfo(
                allocation,
                (sedate.to_timezone(slot_start, allocation.timezone),
                 sedate.to_timezone(slot_end, allocation.timezone)),
                availability,
                1 if availability >= availability_threshold else 0,
                request,
                adjustable=adjustable
            )

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
                    availability = (
                        allocation.display_end() - allocation.display_start()
                    ) / duration * 100.0
                    if adjustable := allocation.quota > 1:
                        if availability >= 100.0:
                            availability = 100.0

                    slots.append(utils.FindYourSpotEventInfo(
                        allocation,
                        None,
                        availability if quota_left else 0.0,
                        quota_left,
                        request,
                        adjustable=adjustable
                    ))
                    continue
                elif target_start >= target_end:
                    # this can happen for non-existent times, we
                    # just treat it as not available in this case
                    continue

                # add single click slots for the correct duration
                added_slots = 0
                for target_slot_start in sedate.dtrange(
                    target_start,
                    target_end - step,
                    step,
                    skip_missing=True
                ):
                    if added_slots >= 5:
                        break

                    target_slot_end = target_slot_start + duration

                    free = allocation.free_slots(
                        target_slot_start,
                        target_slot_end
                    )
                    if not free:
                        if (
                            allocation.display_start() <= target_slot_start
                            and allocation.display_end() >= target_slot_end
                        ):
                            # render an unavailable slot
                            added_slots += 1
                            slots.append(utils.FindYourSpotEventInfo(
                                allocation,
                                (
                                    max(
                                        sedate.to_timezone(
                                            target_slot_start,
                                            allocation.timezone
                                        ),
                                        allocation.display_start(),
                                    ),
                                    min(
                                        sedate.to_timezone(
                                            target_slot_end,
                                            allocation.timezone
                                        ),
                                        allocation.display_end()
                                    )
                                ),
                                0,
                                0,
                                request,
                            ))
                        continue

                    spot_infos = list(spot_infos_for_free_slots(
                        allocation,
                        free,
                        target_slot_end - target_slot_start
                    ))
                    if (
                        len(spot_infos) != 1
                        or spot_infos[0].availability < 100.0
                    ):
                        total_availability = sum(
                            info.availability
                            for info in spot_infos
                        )
                        # render a partially available slot
                        slots.append(utils.FindYourSpotEventInfo(
                            allocation,
                            (
                                max(
                                    sedate.to_timezone(
                                        target_slot_start,
                                        allocation.timezone
                                    ),
                                    allocation.display_start(),
                                ),
                                min(
                                    sedate.to_timezone(
                                        target_slot_end,
                                        allocation.timezone
                                    ),
                                    allocation.display_end()
                                )
                            ),
                            total_availability,
                            0,
                            request,
                        ))
                        added_slots += 1
                        continue

                    slots.append(spot_infos[0])
                    added_slots += 1

                free = allocation.free_slots(
                    target_start,
                    target_end
                )
                if not free:
                    continue

                # add the actual available slots for custom adjustments
                slots.extend(
                    slot
                    for slot in spot_infos_for_free_slots(
                        allocation,
                        # we want to render the entire available time
                        # span, as long as it overlaps with our target
                        # so people can reserve a slot that's slightly
                        # outside their selected range if they want
                        allocation.free_slots(),
                        duration,
                        adjustable=True
                    )
                    # but let's exclude slots that are way smaller than
                    # our selected duration
                    if slot.availability >= 25.0 and sedate.overlaps(
                        target_start,
                        target_end,
                        # these slots should always have a slot_time
                        slot.slot_time[0],  # type: ignore[index]
                        slot.slot_time[1]  # type: ignore[index]
                    )
                )

        auto_reserve = form.auto_reserve_available_slots.data
        if auto_reserve != 'no':
            rooms_dict = {room.id: room for room in rooms}
            reservations: dict[UUID, list[Reservation]] = {
                room.id: room.bound_reservations(request).all()  # type: ignore[attr-defined]
                for room in rooms
            }
            skipped_due_to_existing_reservation = {
                date: {
                    room_id
                    for room_id, slots in date_room_slots.items()
                    if any(
                        reservation.display_start() == dates[0]
                        and reservation.display_end() == dates[1]
                        for slot in slots
                        if slot.availability >= 5.0
                        if (dates := slot.slot_time or (
                            slot.allocation.display_start(),
                            slot.allocation.display_end()
                        ))
                        for reservation in reservations[room_id]
                    )
                }
                for date, date_room_slots in room_slots.items()
            }

            reserved_dates: dict[date_t, set[UUID]] = {}
            for date, date_room_slots in (
                # skip iteration if we have existing reservations
                # that match our criteria and we're only supposed
                # to reserve one of them
                () if auto_reserve == 'for_first_day' and any(
                    skipped_due_to_existing_reservation.values()
                ) else room_slots.items()
            ):
                skipped = skipped_due_to_existing_reservation[date]
                reserved_dates[date] = skipped
                if skipped and (
                    auto_reserve != 'for_every_room'
                    or len(skipped) == len(date_room_slots)
                ):
                    # date already fully reserved
                    continue

                for room_id, slots in date_room_slots.items():
                    if (
                        auto_reserve == 'for_every_room'
                        and room_id in skipped
                    ):
                        # already fully reserved
                        continue

                    for slot in slots:
                        if slot.availability == 100.0:
                            try:
                                room = rooms_dict[room_id]
                                assert hasattr(room, 'bound_session_id')
                                room.scheduler.reserve(
                                    email='0xdeadbeef@example.org',
                                    dates=slot.slot_time or (
                                        slot.allocation.display_start(),
                                        slot.allocation.display_end()
                                    ),
                                    quota=1,
                                    session_id=room.bound_session_id(request),
                                    single_token_per_session=True
                                )
                            except LibresError:
                                # could happen for overlapping existing
                                # reservations or other violations, we treat
                                # this as a missing reserved slot
                                continue
                            else:
                                # we managed to reserve a slot
                                break
                    else:
                        # no slot reserved, move on to the next room
                        continue

                    reserved_dates.setdefault(date, set()).add(room_id)

                    # since we managed to reserve a slot and we're not
                    # making a reservation for every room, we need to
                    # skip the other rooms for this date
                    if auto_reserve != 'for_every_room':
                        break
                else:
                    # either we didn't reserve a slot or we're reserving
                    # a slot in every room, so move on to the next date
                    continue

                # since we broke out of the room loop we must have managed
                # to reserve a slot, so we need to stop the iteration of
                # dates here
                if auto_reserve == 'for_first_day':
                    break

            wanted = len(rooms) if auto_reserve == 'for_every_room' else 1
            missing_dates = {
                date: [
                    room
                    for room in rooms
                    if room.id not in room_ids
                ] if wanted > 1 else None
                for date in room_slots.keys()
                if len(room_ids := reserved_dates.get(date, set())) < wanted
            } if auto_reserve != 'for_first_day' else {}

    if room_slots:
        request.include('reservationlist')

    return {
        'title': _('Find Your Spot'),
        'form': form,
        'rooms': rooms,
        'room_slots': room_slots,
        'missing_dates': missing_dates,
        'layout': layout or FindYourSpotLayout(self, request)
    }


@OrgApp.json(
    model=FindYourSpotCollection,
    name='reservations',
    permission=Public
)
def get_find_your_spot_reservations(
    self: FindYourSpotCollection,
    request: OrgRequest
) -> JSON_ro:

    reservations = sorted(
        (utils.ReservationInfo(resource, reservation, request).as_dict()
            for resource in request.exclude_invisible(self.query())
            # FIXME: Maybe we should move bound_reservations to the base
            #        Resource class?
            if hasattr(resource, 'bound_reservations')
            for reservation in resource.bound_reservations(request)),
        key=itemgetter('date', 'title')
    )

    return {
        'reservations': reservations,
        'delete_link': request.csrf_protected_url(
            request.link(self, name='reservations')
        ),
        # no predictions in the list
        'prediction': None
    }


@OrgApp.json(
    model=FindYourSpotCollection,
    name='reservations',
    request_method='DELETE',
    permission=Public
)
def delete_all_find_your_spot_reservations(
    self: FindYourSpotCollection,
    request: OrgRequest
) -> JSON_ro:

    # anonymous users do not get a csrf token (it's bound to the identity)
    # therefore we can't check for it -> this is not a problem since
    # anonymous users do not really have much to lose here
    # FIXME: We always generate a csrf token now, so we could reconsider
    #        this, although it would mean, that people, that have blocked
    #        cookies, will not be able to delete reservations at all.
    if request.is_logged_in:
        request.assert_valid_csrf_token()

    # TODO: We might be able to make this a lot more efficient by taking
    #       advantage of the fact that we use a single shared token for
    #       all reservations in the same session (although that might
    #       include submitted reservations too? which would be bad)
    for resource in request.exclude_invisible(self.query()):
        resource.bind_to_libres_context(request.app.libres_context)
        # FIXME: Maybe we should move bound_reservations to the base
        #        Resource class?
        assert hasattr(resource, 'bound_reservations')
        for reservation in resource.bound_reservations(request):
            # these shouldn't have a ticket yet, so we don't need
            # to worry about it
            resource.scheduler.remove_reservation(
                reservation.token,
                reservation.id
            )

    return {
        'reservations': [],
        'delete_link': request.csrf_protected_url(
            request.link(self, name='reservations')
        ),
        # no predictions in the list
        'prediction': None
    }


@OrgApp.json(model=ResourceCollection, permission=Public, name='json')
def view_resources_json(
    self: ResourceCollection,
    request: OrgRequest
) -> JSON_ro:

    def transform(resource: Resource) -> JSON_ro:
        return {
            'name': resource.name,
            'title': resource.title,
            'url': request.link(resource),
        }

    @request.after
    def cache(response: BaseResponse) -> None:
        # only update once every minute
        response.cache_control.max_age = 60

    return group_by_column(
        request=request,
        query=self.query(),
        group_column=Resource.group,
        sort_column=Resource.title,
        transform=transform,
        default_group=request.translate(_('Reservations'))
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
    request: OrgRequest,
    form: ResourceForm,
    layout: ResourcesLayout | None = None
) -> RenderData | BaseResponse:
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
    request: OrgRequest,
    form: ResourceForm,
    layout: ResourcesLayout | None = None
) -> RenderData | BaseResponse:
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
    request: OrgRequest,
    form: ResourceForm,
    layout: ResourcesLayout | None = None
) -> RenderData | BaseResponse:
    return handle_new_resource(self, request, form, 'daily-item', layout)


def handle_new_resource(
    self: ResourceCollection,
    request: OrgRequest,
    form: ResourceForm,
    type: str,
    layout: ResourcesLayout | None = None
) -> RenderData | BaseResponse:

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
    layout.edit_mode = True

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
    request: OrgRequest,
    form: ResourceForm,
    layout: ResourceLayout | None = None
) -> RenderData | BaseResponse:

    if form.submitted(request):
        form.populate_obj(self)

        request.success(_('Your changes were saved'))
        return morepath.redirect(request.link(self))

    elif not request.POST:
        form.process(obj=self)

    layout = layout or ResourceLayout(self, request)
    layout.include_editor()
    layout.include_code_editor()
    layout.breadcrumbs.append(Link(_('Edit'), '#'))
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
    request: OrgRequest,
    layout: ResourceLayout | None = None
) -> RenderData:

    return {
        'title': self.title,
        'files': getattr(self, 'files', None),
        'resource': self,
        'layout': layout or ResourceLayout(self, request),
        'feed': request.link(self, name='slots'),
        'resources_url': request.class_link(ResourceCollection, name='json')
    }


@OrgApp.view(model=Resource, request_method='DELETE', permission=Private)
def handle_delete_resource(self: Resource, request: OrgRequest) -> None:

    request.assert_valid_csrf_token()

    def handle_reservation_ticket(ticket: ReservationTicket) -> None:
        if ticket:
            assert request.current_user is not None

            close_ticket(ticket, request.current_user, request)
            ticket.create_snapshot(request)

            if ticket.payment:
                # unlink payment from invoice items, delete invoice
                # items and finally delete invoice
                if ticket.invoice:
                    for invoice_item in ticket.invoice.items:
                        invoice_item.payments = []
                        request.session.delete(invoice_item)

                    request.session.delete(ticket.invoice)

                    # unlink invoice from ticket
                    ticket.invoice = None
                    ticket.invoice_id = None

                # unlink payment from reservation
                for reservation in ticket.handler.reservations:
                    reservation.payment = None

                # unlink and delete payment from ticket
                request.session.delete(ticket.payment)
                ticket.payment = None
                ticket.payment_id = None

    collection = ResourceCollection(request.app.libres_context)
    collection.delete(
        self,
        including_reservations=True,
        handle_reservation_ticket=handle_reservation_ticket,
    )


@OrgApp.form(model=Resource, permission=Private, name='cleanup',
             form=ResourceCleanupForm, template='resource_cleanup.pt')
def handle_cleanup_allocations(
    self: Resource,
    request: OrgRequest,
    form: ResourceCleanupForm,
    layout: ResourceLayout | None = None
) -> RenderData | BaseResponse:
    """ Removes all unused allocations between the given dates. """

    if form.submitted(request):
        start, end, days = form.start.data, form.end.data, form.weekdays.data
        assert start is not None and end is not None
        count = self.scheduler.remove_unused_allocations(start, end, days=days)

        request.success(
            _('Successfully removed ${count} unused allocations', mapping={
                'count': count
            })
        )

        return morepath.redirect(request.link(self))

    if request.method == 'GET':
        form.start.data, form.end.data = get_date_range(self, request.params)

    layout = layout or ResourceLayout(self, request)
    layout.breadcrumbs.append(Link(_('Clean up'), '#'))
    layout.editbar_links = None

    return {
        'layout': layout,
        'title': _('Clean up'),
        'form': form
    }


def predict_next_reservation(
    resource: Resource,
    request: OrgRequest,
    reservations: Iterable[BaseReservation]
) -> RenderData | None:

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
        time = request.translate(_('Whole day'))
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
def get_reservations(self: Resource, request: OrgRequest) -> RenderData:

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
    params: Mapping[str, Any]
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


def assert_visible_by_members(self: Resource, request: OrgRequest) -> None:
    # for members check if they're actually allowed to see this
    if (
        request.has_role('member')
        and not getattr(self, 'occupancy_is_visible_to_members', False)
    ):
        raise exc.HTTPForbidden()


@OrgApp.json(model=Resource, name='occupancy-json', permission=Personal)
def view_occupancy_json(self: Resource, request: OrgRequest) -> JSON_ro:
    """ Returns the reservations in a fullcalendar compatible events feed.

    See `<https://fullcalendar.io/docs/event_data/events_json_feed/>`_ for
    more information.

    """
    assert_visible_by_members(self, request)

    start, end = utils.parse_fullcalendar_request(request, self.timezone)

    if not (start and end):
        return ()

    # get all reservations and tickets
    query: Query[tuple[Reservation, Ticket]]
    query = self.reservations_with_tickets_query(  # type:ignore[attr-defined]
        start, end, exclude_pending=False
    ).with_entities(Reservation, Ticket)
    query = query.options(undefer(Reservation.data))

    return *(
        res.as_dict()
        for res in utils.ReservationEventInfo.from_reservations(
            request,
            self,
            query.with_entities(Reservation, Ticket)
        )
    ), *(
        av.as_dict()
        for av in utils.AvailabilityEventInfo.from_allocations(
            request,
            self,
            # get all all master allocations
            self.scheduler.allocations_in_range(start, end)  # type: ignore[arg-type]
        )
    )


@OrgApp.html(
    model=Resource,
    permission=Personal,
    name='occupancy',
    template='resource_occupancy.pt'
)
def view_occupancy(
    self: Resource,
    request: OrgRequest,
    layout: ResourceLayout | None = None
) -> RenderData:

    assert_visible_by_members(self, request)

    request.include('occupancycalendar')

    return {
        'title': _('Occupancy'),
        'resource': self,
        'layout': layout or ResourceLayout(self, request),
        'feed': request.link(self, name='occupancy-json'),
    }


@OrgApp.json(
    model=ResourceCollection,
    name='my-reservations-json',
    permission=Public
)
def view_my_reservations_json(
    self: ResourceCollection,
    request: OrgRequest
) -> JSON_ro:
    """ Returns the reservations in a fullcalendar compatible events feed.

    See `<https://fullcalendar.io/docs/event_data/events_json_feed/>`_ for
    more information.

    """
    if not request.app.org.citizen_login_enabled:
        raise exc.HTTPNotFound()

    if not request.authenticated_email:
        raise exc.HTTPForbidden()

    start, end = utils.parse_fullcalendar_request(request, 'Europe/Zurich')

    if not (start and end):
        return ()

    path = module_path('onegov.org', 'queries/my-reservations.sql')
    stmt = as_selectable_from_path(path)

    records = request.session.execute(select(stmt.c).where(and_(
        func.lower(stmt.c.email) == request.authenticated_email.lower(),
        start <= stmt.c.start,
        stmt.c.start <= end
    )))

    return [
        utils.MyReservationEventInfo(
            id=r.id,
            token=r.token,
            start=r.start,
            end=r.end,
            accepted=r.accepted,
            timezone=r.timezone,
            resource=r.resource,
            resource_id=r.resource_id,
            ticket_id=r.ticket_id,
            handler_code=r.handler_code,
            ticket_number=r.ticket_number,
            key_code=r.key_code,
            request=request
        ).as_dict() for r in records
    ]


@OrgApp.html(
    model=ResourceCollection,
    name='my-reservations-pdf',
    permission=Public
)
def view_my_reservations_pdf(
    self: ResourceCollection,
    request: OrgRequest
) -> Response:
    """ Returns the reservations as PDF. """
    if not request.app.org.citizen_login_enabled:
        raise exc.HTTPNotFound()

    if not request.authenticated_email:
        raise exc.HTTPForbidden()

    start, end = utils.parse_fullcalendar_request(request, 'Europe/Zurich')

    if not (start and end):
        raise exc.HTTPBadRequest()

    path = module_path('onegov.org', 'queries/my-reservations.sql')
    stmt = as_selectable_from_path(path)

    conditions = [
        func.lower(stmt.c.email) == request.authenticated_email.lower(),
        start <= stmt.c.start,
        stmt.c.start <= end,
    ]

    if request.GET.get('accepted') == '1':
        conditions.append(stmt.c.accepted.is_(True))

    records = request.session.execute(select(stmt.c).where(and_(*conditions)))

    content = MyReservationsPdf.from_reservations(request, [
        utils.MyReservationEventInfo(
            id=r.id,
            token=r.token,
            start=r.start,
            end=r.end,
            accepted=r.accepted,
            timezone=r.timezone,
            resource=r.resource,
            resource_id=r.resource_id,
            ticket_id=r.ticket_id,
            handler_code=r.handler_code,
            ticket_number=r.ticket_number,
            key_code=r.key_code,
            request=request
        ) for r in records
    ], start, end)

    return Response(
        content.read(),
        content_type='application/pdf',
        content_disposition='attachment; filename='
        'my-reservations-{}-{}-{}.pdf'.format(
            request.authenticated_email,
            start.strftime('%Y%m%d'),
            end.strftime('%Y%m%d')
        )
    )


@OrgApp.html(
    model=ResourceCollection,
    permission=Public,
    name='my-reservations',
    template='resource_occupancy.pt'
)
def view_my_reservations(
    self: ResourceCollection,
    request: OrgRequest,
    layout: DefaultLayout | None = None
) -> RenderData:

    assert_citizen_logged_in(request)

    # NOTE: For some reason we need to manually include common
    #       and fullcalendar in addition to occupancycalendar
    #       here. Maybe because we use DefaultLayout?
    request.include('common')
    request.include('fullcalendar')
    request.include('occupancycalendar')

    layout = layout or DefaultLayout(self, request)
    layout.breadcrumbs = [
        Link(_('Homepage'), layout.homepage_url),
        Link(_('Overview'), request.class_link(CitizenDashboard)),
        Link(_('My Reservations'), '#')
    ]

    layout.editbar_links = [
        Link(
            _('Subscribe'),
            request.link(self, 'my-reservations-subscribe'),
            classes={'subscribe-link'}
        )
    ]

    try:
        date = date_t.fromisoformat(request.GET.get('date', ''))
    except Exception:
        date = None

    return {
        'title': _('My Reservations'),
        'resource': Bunch(
            type='room',
            date=date,
            view=request.GET.get('view'),
            highlights_min=request.GET.get('highlights_min'),
            highlights_max=request.GET.get('highlights_max'),
            default_view='timeGridWeek'
        ),
        'layout': layout,
        'feed': request.link(self, name='my-reservations-json'),
        'pdf_url': request.link(self, name='my-reservations-pdf'),
    }


@OrgApp.html(
    model=ResourceCollection,
    template='resource-subscribe.pt',
    permission=Public,
    name='my-reservations-subscribe'
)
def view_my_reservations_subscribe(
    self: ResourceCollection,
    request: OrgRequest,
    layout: DefaultLayout | None = None
) -> RenderData:

    assert_citizen_logged_in(request)

    salt = secrets.token_urlsafe(16)
    url_obj = URL(request.link(self, 'my-reservations-ical'))
    url_obj = url_obj.scheme('webcal')
    token = request.new_url_safe_token(request.authenticated_email, salt)
    url_obj = url_obj.query_param('token', token)
    url_obj = url_obj.query_param('salt', salt)
    url = url_obj.as_string()

    layout = layout or DefaultLayout(self, request)
    layout.breadcrumbs = [
        Link(_('Homepage'), layout.homepage_url),
        Link(_('Overview'), request.class_link(CitizenDashboard)),
        Link(_('My Reservations'), request.url.replace('-subscribe', '')),
        Link(_('Subscribe'), '#')
    ]

    # generate a second url which includes key codes
    if request.app.org.kaba_configurations:
        salt = secrets.token_urlsafe(16)
        url_obj = URL(request.link(self, 'my-reservations-ical'))
        url_obj = url_obj.scheme('webcal')
        token = request.new_url_safe_token(
            [request.authenticated_email, True],
            salt
        )
        url_obj = url_obj.query_param('token', token)
        url_obj = url_obj.query_param('salt', salt)
        key_code_url = url_obj.as_string()
    else:
        key_code_url = None

    return {
        'title': _('Subscribe'),
        'resource': self,
        'layout': layout,
        'url': url,
        'key_code_url': key_code_url,
    }


@OrgApp.view(
    model=ResourceCollection,
    permission=Public,
    name='my-reservations-ical'
)
def view_my_reservations_ical(
    self: ResourceCollection,
    request: OrgRequest
) -> Response:

    token = request.GET.get('token')
    salt = request.GET.get('salt')
    email = request.load_url_safe_token(token, salt, None)
    include_key_code = False
    if email is None:
        raise exc.HTTPForbidden()
    elif isinstance(email, list):
        email, include_key_code = email

    s = utcnow() - timedelta(days=30)
    e = utcnow() + timedelta(days=365)

    cal = icalendar.Calendar()
    cal.add('prodid', '-//OneGov//onegov.org//')
    cal.add('version', '2.0')
    cal.add('method', 'PUBLISH')

    prefix = request.translate(_('My Reservations'))
    cal.add('x-wr-calname', f'{prefix} {request.app.org.title}')
    # generate a unique id for this calendar
    sha1 = hashlib.new('sha1', usedforsecurity=False)
    sha1.update(email.encode('utf-8'))
    sha1.update(request.app.application_id.encode('utf-8'))
    cal.add('x-wr-relcalid', sha1.hexdigest())

    # refresh every 120 minutes by default (Outlook and maybe others)
    cal.add('x-published-ttl', 'PT120M')

    # add allocations/reservations
    date = utcnow()
    path = module_path('onegov.org', 'queries/my-reservations.sql')
    stmt = as_selectable_from_path(path)

    records = request.session.execute(select(stmt.c).where(and_(
        func.lower(stmt.c.email) == email.lower(),
        s <= stmt.c.start, stmt.c.start <= e,
        # only include accepted reservations in ICS file
        stmt.c.accepted.is_(True)
    )))

    ticket_label = request.translate(_('Check request status'))
    key_code_label = request.translate(_('Key Code'))

    for r in records:
        start = r.start
        end = r.end + timedelta(microseconds=1)

        url = request.class_link(Ticket, {
            'handler_code': r.handler_code,
            'id': r.ticket_id
        }, name='status')
        description = f'{r.ticket_number}\n{ticket_label}: {url}'
        if include_key_code and r.key_code:
            description = f'{description}\n{key_code_label}: {r.key_code}'

        evt = icalendar.Event()
        evt.add('uid', f'{r.token}-{r.id}')
        evt.add('summary', r.resource)
        evt.add('location', r.resource)
        evt.add('description', description)
        evt.add('dtstart', standardize_date(start, 'UTC'))
        evt.add('dtend', standardize_date(end, 'UTC'))
        evt.add('dtstamp', date)
        evt.add('url', url)

        cal.add_component(evt)

    suffix = '-with-key-codes' if include_key_code else ''
    filename = f'inline; filename=my-reservations-{email}{suffix}.ics'
    return Response(
        cal.to_ical(),
        content_type='text/calendar',
        content_disposition=filename,
    )


@OrgApp.html(
    model=Resource,
    template='resource-subscribe.pt',
    permission=Private,
    name='subscribe'
)
def view_resource_subscribe(
    self: Resource,
    request: OrgRequest,
    layout: ResourceLayout | None = None
) -> RenderData:

    url_obj = URL(request.link(self, 'ical'))
    url_obj = url_obj.scheme('webcal')

    if url_obj.has_query_param('view'):
        url_obj = url_obj.remove_query_param('view')

    if self.access_token is not None:
        url_obj = url_obj.query_param('access-token', self.access_token)
    url = url_obj.as_string()

    layout = layout or ResourceLayout(self, request)
    layout.breadcrumbs.append(Link(_('Subscribe'), '#'))

    return {
        'title': self.title,
        'resource': self,
        'layout': layout,
        'url': url
    }


@OrgApp.view(model=Resource, permission=Public, name='ical')
def view_ical(self: Resource, request: OrgRequest) -> Response:
    assert self.access_token is not None

    if request.params.get('access-token') != self.access_token:
        raise exc.HTTPForbidden()

    start = utcnow() - timedelta(days=30)
    end = utcnow() + timedelta(days=730)

    cal = icalendar.Calendar()
    cal.add('prodid', '-//OneGov//onegov.org//')
    cal.add('version', '2.0')
    cal.add('method', 'PUBLISH')

    cal.add('x-wr-calname', self.title)
    cal.add('x-wr-relcalid', self.id.hex)

    # refresh every 30 minutes by default (Outlook and maybe others)
    # this is a higher frequency than my-reservations, since it can
    # have quite a bit of activity on busy days
    cal.add('x-published-ttl', 'PT30M')

    # add allocations/reservations
    date = utcnow()
    query = (
        request.session.query(Reservation)
        .join(
            Ticket,
            sa_cast(Ticket.handler_id, UUIDType) == Reservation.token
        )
        .with_entities(
            Reservation.id.label('id'),
            Reservation.token.label('token'),
            Ticket.subtitle.label('title'),
            Ticket.number.label('description'),
            Reservation.start.label('start'),
            Reservation.end.label('end'),
            Ticket.id.label('ticket_id'),
            Ticket.handler_code.label('handler_code'),
            *(
                FormSubmission.data[as_internal_id(field)].astext.label(field)
                for field in self.ical_fields
            )
        )
        .filter(Reservation.status == 'approved')
        .filter(Reservation.resource == self.id)
        .filter(sa_cast(Reservation.data['accepted'], Boolean).is_(True))
        .filter(Reservation.start >= start)
        .filter(Reservation.start <= end)
    )
    if self.ical_fields:
        query = query.outerjoin(
            FormSubmission,
            FormSubmission.id == Reservation.token
        )

    ticket_label = request.translate(_('Ticket'))
    for r in query:
        start = r.start
        end = r.end + timedelta(microseconds=1)

        url = request.class_link(Ticket, {
            'handler_code': r.handler_code,
            'id': r.ticket_id
        })
        description = '\n'.join((
            r.description,
            *(
                f'{field}: {value}'
                for field in self.ical_fields
                if (value := getattr(r, field))
            ),
            f'{ticket_label}: {url}'
        ))
        evt = icalendar.Event()
        evt.add('uid', f'{r.token}-{r.id}')
        evt.add('summary', r.title)
        evt.add('location', self.title)
        evt.add('description', description)
        evt.add('dtstart', standardize_date(start, 'UTC'))
        evt.add('dtend', standardize_date(end, 'UTC'))
        evt.add('dtstamp', date)
        evt.add('url', url)

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
    request: OrgRequest,
    form: ResourceExportForm,
    layout: ResourceLayout | None = None
) -> RenderData | BaseResponse:

    layout = layout or ResourceLayout(self, request)
    layout.breadcrumbs.append(Link(_('Occupancy'), '#'))
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
        'title': _('Export'),
        'form': form,
        'explanation': _('Exports the reservations of the given date range.')
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
    request: OrgRequest,
    form: AllResourcesExportForm,
    layout: ResourceLayout | None = None
) -> RenderData | BaseResponse:

    # FIXME: Why are we using ResouceLayout and not ResourcesLayout?
    #        this is a weird hack, if you want to be able to use the
    #        ResourceLayout with ResourceCollection, then make it work
    #        in the Layout, not by patching the collection...
    self.title = _('Export All')  # type:ignore
    layout = layout or ResourceLayout(self, request)  # type:ignore
    layout.editbar_links = None
    layout.edit_mode = True

    if form.submitted(request):

        default_group = request.translate(_('General'))
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
            request.alert(_('No reservations found for the given date range.'))
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
        'title': _('Export'),
        'form': form,
        'explanation': _(
            'Exports the reservations of all resources in'
            ' a given date range.'
        )
    }


def run_export(
    resource: Resource,
    start: DateLike,
    end: DateLike,
    nested: bool,
    formatter: Callable[[Any], object]
) -> tuple[Callable[[str], tuple[int, str]], list[dict[str, Any]]]:

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
