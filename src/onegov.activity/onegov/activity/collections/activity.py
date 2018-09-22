import sedate

from copy import copy
from enum import IntEnum
from onegov.activity.models import Activity, Occasion, Period
from onegov.activity.utils import num_range_decode
from onegov.activity.utils import num_range_encode
from onegov.activity.utils import date_range_decode
from onegov.activity.utils import date_range_encode
from onegov.activity.utils import merge_ranges
from onegov.activity.utils import overlaps
from onegov.core.collection import Pagination
from onegov.core.utils import increment_name
from onegov.core.utils import is_uuid
from onegov.core.utils import normalize_for_url
from onegov.core.utils import toggle
from sqlalchemy import column
from sqlalchemy import distinct
from sqlalchemy import func
from sqlalchemy import and_, or_
from sqlalchemy import select
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import array
from uuid import UUID


AVAILABILITY_VALUES = {'none', 'few', 'many'}


class ActivityFilter(object):

    # supported filters - should be named with a plural version that can
    # be turned into a singular with the removal of the last s
    # (i.e. slots => slot)
    __slots__ = (
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
        'weekdays',
    )

    singular = {
        'municipalities': 'municipality'
    }

    def __init__(self, **keywords):

        for key in self.__slots__:
            if key in keywords:
                values = set(keywords[key]) if keywords[key] else set()

                if values and hasattr(self, f'adapt_{key}'):
                    values = getattr(self, f'adapt_{key}')(values)

                setattr(self, key, values)
            else:
                setattr(self, key, set())

    @property
    def keywords(self):
        keywords = {}

        for key in self.__slots__:
            if getattr(self, key):
                keywords[key] = self.encode(key, getattr(self, key))

        return keywords

    def toggled(self, **keywords):
        # create a new filter with the toggled values
        toggled = copy(self)

        for key in self.__slots__:
            # support plural and singular
            if key.endswith('s'):
                singular = self.singular.get(key, key[:-1])
            else:
                singular = key

            if singular in keywords:
                value = keywords[singular]
            elif key in keywords:
                value = keywords[key]
            else:
                continue

            setattr(toggled, key, toggle(getattr(self, key), value))

        return toggled

    def adapt_available(self, values):
        return values & AVAILABILITY_VALUES

    def adapt_num_ranges(self, values):
        decoded = set(v for v in map(num_range_decode, values) if v)
        return decoded and set(merge_ranges(decoded)) or set()

    def adapt_age_ranges(self, values):
        return self.adapt_num_ranges(values)

    def adapt_price_ranges(self, values):
        return self.adapt_num_ranges(values)

    def adapt_dateranges(self, values):
        return set(v for v in map(date_range_decode, values) if v)

    def adapt_weekdays(self, values):
        return set(int(v) for v in values if v.isdigit())

    def adapt_period_ids(self, values):
        return set(UUID(v) for v in values if is_uuid(v))

    def adapt_durations(self, values):
        return set(int(v) for v in values)

    def encode(self, key, value):
        if isinstance(value, str):
            return value

        if key == 'dateranges':
            return [date_range_encode(v) for v in value]

        if key == 'age_ranges':
            return [num_range_encode(v) for v in value]

        if key == 'price_ranges':
            return [num_range_encode(v) for v in value]

        if isinstance(value, IntEnum):
            return str(int(value))

        if isinstance(value, int):
            return str(value)

        if isinstance(value, UUID):
            return value.hex

        if isinstance(value, (tuple, list, set)):
            return [self.encode(key, v) for v in value]

        raise NotImplementedError()

    def contains_num_range(self, value, ranges):
        for r in ranges:
            if overlaps(r, value):
                return True
        return False

    def contains_age_range(self, age_range):
        return self.contains_num_range(age_range, self.age_ranges)

    def contains_price_range(self, price_range):
        return self.contains_num_range(price_range, self.price_ranges)


class ActivityCollection(Pagination):

    def __init__(self, session, type='*', page=0, filter=None):
        self.session = session
        self.type = type
        self.page = page
        self.filter = filter or ActivityFilter()

    def __eq__(self, other):
        return self.type == other.type and self.page == other.page

    def subset(self):
        return self.query()

    @property
    def page_index(self):
        return self.page

    def page_by_index(self, index):
        return self.__class__(
            self.session,
            type=self.type,
            page=index,
            filter=self.filter
        )

    @property
    def model_class(self):
        return Activity.get_polymorphic_class(self.type, Activity)

    def query_base(self):
        """ Returns the query based used by :meth:`query`. Overriding this
        function is useful to apply a general filter to the query before
        any other filter is applied.

        For example, a policy can be enforced that only allows public
        activites.

        """
        return self.session.query(self.model_class)

    def query(self):
        query = self.query_base()
        model_class = self.model_class

        # activity based filters
        if self.type != '*':
            query = query.filter(model_class.type == self.type)

        if self.filter.tags:
            query = query.filter(
                model_class._tags.has_any(array(self.filter.tags)))

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
        o = self.session.query(Occasion).with_entities(Occasion.activity_id)

        if self.filter.period_ids:
            o = o.filter(Occasion.period_id.in_(self.filter.period_ids))

        if self.filter.durations:
            o = o.filter(Occasion.duration.in_(
                int(d) for d in self.filter.durations))

        if self.filter.age_ranges:
            o = o.filter(or_(
                *(
                    Occasion.age.overlaps(func.int4range(min_age, max_age + 1))
                    for min_age, max_age in self.filter.age_ranges
                )
            ))

        if self.filter.price_ranges:
            o = o.join(Period)
            o = o.filter(or_(
                *(
                    and_(
                        min_price <= func.coalesce(
                            Occasion.cost + Period.occasion_extra_cost
                        ),
                        func.coalesce(
                            Occasion.cost + Period.occasion_extra_cost
                        ) <= max_price
                    ) for min_price, max_price in self.filter.price_ranges
                )
            ))

        if self.filter.dateranges:
            o = o.filter(Occasion.active_days.op('&&')(array(
                tuple(
                    dt.toordinal()
                    for start, end in self.filter.dateranges
                    for dt in sedate.dtrange(start, end)
                )))
            )

        if self.filter.weekdays:
            o = o.filter(
                Occasion.weekdays.op('&&')(array(self.filter.weekdays)))

        if self.filter.available:
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
        if o._criterion is not None:
            query = query.filter(model_class.id.in_(o.subquery()))

        return query

    def for_filter(self, **keywords):
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
            page=0,
            filter=self.filter.toggled(**keywords)
        )

    def by_id(self, id):
        return self.query().filter(Activity.id == id).first()

    def by_name(self, name):
        return self.query().filter(Activity.name == name).first()

    def by_user(self, user):
        return self.query().filter(Activity.username == user.username)

    def by_username(self, username):
        return self.query().filter(Activity.username == username)

    @property
    def used_tags(self):
        """ Returns a list of all the tags used on *all* activites of
        the current type.

        """

        base = self.query_base().with_entities(
            func.skeys(self.model_class._tags).label('keys'))

        query = select([func.array_agg(column('keys'))], distinct=True)
        query = query.select_from(base.subquery())

        tags = self.session.execute(query).scalar()

        return set(tags) if tags else set()

    @property
    def used_municipalities(self):
        """ Returns a list of all the municipalities on *all* activites of
        the current type

        """
        q = self.query_base().with_entities(distinct(Activity.municipality))
        q = q.filter(Activity.municipality != None)

        return set(r[0] for r in q)

    def get_unique_name(self, name):
        """ Given a desired name, finds a variant of that name that's not
        yet used. So if 'foobar' is already used, 'foobar-1' will be returned.

        """
        name = normalize_for_url(name)

        existing = self.session.query(self.model_class)
        existing = existing.filter(Activity.name.like('{}%'.format(name)))
        existing = existing.with_entities(Activity.name)
        existing = set(r[0] for r in existing.all())

        while name in existing:
            name = increment_name(name)

        return name

    def add(self, title, username, lead=None, text=None, tags=None, name=None):

        type = self.type != '*' and self.type or None

        name = name or self.get_unique_name(title)

        activity = self.model_class(
            name=name,
            title=title,
            tags=tags,
            type=type,
            username=username,
            lead=lead,
            text=text
        )

        self.session.add(activity)
        self.session.flush()

        return activity

    def delete(self, activity):
        for occasion in activity.occasions:
            self.session.delete(occasion)

        self.session.delete(activity)
        self.session.flush()

    def available_weeks(self, period):
        if not period:
            return

        weeknumbers = {n[0] for n in self.session.execute(text("""
            SELECT DISTINCT
                EXTRACT(week FROM start::date)
            FROM OCCASION_DATES
                LEFT JOIN occasions
                ON occasion_id = occasions.id
            WHERE period_id = :period_id
        """), {'period_id': period.id})}

        weeks = sedate.weekrange(period.execution_start, period.execution_end)

        for start, end in weeks:
            if sedate.weeknumber(start) in weeknumbers:
                yield start, end
