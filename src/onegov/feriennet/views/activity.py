from __future__ import annotations

import copy
import sedate
import random

from datetime import date, timedelta
from itertools import groupby
from onegov.activity import Activity
from onegov.activity import Booking
from onegov.activity import Occasion
from onegov.activity import OccasionCollection
from onegov.activity import BookingPeriod
from onegov.activity.models import ACTIVITY_STATES, DAYS

from onegov.core.elements import Link, Confirm, Intercooler
from onegov.core.security import Personal
from onegov.core.security import Private
from onegov.core.security import Public
from onegov.core.security import Secret
from onegov.core.utils import normalize_for_url
from onegov.feriennet import _
from onegov.feriennet import FeriennetApp
from onegov.feriennet.collections import VacationActivityCollection
from onegov.feriennet.forms import VacationActivityForm
from onegov.feriennet.layout import VacationActivityCollectionLayout
from onegov.feriennet.layout import VacationActivityFormLayout
from onegov.feriennet.layout import VacationActivityLayout
from onegov.feriennet.models import ActivityMessage
from onegov.feriennet.models import VacationActivity
from onegov.feriennet.models import VolunteerCart
from onegov.feriennet.models import VolunteerCartAction
from onegov.feriennet.utils import (activity_ages, activity_min_cost,
                                    activity_max_cost, activity_spots)
from onegov.org.mail import send_ticket_mail
from onegov.org.models import TicketMessage
from onegov.ticket import TicketCollection
from purl import URL
from re import search
from sedate import dtrange, overlaps
from sqlalchemy import desc
from sqlalchemy.orm import contains_eager
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import undefer
from webob import exc


from typing import Literal, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Sequence
    from onegov.activity.models import OccasionDate
    from onegov.activity.models.occasion_need import OccasionNeed
    from onegov.core.types import JSON_ro, RenderData
    from onegov.feriennet.request import FeriennetRequest
    from onegov.ticket import Ticket
    from sqlalchemy.orm import Session
    from webob import Response


ACTIVITY_STATE_TRANSLATIONS = {
    'preview': _('Preview'),
    'proposed': _('Proposed'),
    'accepted': _('Published'),  # users like the term 'Published' better
    'archived': _('Archived')
}


WEEKDAYS = (
    _('Mo'),
    _('Tu'),
    _('We'),
    _('Th'),
    _('Fr'),
    _('Sa'),
    _('Su')
)


def get_activity_form_class(
    model: VacationActivity | VacationActivityCollection,
    request: FeriennetRequest
) -> type[VacationActivityForm]:

    if isinstance(model, VacationActivityCollection):
        model = VacationActivity()

    return model.with_content_extensions(VacationActivityForm, request)


def occasions_by_period(
    session: Session,
    activity: Activity,
    show_inactive: bool,
    show_archived: bool,
    show_only_inactive: bool = False
) -> tuple[tuple[str, tuple[Occasion, ...]], ...]:

    query = OccasionCollection(session).query()
    query = query.filter(Occasion.activity_id == activity.id)

    query = query.join(Occasion.period)
    query = query.options(contains_eager(Occasion.period))

    if not show_inactive:
        query = query.filter(BookingPeriod.active == True)

    if not show_archived:
        query = query.filter(BookingPeriod.archived == False)

    if show_only_inactive:
        query = query.filter(BookingPeriod.active == False)

    query = query.order_by(
        desc(BookingPeriod.active),
        BookingPeriod.execution_start,
        Occasion.order)

    return tuple(
        (title, tuple(occasions)) for title, occasions in
        groupby(query, key=lambda o: o.period.title)
    )


def filter_link(
    text: str,
    active: bool,
    url: str,
    rounded: bool = False
) -> Link:
    return Link(text=text, active=active, url=url,
                rounded=rounded, attrs={
        'ic-get-from': url
    })


def filter_timelines(
    activity: VacationActivityCollection,
    request: FeriennetRequest
) -> list[Link]:

    links = [
        filter_link(
            text=request.translate(_('Elapsed')),
            active='past' in activity.filter.timelines,
            url=request.link(activity.for_filter(timeline='past'))
        ),
        filter_link(
            text=request.translate(_('Now')),
            active='now' in activity.filter.timelines,
            url=request.link(activity.for_filter(timeline='now'))
        ),
        filter_link(
            text=request.translate(_('Scheduled')),
            active='future' in activity.filter.timelines,
            url=request.link(activity.for_filter(timeline='future'))
        ),
    ]

    if request.is_organiser:
        links.insert(0, filter_link(
            text=request.translate(_('Without')),
            active='undated' in activity.filter.timelines,
            url=request.link(activity.for_filter(timeline='undated'))
        ))

    return links


def filter_tags(
    activity: VacationActivityCollection,
    request: FeriennetRequest
) -> list[Link]:

    links = [
        filter_link(
            text=request.translate(_(tag)),
            active=tag in activity.filter.tags,
            url=request.link(activity.for_filter(tag=tag)),
        ) for tag in activity.used_tags
    ]
    links.sort(key=lambda l: l.text)  # type:ignore

    return links


def filter_durations(
    activity: VacationActivityCollection,
    request: FeriennetRequest
) -> tuple[Link, ...]:

    return tuple(
        filter_link(
            text=request.translate(text),
            active=duration in activity.filter.durations,
            url=request.link(activity.for_filter(duration=duration))
        ) for text, duration in (
            (_('Half day'), DAYS.half),
            (_('Full day'), DAYS.full),
            (_('Multiple days'), DAYS.many),
        )
    )


def filter_ages(
    activity: VacationActivityCollection,
    request: FeriennetRequest
) -> tuple[Link, ...]:

    ages = activity.available_ages()

    if not ages:
        return ()

    def age_filters() -> Iterator[tuple[str, tuple[int, int]]]:
        for age in range(*ages):
            if age < 16:
                yield str(age), (age, age)
            else:
                yield '16+', (16, 99)
                break

    return tuple(
        filter_link(
            text=request.translate(text),
            active=activity.filter.contains_age_range(age_range),
            url=request.link(activity.for_filter(age_range=age_range))
        ) for text, age_range in age_filters()
    )


def filter_price_range(
    activity: VacationActivityCollection,
    request: FeriennetRequest
) -> tuple[Link, ...]:

    return tuple(
        filter_link(
            text=request.translate(text),
            active=activity.filter.contains_price_range(price_range),
            url=request.link(activity.for_filter(price_range=price_range))
        ) for text, price_range in (
            (_('Free of Charge'), (0, 0)),
            (_('Up to 25 CHF'), (1, 25)),
            (_('Up to 50 CHF'), (26, 50)),
            (_('Up to 100 CHF'), (51, 100)),
            (_('More than 100 CHF'), (101, 100000)),
        )
    )


def filter_weeks(
    activity: VacationActivityCollection,
    request: FeriennetRequest
) -> tuple[Link, ...]:

    # FIXME: format_date should be available on the request, so we don't
    #        need to create dummy layouts in order to use it.
    layout = VacationActivityCollectionLayout(activity, request)

    return tuple(
        filter_link(
            text='{} - {}'.format(
                layout.format_date(daterange[0], 'date'),
                layout.format_date(daterange[1], 'date')
            ),
            active=daterange in activity.filter.dateranges,
            url=request.link(activity.for_filter(daterange=daterange))
        ) for nth, daterange in enumerate(
            activity.available_weeks(request.app.active_period),
            start=1
        )
    )


def filter_weekdays(
    activity: VacationActivityCollection,
    request: FeriennetRequest
) -> tuple[Link, ...]:

    return tuple(
        filter_link(
            text=WEEKDAYS[weekday],
            active=weekday in activity.filter.weekdays,
            url=request.link(activity.for_filter(weekday=weekday))
        ) for weekday in range(7)
    )


def filter_available(
    activity: VacationActivityCollection,
    request: FeriennetRequest
) -> tuple[Link, ...]:

    # NOTE: We're helping out mypy's inference here, since it won't
    #       infer the second tuple element as a literal
    availabilities: tuple[
        tuple[str, Literal['none', 'few', 'many']],
        ...
    ] = (
        (_('None'), 'none'),
        (_('Few'), 'few'),
        (_('Many'), 'many'),
    )
    return tuple(
        filter_link(
            text=request.translate(text),
            active=available in activity.filter.available,
            url=request.link(activity.for_filter(available=available))
        ) for text, available in availabilities
    )


def filter_municipalities(
    activity: VacationActivityCollection,
    request: FeriennetRequest
) -> list[Link]:

    links = [
        filter_link(
            text=municipality,
            active=municipality in activity.filter.municipalities,
            url=request.link(activity.for_filter(municipality=municipality))
        ) for municipality in activity.used_municipalities
    ]

    links.sort(key=lambda l: normalize_for_url(l.text))  # type:ignore

    return links


def filter_periods(
    activity: VacationActivityCollection,
    request: FeriennetRequest
) -> list[Link]:

    links = [
        filter_link(
            text=period.title,
            active=period.id in activity.filter.period_ids,
            url=request.link(activity.for_filter(period_id=period.id))
        ) for period in request.app.periods if period
    ]
    links.sort(key=lambda l: l.text)  # type:ignore

    return links


def filter_own(
    activity: VacationActivityCollection,
    request: FeriennetRequest
) -> tuple[Link, ...]:

    assert request.current_username is not None
    return (
        filter_link(
            text=request.translate(_('Own')),
            active=request.current_username in activity.filter.owners,
            url=request.link(
                activity.for_filter(owner=request.current_username))
        ),
    )


def filter_states(
    activity: VacationActivityCollection,
    request: FeriennetRequest
) -> tuple[Link, ...]:

    return tuple(
        filter_link(
            text=ACTIVITY_STATE_TRANSLATIONS[state],
            active=state in activity.filter.states,
            url=request.link(activity.for_filter(state=state))
        ) for state in ACTIVITY_STATES
    )


def is_filtered(filters: dict[str, tuple[str, Sequence[Link]]]) -> bool:
    for links in filters.values():
        for link in links[1]:
            if link.active:
                return True

    return False


def count_active(filter: tuple[str, Sequence[Link]]) -> int:
    return sum(1 for link in filter[1] if link.active)


def adjust_filter_path(
    filters: dict[str, tuple[str, Sequence[Link]]],
    suffix: str
) -> None:

    for links in filters.values():
        for link in links[1]:
            link.attrs['href'] = link.attrs['ic-get-from'] = URL(
                link.attrs['href']).add_path_segment(suffix).as_string()


def exclude_filtered_dates(
    activities: VacationActivityCollection,
    dates: Iterable[OccasionDate]
) -> list[OccasionDate]:

    today = date.today()
    return [
        dt
        for dt in dates

        # only include future date ranges
        if dt.start.date() > today

        # .. that overlap with the selected date ranges
        #    unless we didn't select any date ranges
        if not activities.filter.dateranges or any(
            overlaps(dt.start.date(), dt.end.date(), s, e)
            for s, e in activities.filter.dateranges
        )

        # .. and don't contain a weekday that wasn't selected
        #    unless we didn't select any weekdays
        if not activities.filter.weekdays or all(
            day.weekday() in activities.filter.weekdays
            # NOTE: This is technically quite inefficient for date ranges
            #       that are longer than a week, but realistically most
            #       activities will be much shorter than that.
            for day in dtrange(dt.start, dt.end)
        )
    ]


@FeriennetApp.html(
    model=VacationActivityCollection,
    template='activities.pt',
    permission=Public)
def view_activities(
    self: VacationActivityCollection,
    request: FeriennetRequest
) -> RenderData:

    active_period = request.app.active_period
    show_activities = bool(active_period or request.is_organiser)
    layout = VacationActivityCollectionLayout(self, request)

    filters: dict[str, tuple[str, Sequence[Link]]] = {}

    if show_activities:
        filters['timelines'] = (_('Occasion'), filter_timelines(self, request))
        filters['tags'] = (_('Tags'), filter_tags(self, request))
        filters['durations'] = (_('Duration'), filter_durations(self, request))
        filters['ages'] = (_('Age'), filter_ages(self, request))
        filters['price_range'] = (_('Price'),
                                  filter_price_range(self, request))

        if active_period:
            filters['weeks'] = (_('Weeks'), filter_weeks(self, request))

        filters['weekdays'] = (_('Weekdays'), filter_weekdays(self, request))
        filters['available'] = (_('Free Spots'),
                                filter_available(self, request))
        filters['municipalities'] = (_('Municipalities'),
                                     filter_municipalities(self, request))

        if request.is_organiser:
            if request.app.periods:
                filters['periods'] = (_('Periods'),
                                      filter_periods(self, request))

            filters['own'] = (_('Advanced'), filter_own(self, request))
            filters['states'] = (_('State'), filter_states(self, request))

    filters = {k: v for k, v in filters.items() if v}
    mobile_filters = {k: v for k, v in copy.deepcopy(filters).items() if v}

    all_sponsors = layout.app.banners(request)
    main_sponsor = all_sponsors[0]
    sponsors = all_sponsors[1:len(all_sponsors)]

    activities = list(self.batch) if show_activities else []
    active_filter = request.params.get('active-filter', None)
    adjust_filter_path(filters, suffix='filters')
    adjust_filter_path(mobile_filters, suffix='filters')

    return {
        'activities': activities,
        'main_sponsor': main_sponsor,
        'sponsors': sponsors,
        'random': random,
        'layout': layout,
        'title': _('Activities'),
        'count_active': count_active,
        'filters': filters,
        'mobile_filters': mobile_filters,
        'active_filter': active_filter,
        'filtered': is_filtered(filters),
        'period': active_period,
        'current_location': request.link(
            self.by_page_range((0, self.pages[-1]))),
        'activity_ages': activity_ages,
        'activity_min_cost': activity_min_cost,
        'activity_spots': activity_spots
}


@FeriennetApp.html(
    model=VacationActivityCollection,
    template='activity-filters.pt',
    permission=Public,
    name='filters')
def view_activity_filters(
    self: VacationActivityCollection,
    request: FeriennetRequest
) -> RenderData | Response:

    if not request.is_xhr:
        return request.redirect(request.class_link(VacationActivityCollection))

    active_period = request.app.active_period
    show_activities = bool(active_period or request.is_organiser)
    layout = VacationActivityCollectionLayout(self, request)

    filters: dict[str, tuple[str, Sequence[Link]]] = {}

    if show_activities:
        filters['timelines'] = (_('Occasion'), filter_timelines(self,
                                                                request))
        filters['tags'] = (_('Tags'), filter_tags(self, request))
        filters['durations'] = (_('Duration'), filter_durations(self,
                                                                request))
        filters['ages'] = (_('Age'), filter_ages(self, request))
        filters['price_range'] = (_('Price'), filter_price_range(self,
                                                                 request))

        if active_period:
            filters['weeks'] = (_('Weeks'), filter_weeks(self, request))

        filters['weekdays'] = (_('Weekdays'), filter_weekdays(self, request))
        filters['available'] = (_('Free Spots'),
                                filter_available(self, request))
        filters['municipalities'] = (_('Municipalities'),
                                     filter_municipalities(self, request))

        if request.is_organiser:
            if request.app.periods:
                filters['periods'] = (_('Periods'),
                                      filter_periods(self, request))

            filters['own'] = (_('Advanced'), filter_own(self, request))
            filters['states'] = (_('State'), filter_states(self, request))

    filters = {k: v for k, v in filters.items() if v}
    mobile_filters = {k: v for k, v in copy.deepcopy(filters).items() if v}

    active_filter = request.params.get('active-filter', None)

    return {
        'layout': layout,
        'count_active': count_active,
        'filters': filters,
        'mobile_filters': mobile_filters,
        'active_filter': active_filter,
        'filtered': is_filtered(filters),
        'period': active_period,
    }


@FeriennetApp.json(
    model=VacationActivityCollection,
    name='json',
    permission=Public
)
def view_activities_as_json(
    self: VacationActivityCollection,
    request: FeriennetRequest
) -> JSON_ro:

    self.filter.states = {'accepted'}

    active_period = request.app.active_period

    def image(activity: VacationActivity) -> JSON_ro:
        url = (activity.meta or {}).get('thumbnail')
        return {
            'thumbnail': url,
            'full': url.replace('/thumbnail', '') if url else None
        }

    def age(activity: VacationActivity) -> JSON_ro:
        ages = activity_ages(activity, request)
        min_age = min(age.lower for age in ages) if ages else None
        max_age = max(age.upper - 1 for age in ages) if ages else None
        return {'min': min_age, 'max': max_age}

    def cost(activity: VacationActivity) -> JSON_ro:
        min_cost = activity_min_cost(activity, request)
        max_cost = activity_max_cost(activity, request)
        return {
            'min': float(min_cost) if min_cost is not None else 0.0,
            'max': float(max_cost) if max_cost is not None else 0.0
        }

    def dates(activity: VacationActivity) -> JSON_ro:
        occasion_dates = []
        for occasion in activity.occasions:
            for occasion_date in occasion.dates:
                start = occasion_date.localized_start
                end = occasion_date.localized_end
                occasion_dates.append({
                    'start_date': start.date().isoformat(),
                    'start_time': start.time().isoformat(),
                    'end_date': end.date().isoformat(),
                    'end_time': end.time().isoformat(),
                })
        return occasion_dates

    def zip_code(activity: VacationActivity) -> int | None:
        match = search(r'(\d){4}', activity.location or '')
        return int(match.group()) if match else None

    def coordinates(activity: VacationActivity) -> JSON_ro:
        lat = activity.coordinates.lat if activity.coordinates else None
        lon = activity.coordinates.lon if activity.coordinates else None
        return {'lat': lat, 'lon': lon}

    def tags(activity: VacationActivity) -> JSON_ro:
        period = request.app.active_period
        period_id = period.id if period else None
        durations = sum({
            o.duration
            for o in activity.occasions
            if o.period_id == period_id and o.duration is not None
        })
        return activity.ordered_tags(request, durations)

    provider = request.app.org.title

    if active_period:
        wish_start = None
        wish_end = None
        if active_period.confirmable:
            wish_start = active_period.prebooking_start.isoformat()
            wish_end = active_period.prebooking_end.isoformat()

        return {
            'period_name': active_period.title,
            'wish_phase_start': wish_start,
            'wish_phase_end': wish_end,
            'booking_phase_start': active_period.booking_start.isoformat(),
            'booking_phase_end': active_period.booking_end.isoformat(),
            'deadline_days': active_period.deadline_days,
            'activities': [
                {
                    'provider': provider,
                    'url': request.link(activity),
                    'title': activity.title,
                    'lead': (activity.meta or {}).get('lead', ''),
                    'image': image(activity),
                    'age': age(activity),
                    'cost': cost(activity),
                    'spots': activity_spots(activity, request),
                    'dates': dates(activity),
                    'location': activity.location,
                    'zip_code': zip_code(activity),
                    'coordinate': coordinates(activity),
                    'tags': tags(activity),
                } for activity in self.query().options(
                    joinedload(Activity.occasions),
                    undefer(Activity.content))
            ]
        }
    else:
        return {}


@FeriennetApp.html(
    model=VacationActivityCollection,
    template='activities-for-volunteers.pt',
    permission=Public,
    name='volunteer')
def view_activities_for_volunteers(
    self: VacationActivityCollection,
    request: FeriennetRequest
) -> RenderData:

    if not request.app.show_volunteers(request):
        raise exc.HTTPForbidden()

    active_period = request.app.active_period
    show_activities = bool(active_period or request.is_organiser)

    layout = VacationActivityCollectionLayout(self, request)
    layout.breadcrumbs[-1].text = _('Join as a Volunteer')
    layout.editbar_links = []

    # always limit to activities seeking volunteers
    self.filter.volunteers = {True}

    # include javascript part
    request.include('volunteer-cart')

    filters: dict[str, tuple[str, Sequence[Link]]] = {}

    if show_activities:

        filters['tags'] = (_('Tags'), filter_tags(self, request))
        filters['durations'] = (_('Duration'),
                                filter_durations(self, request))

        if active_period:
            filters['weeks'] = (_('Weeks'), filter_weeks(self, request))
            self.filter.period_ids = {active_period.id}

        filters['weekdays'] = (_('Weekday'), filter_weekdays(self, request))
        filters['municipalities'] = (_('Municipalities'),
                                     filter_municipalities(self, request))

    filters = {k: v for k, v in filters.items() if v}
    mobile_filters = {k: v for k, v in copy.deepcopy(filters).items() if v}
    active_filter = request.params.get('active-filter', None)
    adjust_filter_path(filters, suffix='volunteer')
    adjust_filter_path(mobile_filters, suffix='volunteer')

    def occasions_for_volunteer(
        activity: Activity,
    ) -> list[Occasion]:

        query = OccasionCollection(request.session).query()
        query = query.filter(Occasion.activity_id == activity.id)

        query = query.join(Occasion.period)
        query = query.options(contains_eager(Occasion.period))

        query = query.filter(BookingPeriod.active == True)
        query = query.filter(BookingPeriod.archived == False)

        query = query.order_by(
            desc(BookingPeriod.active),
            BookingPeriod.execution_start,
            Occasion.order)

        return query.all()

    def wants_more_volunteers(need: OccasionNeed) -> bool:
        needed = need.number.upper - 1
        current = sum(v.state == 'confirmed' for v in need.volunteers)
        return current < needed

    self.batch_size = 24

    return {
        'activities': self.batch if show_activities else None,
        'layout': layout,
        'title': _('Join as a Volunteer'),
        'filters': filters,
        'mobile_filters': mobile_filters,
        'active_filter': active_filter,
        'count_active': count_active,
        'filtered': is_filtered(filters),
        'period': active_period,
        'exclude_filtered_dates': exclude_filtered_dates,
        'occasions_for_volunteer': occasions_for_volunteer,
        'wants_more_volunteers': wants_more_volunteers,
        'cart_url': request.class_link(VolunteerCart),
        'cart_submit_url': request.class_link(VolunteerCart, name='submit'),
        'cart_action_url': request.class_link(VolunteerCartAction, {
            'action': 'action',
            'target': 'target',
        }),
        'current_location': request.link(
            self.by_page_range((0, self.pages[-1])), name='volunteer'),
        'activity_ages': activity_ages,
        'activity_min_cost': activity_min_cost,
        'activity_spots': activity_spots
    }


@FeriennetApp.html(
    model=VacationActivity,
    template='activity.pt',
    permission=Public)
def view_activity(
    self: VacationActivity,
    request: FeriennetRequest
) -> RenderData:

    session = request.session
    layout = VacationActivityLayout(self, request)

    occasion_ids = {o.id for o in self.occasions}
    occasion_ids_with_bookings = occasion_ids and {
        b.occasion_id for b in session.query(Booking)
        .with_entities(Booking.occasion_id)
        .filter(Booking.occasion_id.in_(occasion_ids))
    } or set()

    def occasion_links(o: Occasion) -> Iterator[Link]:

        if not o.period.archived and (o.period.active or request.is_admin):
            yield Link(text=_('Edit'), url=request.link(o, name='edit'))

        yield Link(text=_('Clone'), url=request.link(o, name='clone'))

        title = layout.format_datetime_range(
            o.dates[0].localized_start,
            o.dates[0].localized_end
        )
        can_cancel = not o.cancelled and (
            request.is_admin or not o.period.finalized
        )

        if o.cancelled and not o.period.finalized:
            yield Link(
                text=_('Reinstate'),
                url=layout.csrf_protected_url(
                    request.link(o, name='reinstate')
                ),
                traits=(
                    Confirm(
                        _(
                            'Do you really want to reinstate "${title}"?',
                            mapping={'title': title}
                        ),
                        _('Previous attendees need to re-apply'),
                        _('Reinstate Occasion'),
                        _('Cancel')
                    ),
                    Intercooler(
                        request_method='POST',
                        redirect_after=request.link(self)
                    )
                )
            )
        elif o.id in occasion_ids_with_bookings and can_cancel:
            yield Link(
                text=_('Rescind'),
                url=layout.csrf_protected_url(request.link(o, name='cancel')),
                traits=(
                    Confirm(
                        _(
                            'Do you really want to rescind "${title}"?',
                            mapping={'title': title}
                        ),
                        _(
                            '${count} already accepted bookings will '
                            'be cancelled', mapping={'count': o.attendee_count}
                        ),
                        _(
                            'Rescind Occasion'
                        ),
                        _(
                            'Cancel'
                        )
                    ),
                    Intercooler(
                        request_method='POST',
                        redirect_after=request.link(self)
                    )
                )
            )
        elif o.id not in occasion_ids_with_bookings:
            yield Link(
                text=_('Delete'),
                url=layout.csrf_protected_url(request.link(o)),
                traits=(
                    Confirm(
                        _('Do you really want to delete "${title}"?', mapping={
                            'title': title
                        }),
                        _(
                            'There are no accepted bookings associated with '
                            'this occasion, though there might be '
                            'cancelled/blocked bookings which will be deleted.'
                        ),
                        _('Delete Occasion'),
                        _('Cancel')
                    ),
                    Intercooler(
                        request_method='DELETE',
                        redirect_after=request.link(self)
                    )
                )
            )

    def show_enroll(occasion: Occasion) -> bool:
        if self.state != 'accepted':
            return False

        if not occasion.period.active:
            return False

        if occasion.cancelled:
            return False

        if occasion.full and occasion.period.phase != 'wishlist':
            return False

        # the rest of the restrictions only apply to non-admins
        if request.is_admin:
            return True

        if occasion.period.finalized and not occasion.period.book_finalized:
            return False

        acceptable_phases: tuple[str, ...]
        if occasion.period.finalized and occasion.period.book_finalized:
            acceptable_phases = ('wishlist', 'booking', 'execution', 'payment')
        else:
            acceptable_phases = ('wishlist', 'booking', 'execution')

        if occasion.period.phase not in acceptable_phases:
            return False

        if occasion.is_past_deadline(sedate.utcnow()):
            return False

        if (
            occasion.period.wishlist_phase
            and occasion.period.is_prebooking_in_past
        ):
            return False

        return True

    phases = []
    active_period = request.app.active_period
    text_until = request.translate(_('Until'))
    text_from = request.translate(_('Starts at'))

    # Booking date
    if active_period and not active_period.book_finalized:
        text = text_until
        date = active_period.booking_end
        if active_period.is_booking_in_future:
            text = text_from
            date = active_period.booking_start
        phases.append(
            f'{text} {layout.format_date(date, "date_long")}')
    # Pre booking date
    if (active_period and active_period.wishlist_phase
        ) and not active_period.is_prebooking_in_past:
        text = text_until
        date = active_period.prebooking_end
        if active_period.is_prebooking_in_future:
            text = text_from
            date = active_period.prebooking_start
        phases.append(
            f'{text} {layout.format_date(date, "date_long")}')

    return {
        'layout': layout,
        'title': self.title,
        'activity': self,
        'show_enroll': show_enroll,
        'occasion_links': occasion_links,
        'occasions_current_period': occasions_by_period(
            session=session,
            activity=self,
            show_inactive=False,
            show_archived=request.is_admin or (
                request.is_organiser
                and self.username == request.current_username
            )
        ),
        'occasions_by_period': occasions_by_period(
            session=session,
            activity=self,
            show_inactive=request.is_organiser,
            show_archived=request.is_admin or (
                request.is_organiser
                and self.username == request.current_username
            ),
            show_only_inactive=True
        ),
        'phases_date': phases
    }


@FeriennetApp.form(
    model=VacationActivityCollection,
    template='form.pt',
    form=get_activity_form_class,
    permission=Private,
    name='new')
def new_activity(
    self: VacationActivityCollection,
    request: FeriennetRequest,
    form: VacationActivityForm
) -> RenderData | Response:

    if form.submitted(request):
        assert form.title.data is not None
        assert request.current_username is not None
        activity = self.add(
            title=form.title.data,
            username=request.current_username)

        form.populate_obj(activity)

        return request.redirect(request.link(activity))

    layout = VacationActivityFormLayout(self, request, _('New Activity'))
    layout.edit_mode = True

    return {
        'layout': layout,
        'title': _('New Activity'),
        'form': form
    }


@FeriennetApp.form(
    model=VacationActivity,
    template='form.pt',
    form=get_activity_form_class,
    permission=Private,
    name='edit')
def edit_activity(
    self: VacationActivity,
    request: FeriennetRequest,
    form: VacationActivityForm
) -> RenderData | Response:

    if form.submitted(request):
        old_username = self.username
        form.populate_obj(self)
        new_username = self.username

        if old_username != new_username:

            # if there is already a ticket..
            ticket = relevant_ticket(self, request)

            if ticket:

                # ..note the change
                ActivityMessage.create(
                    ticket, request, 'reassign',
                    old_username=old_username,
                    new_username=new_username
                )

        request.success(_('Your changes were saved'))

        return request.redirect(request.link(self))

    elif not request.POST:
        form.process(obj=self)

    layout = VacationActivityFormLayout(self, request, _('Edit Activity'))
    layout.edit_mode = True

    return {
        'layout': layout,
        'title': self.title,
        'form': form
    }


@FeriennetApp.view(
    model=VacationActivity,
    permission=Private,
    request_method='DELETE')
def discard_activity(
    self: VacationActivity,
    request: FeriennetRequest
) -> None:

    request.assert_valid_csrf_token()

    # discard really is like delete, but activites can only be deleted
    # before they are submitted for publication, so 'discard' is a more
    # accurate description
    if self.state != 'preview':
        raise exc.HTTPMethodNotAllowed()

    activities = VacationActivityCollection(
        request.session,
        identity=request.identity
    )
    activities.delete(self)

    request.success(_('The activity was discarded'))


@FeriennetApp.view(
    model=VacationActivity,
    permission=Private,
    name='propose',
    request_method='POST')
def propose_activity(
    self: VacationActivity,
    request: FeriennetRequest
) -> None:

    assert request.app.active_period, 'An active period is required'

    # if the latest request has been done in the last minute, this is a
    # duplicate and should be ignored
    latest = self.latest_request

    if latest and (sedate.utcnow() - timedelta(seconds=60)) < latest.created:
        return

    session = request.session

    with session.no_autoflush:
        self.propose()

        publication_request = self.create_publication_request(
            request.app.active_period.materialize(request.session))

        ticket = TicketCollection(session).open_ticket(
            handler_code='FER',
            handler_id=publication_request.id.hex
        )
        TicketMessage.create(ticket, request, 'opened', 'external')

    send_ticket_mail(
        request=request,
        template='mail_ticket_opened.pt',
        subject=_('Your ticket has been opened'),
        receivers=(self.username, ),
        ticket=ticket,
        force=(
            request.is_organiser_only
            or request.current_username != self.username
        )
    )
    if request.email_for_new_tickets:
        send_ticket_mail(
            request=request,
            template='mail_ticket_opened_info.pt',
            subject=_('New ticket'),
            ticket=ticket,
            receivers=(request.email_for_new_tickets, ),
            content={
                'model': ticket
            }
        )

    request.app.send_websocket(
        channel=request.app.websockets_private_channel,
        message={
            'event': 'browser-notification',
            'title': request.translate(_('New ticket')),
            'created': ticket.created.isoformat()
        },
        groupids=request.app.groupids_for_ticket(ticket),
    )

    request.success(_('Thank you for your proposal!'))

    @request.after
    def redirect_intercooler(response: Response) -> None:
        response.headers.add('X-IC-Redirect', request.link(ticket, 'status'))

    # do not redirect here, intercooler doesn't deal well with that...
    return


@FeriennetApp.view(
    model=VacationActivity,
    permission=Secret,
    name='accept',
    request_method='POST')
def accept_activity(
    self: VacationActivity,
    request: FeriennetRequest
) -> None:

    return administer_activity(
        model=self,
        request=request,
        action='accept',
        template='mail_activity_accepted.pt',
        subject=_('Your activity has been published')
    )


@FeriennetApp.view(
    model=VacationActivity,
    permission=Secret,
    name='archive',
    request_method='POST')
def archive_activity(
    self: VacationActivity,
    request: FeriennetRequest
) -> None:

    return administer_activity(
        model=self,
        request=request,
        action='archive',
        template='mail_activity_archived.pt',
        subject=_('Your activity has been archived')
    )


@FeriennetApp.view(
    model=VacationActivity,
    permission=Personal,
    name='offer-again',
    request_method='POST')
def offer_activity_again(
    self: VacationActivity,
    request: FeriennetRequest
) -> None:

    assert self.state in ('archived', 'preview')

    if self.state == 'archived':
        self.state = 'preview'

    @request.after
    def redirect_intercooler(response: Response) -> None:
        response.headers.add('X-IC-Redirect', request.link(self, 'edit'))


def relevant_ticket(
    activity: VacationActivity,
    request: FeriennetRequest
) -> Ticket | None:

    pr = (activity.request_by_period(request.app.active_period)
          or activity.latest_request)

    if pr:
        return TicketCollection(request.session).by_handler_id(pr.id.hex)
    return None


def administer_activity(
    model: VacationActivity,
    request: FeriennetRequest,
    action: str,
    template: str,
    subject: str
) -> None:

    ticket = relevant_ticket(model, request)
    if not ticket:
        raise RuntimeError(
            f'No ticket found for {model.name}, when performing {action}')

    # execute state change
    getattr(model, action)()

    send_ticket_mail(
        request=request,
        template=template,
        subject=subject,
        receivers=(model.username, ),
        ticket=ticket,
        content={
            'model': model,
            'ticket': ticket
        }
    )

    ActivityMessage.create(ticket, request, action)

    @request.after
    def redirect_intercooler(response: Response) -> None:
        response.headers.add('X-IC-Redirect', request.link(ticket))

    # do not redirect here, intercooler doesn't deal well with that...
    return
