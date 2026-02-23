from __future__ import annotations

import secrets
import sedate

from copy import copy
from enum import IntEnum
from onegov.activity.models import Activity, BookingPeriod
from onegov.activity.models import Occasion, OccasionDate
from onegov.activity.utils import date_range_decode
from onegov.activity.utils import date_range_encode
from onegov.activity.utils import merge_ranges
from onegov.activity.utils import num_range_decode
from onegov.activity.utils import num_range_encode
from onegov.activity.utils import overlaps
from onegov.core.collection import RangedPagination
from onegov.core.utils import increment_name
from onegov.core.utils import is_uuid
from onegov.core.utils import normalize_for_url
from onegov.core.utils import toggle
from sedate import utcnow
from sqlalchemy import and_, or_, not_
from sqlalchemy import column
from sqlalchemy import distinct
from sqlalchemy import exists
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import array
from uuid import UUID


from typing import overload, Literal, TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Collection, Iterable, Iterator
    from datetime import date
    from markupsafe import Markup
    from onegov.activity.models import BookingPeriodMeta
    from onegov.activity.models.activity import ActivityState
    from onegov.user import User
    from sqlalchemy.orm import Query, Session
    from typing_extensions import TypedDict, Unpack
    from typing import Self, TypeAlias

    AvailabilityType: TypeAlias = Literal['none', 'few', 'many']
    FilterKey: TypeAlias = Literal[
        'age_ranges',
        'available',
        'price_ranges',
        'dateranges',
        'durations',
        'municipalities',
        'owners',
        'period_ids',
        'states',
        'tags',
        'timelines',
        'weekdays',
        'volunteers',
    ]

    # TODO: We may want to use PEP-728 for extra items once it's available
    #       to use in mypy
    class FilterArgs(TypedDict, total=False):
        age_ranges: Collection[str] | None
        available: Collection[str] | None
        price_ranges: Collection[str] | None
        dateranges: Collection[str] | None
        durations: Collection[str] | None
        municipalities: Collection[str] | None
        owners: Collection[str] | None
        period_ids: Collection[str] | None
        states: Collection[str] | None
        tags: Collection[str] | None
        timelines: Collection[str] | None
        weekdays: Collection[str] | None
        volunteers: Collection[str] | None

    class ToggledArgs(TypedDict, total=False):
        age_range: tuple[int, int]
        available: AvailabilityType
        price_range: tuple[int, int]
        daterange: tuple[date, date]
        duration: int
        municipality: str
        owner: str
        period_id: UUID
        state: ActivityState
        tag: str
        timeline: str
        weekday: int
        volunteer: bool


ActivityT = TypeVar('ActivityT', bound=Activity)
AVAILABILITY_VALUES: set[AvailabilityType] = {'none', 'few', 'many'}


class ActivityFilter:

    # supported filters - should be named with a plural version that can
    # be turned into a singular with the removal of the last s
    # (i.e. slots => slot)
    __slots__: tuple[FilterKey, ...] = (
        'age_ranges',
        'available',
        'price_ranges',
        'dateranges',
        'durations',
        'municipalities',
        'owners',
        'period_ids',
        'states',
        'tags',
        'timelines',
        'weekdays',
        'volunteers',
    )

    singular = {
        'municipalities': 'municipality'
    }

    age_ranges: set[tuple[int, int]]
    available: set[AvailabilityType]
    price_ranges: set[tuple[int, int]]
    dateranges: set[tuple[date, date]]
    durations: set[int]
    municipalities: set[str]
    owners: set[str]
    period_ids: set[UUID]
    states: set[ActivityState]
    tags: set[str]
    timelines: set[str]
    weekdays: set[int]
    volunteers: set[bool]

    def __init__(self, **keywords: Unpack[FilterArgs]) -> None:
        for key in self.__slots__:
            if key in keywords:
                values = set(v) if (v := keywords[key]) else set()

                if values and hasattr(self, f'adapt_{key}'):
                    try:
                        values = getattr(self, f'adapt_{key}')(values)
                    except ValueError:
                        values = set()

                setattr(self, key, values)
            else:
                setattr(self, key, set())

    @property
    def keywords(self) -> dict[FilterKey, str | list[str]]:
        return {
            key: self.encode(key, value)
            for key in self.__slots__
            if (value := getattr(self, key))
        }

    def toggled(self, **keywords: Unpack[ToggledArgs]) -> Self:
        # create a new filter with the toggled values
        toggled = copy(self)

        for key in self.__slots__:

            # support plural and singular
            if key.endswith('s'):
                singular = self.singular.get(key, key[:-1])
            else:
                singular = key

            if singular in keywords:
                value = keywords[singular]  # type:ignore[literal-required]
            elif key in keywords:
                value = keywords[key]  # type:ignore[typeddict-item]
            else:
                continue

            setattr(toggled, key, toggle(getattr(self, key), value))

        return toggled

    def adapt_available(self, values: set[str]) -> set[str]:
        return values & AVAILABILITY_VALUES

    def adapt_num_ranges(self, values: set[str]) -> set[tuple[int, int]]:
        decoded = {v for v in map(num_range_decode, values) if v}
        return decoded and set(merge_ranges(decoded)) or set()

    def adapt_age_ranges(self, values: set[str]) -> set[tuple[int, int]]:
        return self.adapt_num_ranges(values)

    def adapt_price_ranges(self, values: set[str]) -> set[tuple[int, int]]:
        return self.adapt_num_ranges(values)

    def adapt_dateranges(self, values: set[str]) -> set[tuple[date, date]]:
        return {v for v in map(date_range_decode, values) if v}

    def adapt_weekdays(self, values: set[str]) -> set[int]:
        return {int(v) for v in values if v.isdigit()}

    def adapt_period_ids(self, values: set[str]) -> set[UUID]:
        return {UUID(v) for v in values if is_uuid(v)}

    def adapt_durations(self, values: set[str]) -> set[int]:
        return {int(v) for v in values}

    def adapt_volunteers(self, values: set[str]) -> set[bool]:
        return {v == 'yes' for v in values}

    def encode(self, key: str, value: object) -> str | list[str]:
        if isinstance(value, str):
            return value

        if key == 'dateranges':
            assert hasattr(value, '__iter__')
            return [date_range_encode(v) for v in value]

        if key == 'age_ranges':
            assert hasattr(value, '__iter__')
            return [num_range_encode(v) for v in value]

        if key == 'price_ranges':
            assert hasattr(value, '__iter__')
            return [num_range_encode(v) for v in value]

        if isinstance(value, IntEnum):
            return str(int(value))

        if isinstance(value, int):
            return str(value)

        if isinstance(value, UUID):
            return value.hex

        if isinstance(value, bool):
            return value and 'yes' or 'no'

        if isinstance(value, (tuple, list, set)):
            # NOTE: We assume no nesting beyond the first level
            return [self.encode(key, v) for v in value]  # type:ignore[misc]

        raise NotImplementedError()

    def contains_num_range(
        self,
        value: tuple[int, int],
        ranges: Iterable[tuple[int, int]]
    ) -> bool:
        for r in ranges:
            if overlaps(r, value):
                return True
        return False

    def contains_age_range(self, age_range: tuple[int, int]) -> bool:
        return self.contains_num_range(age_range, self.age_ranges)

    def contains_price_range(self, price_range: tuple[int, int]) -> bool:
        return self.contains_num_range(price_range, self.price_ranges)


class ActivityCollection(RangedPagination[ActivityT]):

    @overload
    def __init__(
        self: ActivityCollection[Activity],
        session: Session,
        type: Literal['*', 'generic'] = '*',
        pages: tuple[int, int] | None = None,
        filter: ActivityFilter | None = None
    ) -> None: ...

    @overload
    def __init__(
        self,
        session: Session,
        type: str,
        pages: tuple[int, int] | None = None,
        filter: ActivityFilter | None = None
    ) -> None: ...

    def __init__(
        self,
        session: Session,
        type: str = '*',
        pages: tuple[int, int] | None = None,
        filter: ActivityFilter | None = None
    ) -> None:
        self.session = session
        self.type = type
        self.pages = pages or (0, 0)
        self.filter = filter or ActivityFilter()

    def subset(self) -> Query[ActivityT]:
        return self.query()

    @property
    def page_range(self) -> tuple[int, int]:
        return self.pages

    def by_page_range(self, page_range: tuple[int, int] | None) -> Self:
        return self.__class__(
            self.session,
            type=self.type,
            pages=page_range,
            filter=self.filter
        )

    @property
    def model_class(self) -> type[ActivityT]:
        return Activity.get_polymorphic_class(  # type:ignore[return-value]
            self.type,
            Activity  # type:ignore[arg-type]
        )

    def query_base(self) -> Query[ActivityT]:
        """ Returns the query based used by :meth:`query`. Overriding this
        function is useful to apply a general filter to the query before
        any other filter is applied.

        For example, a policy can be enforced that only allows public
        activites.

        """
        return self.session.query(self.model_class)

    def query(self) -> Query[ActivityT]:
        query = self.query_base()
        model_class = self.model_class

        # activity based filters
        if self.type != '*':
            query = query.filter(model_class.type == self.type)

        if self.filter.tags:
            query = query.filter(
                model_class._tags.has_any(array(self.filter.tags))
            )

        if self.filter.states:
            query = query.filter(
                model_class.state.in_(self.filter.states))

        if self.filter.owners:
            query = query.filter(model_class.username.in_(
                self.filter.owners))

        if self.filter.municipalities:
            query = query.filter(
                model_class.municipality.in_(self.filter.municipalities))

        # occasion based filters
        o = self.session.query(Occasion).with_entities(
            Occasion.activity_id
        ).join(OccasionDate).distinct()

        # if we are looking at activities without occasions, we do not have
        # to apply all the filters below which are occasion-based
        if 'undated' in self.filter.timelines:
            if self.filter.period_ids:
                return query.filter(
                    not_(self.session.query(Occasion.activity_id).filter(and_(
                        Occasion.activity_id == Activity.id,
                        Occasion.period_id.in_(self.filter.period_ids)
                    )).exists())
                )
            else:
                return query.filter(
                    not_(self.session.query(Occasion.activity_id).filter(
                        Occasion.activity_id == Activity.id,
                    ).exists())
                )

        now = utcnow()

        filters_applied = False
        if self.filter.timelines:
            conditions = []

            if 'past' in self.filter.timelines:
                conditions.append(OccasionDate.end < now)

            if 'now' in self.filter.timelines:
                conditions.append(and_(
                    OccasionDate.start <= now, now <= OccasionDate.end
                ))

            if 'future' in self.filter.timelines:
                conditions.append(now < OccasionDate.start)

            # the 'undated' option can only be implemented further down
            # when we apply the occasion conditions to the activites query
            # since we'd be looking for activities without occasions
            if conditions:
                filters_applied = True
                o = o.filter(or_(*conditions))

        if self.filter.volunteers:
            filters_applied = True
            o = o.filter(Occasion.seeking_volunteers.in_(
                self.filter.volunteers))

        if self.filter.period_ids:
            filters_applied = True
            o = o.filter(Occasion.period_id.in_(self.filter.period_ids))

        if self.filter.durations:
            filters_applied = True
            o = o.filter(Occasion.duration.in_(
                int(d) for d in self.filter.durations))

        if self.filter.age_ranges:
            filters_applied = True
            o = o.filter(or_(
                *(
                    Occasion.age.overlaps(
                        func.int4range(min_age, max_age + 1))
                    for min_age, max_age in self.filter.age_ranges
                )
            ))

        if self.filter.price_ranges:
            filters_applied = True
            o = o.join(BookingPeriod)
            o = o.filter(or_(
                *(
                    and_(
                        min_price <= Occasion.total_cost,
                        Occasion.total_cost <= max_price,
                    ) for min_price, max_price in self.filter.price_ranges
                )
            ))

        if self.filter.dateranges:
            filters_applied = True
            o = o.filter(Occasion.active_days.op('&&')(array(
                    dt.toordinal()
                    for start, end in self.filter.dateranges
                    for dt in sedate.dtrange(start, end)
                ))
            )

        if self.filter.weekdays:
            filters_applied = True
            o = o.filter(
                Occasion.weekdays.op('<@')(array(self.filter.weekdays))
            )

        if self.filter.available:
            filters_applied = True
            conditions = []

            for amount in self.filter.available:
                if amount == 'none':
                    conditions.append(Occasion.available_spots == 0)

                elif amount == 'few':
                    conditions.append(Occasion.available_spots.in_((1, 2, 3)))

                elif amount == 'many':
                    conditions.append(Occasion.available_spots >= 4)

            o = o.filter(or_(*conditions))

        # if no filter was applied to the occasion subquery, we ignore it since
        # we would otherwise get zero results
        if filters_applied:
            query = query.filter(model_class.id.in_(o.scalar_subquery()))

        return query.order_by(self.model_class.order)

    def for_filter(
        self,
        **keywords: Unpack[ToggledArgs]
    ) -> Self:
        """ Returns a new collection instance.

        The given tag is excluded if already in the list, included if not
        yet in the list. Same goes for the given state.

        Note that dateranges are excluded only if they match exactly. That is
        we don't care about overlaps at all. If the same exact daterange is
        found in the filter, it is excluded.

        """

        return self.__class__(
            session=self.session,
            type=self.type,
            pages=(0, 0),
            filter=self.filter.toggled(**keywords)
        )

    def by_id(self, id: UUID) -> ActivityT | None:
        return self.query().filter(Activity.id == id).first()

    def by_name(self, name: str) -> ActivityT | None:
        return self.query().filter(Activity.name == name).first()

    def by_user(self, user: User) -> Query[ActivityT]:
        return self.query().filter(Activity.username == user.username)

    def by_username(self, username: str) -> Query[ActivityT]:
        return self.query().filter(Activity.username == username)

    @property
    def used_tags(self) -> set[str]:
        """ Returns a list of all the tags used on *all* activites of
        the current type.

        """

        base = self.query_base().with_entities(
            func.skeys(self.model_class._tags).label('keys'))

        query = select(func.array_agg(column('keys')))  # type: ignore[var-annotated]
        query = query.select_from(base.subquery())

        tags = self.session.execute(query.distinct()).scalar()

        return set(tags) if tags else set()

    @property
    def used_municipalities(self) -> set[str]:
        """ Returns a list of all the municipalities on *all* activites of
        the current type

        """
        q = self.query_base().with_entities(distinct(Activity.municipality))
        q = q.filter(Activity.municipality != None)

        return {municipality for municipality, in q}

    def get_unique_name(self, name: str) -> str:
        """ Given a desired name, finds a variant of that name that's not
        yet used. So if 'foobar' is already used, 'foobar-1' will be returned.

        """
        name = normalize_for_url(name)

        def name_exists(name: str) -> bool:
            return self.session.query(exists().where(
                Activity.name == name
            )).scalar()

        for _ in range(25):
            if not name_exists(name):
                return name

            name = increment_name(name)

        # FIXME: Technically the random token could exist as well
        return secrets.token_hex(8)

    def add(
        self,
        title: str,
        username: str,
        lead: str | None = None,
        text: Markup | None = None,
        tags: set[str] | None = None,
        name: str | None = None
    ) -> ActivityT:

        type_ = self.type if self.type != '*' else 'generic'

        name = name or self.get_unique_name(title)

        activity = self.model_class(
            name=name,
            title=title,
            tags=tags,
            type=type_,
            username=username,
            lead=lead,
            text=text
        )

        self.session.add(activity)
        self.session.flush()

        return activity

    def delete(self, activity: Activity) -> None:
        for occasion in activity.occasions:
            self.session.delete(occasion)

        self.session.delete(activity)
        self.session.flush()

    def available_weeks(
        self,
        period: BookingPeriod | BookingPeriodMeta | None
    ) -> Iterator[tuple[date, date]]:
        if not period:
            return

        weeknumbers_weeks = {n[:2] for n in self.session.execute(text("""
            SELECT DISTINCT
                EXTRACT(week FROM start::date),
                EXTRACT(week FROM "end"::date)
            FROM OCCASION_DATES
                LEFT JOIN occasions
                ON occasion_id = occasions.id
            WHERE period_id = :period_id
        """), {'period_id': period.id})}

        weeknumbers_weeks = {
            tuple(
                range(int(start), int(end) + 1)
            ) for start, end in weeknumbers_weeks
        }

        weeknumbers = {week for weeks in weeknumbers_weeks for week in weeks}

        weeks = sedate.weekrange(period.execution_start, period.execution_end)

        for start, end in weeks:
            if sedate.weeknumber(start) in weeknumbers:
                yield start, end

    def available_ages(self) -> tuple[int, int] | None:

        # look at all periods because in the filter view where this is used,
        # we cannot differentiate between the periods unless we make
        # filters interdependent
        query = text("""
            SELECT
                COALESCE(MIN(LOWER(age)), 0),
                COALESCE(MAX(UPPER(age)), 100)
            FROM
                occasions
        """)

        ages = self.session.execute(query).first()

        return ages._tuple() if ages else None
