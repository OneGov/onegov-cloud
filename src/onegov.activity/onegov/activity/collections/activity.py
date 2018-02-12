import sedate

from onegov.activity.models import Activity, Occasion
from onegov.activity.utils import merge_ranges, overlaps
from onegov.core.collection import Pagination
from onegov.core.utils import increment_name
from onegov.core.utils import normalize_for_url
from onegov.core.utils import toggle
from sqlalchemy import bindparam
from sqlalchemy import column
from sqlalchemy import distinct
from sqlalchemy import func
from sqlalchemy import Integer
from sqlalchemy import or_
from sqlalchemy import select
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import array


AVAILABILITY_VALUES = {'none', 'few', 'many'}


class ActivityCollection(Pagination):

    def __init__(self, session, type='*', page=0,
                 tags=None,
                 states=None,
                 durations=None,
                 age_ranges=None,
                 owners=None,
                 period_ids=None,
                 dateranges=None,
                 weekdays=None,
                 municipalities=None,
                 available=None):
        self.session = session
        self.type = type
        self.page = page
        self.tags = set(tags) if tags else set()
        self.states = set(states) if states else set()
        self.durations = set(durations) if durations else set()
        self.age_ranges = set(merge_ranges(age_ranges)) \
            if age_ranges else set()
        self.owners = set(owners) if owners else set()
        self.period_ids = set(period_ids) if period_ids else set()
        self.dateranges = set(dateranges) if dateranges else set()
        self.weekdays = set(weekdays) if weekdays else set()
        self.municipalities = set(municipalities) if municipalities else set()
        self.available = set(available) if available else set()

        assert self.available <= AVAILABILITY_VALUES

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
            tags=self.tags,
            states=self.states,
            durations=self.durations,
            age_ranges=self.age_ranges,
            owners=self.owners,
            period_ids=self.period_ids,
            dateranges=self.dateranges,
            weekdays=self.weekdays,
            municipalities=self.municipalities,
            available=self.available
        )

    def contains_age_range(self, age_range):
        for r in self.age_ranges:
            if overlaps(r, age_range):
                return True
        return False

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

        if self.type != '*':
            query = query.filter(model_class.type == self.type)

        if self.tags:
            query = query.filter(model_class._tags.has_any(array(self.tags)))

        if self.states:
            query = query.filter(model_class.state.in_(self.states))

        if self.durations:
            conditions = tuple(
                func.coalesce(model_class.durations, 0).op('&')(int(d)) > 0
                for d in self.durations
            )
            query = query.filter(or_(*conditions))

        if self.age_ranges:
            conditions = []

            # SQLAlchemy needs unique parameter names if multiple text
            # queries with bind params are used
            for i, (min_age, max_age) in enumerate(self.age_ranges, start=1):
                stmt = "'[:min_{i},:max_{i}]'::int4range && ANY(ages)".format(
                    i=i)

                conditions.append(text(stmt).bindparams(
                    bindparam('min_' + str(i), min_age, type_=Integer),
                    bindparam('max_' + str(i), max_age, type_=Integer),
                ))

            query = query.filter(or_(*conditions))

        if self.owners:
            conditions = tuple(
                model_class.username == username for username in self.owners)

            query = query.filter(or_(*conditions))

        if self.period_ids:
            query = query.filter(
                model_class.period_ids.op('&&')(array(self.period_ids)))

        if self.dateranges:
            query = query.filter(
                model_class.active_days.op('&&')(array(
                    tuple(
                        dt.toordinal()
                        for start, end in self.dateranges
                        for dt in sedate.dtrange(start, end)
                    )
                ))
            )

        if self.weekdays:
            query = query.filter(
                model_class.weekdays.op('&&')(array(self.weekdays)))

        if self.municipalities:
            query = query.filter(
                model_class.municipality.in_(self.municipalities))

        if self.available:
            spots = set()

        if 'none' in self.available:
            spots.add(0)

        if 'few' in self.available:
            spots.update((1, 2))

        if 'many' in self.available:
            spots.update(range(3, 1000))

        if self.available and self.available < AVAILABILITY_VALUES:
            queries = []

            stub = self.session.query(Occasion)
            stub = stub.with_entities(Occasion.activity_id)
            stub = stub.group_by(Occasion.activity_id)

            for amount in self.available:
                if amount == 'none':
                    queries.append(
                        model_class.id.in_(
                            stub.having(
                                func.sum(Occasion.available_spots) == 0
                            )
                        )
                    )
                elif amount == 'few':
                    queries.append(
                        model_class.id.in_(
                            stub.having(
                                func.sum(Occasion.available_spots).in_(
                                    (1, 2, 3)
                                )
                            )
                        )
                    )
                elif amount == 'many':
                    queries.append(
                        model_class.id.in_(
                            stub.having(
                                func.sum(Occasion.available_spots) >= 4
                            )
                        )
                    )
                else:
                    raise NotImplementedError

            query = query.filter(or_(*queries))

        return query

    def for_filter(self,
                   tag=None,
                   state=None,
                   duration=None,
                   age_range=None,
                   owner=None,
                   period_id=None,
                   daterange=None,
                   weekday=None,
                   municipality=None,
                   available=None):
        """ Returns a new collection instance.

        The given tag is excluded if already in the list, included if not
        yet in the list. Same goes for the given state.

        Note that dateranges are excluded only if they match exactly. That is
        we don't care about overlaps at all. If the same exact daterange is
        found in the filter, it is excluded.

        """

        duration = int(duration) if duration is not None else None

        toggled = (
            toggle(collection, item) for collection, item in (
                (self.tags, tag),
                (self.states, state),
                (self.durations, duration),
                (self.age_ranges, age_range),
                (self.owners, owner),
                (self.period_ids, period_id),
                (self.dateranges, daterange),
                (self.weekdays, weekday),
                (self.municipalities, municipality),
                (self.available, available)
            )
        )

        return self.__class__(self.session, self.type, 0, *toggled)

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
