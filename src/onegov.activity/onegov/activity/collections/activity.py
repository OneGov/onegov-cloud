from onegov.activity.models import Activity
from onegov.activity.utils import merge_ranges, overlaps
from onegov.core.collection import Pagination
from onegov.core.utils import increment_name
from onegov.core.utils import normalize_for_url
from sqlalchemy import distinct, or_, func, text, bindparam, Integer
from sqlalchemy.dialects.postgresql import array


class ActivityCollection(Pagination):

    def __init__(self, session, type='*', page=0,
                 tags=None, states=None, durations=None, age_ranges=None):
        self.session = session
        self.type = type
        self.page = page
        self.tags = set(tags) if tags else set()
        self.states = set(states) if states else set()
        self.durations = set(durations) if durations else set()
        self.age_ranges = set(merge_ranges(age_ranges)) \
            if age_ranges else set()

    def __eq__(self, other):
        self.type == type and self.page == other.page

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
            age_ranges=self.age_ranges
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
            conditions = tuple(
                text("'[:min,:max]'::int4range && ANY(ages)").bindparams(
                    bindparam('min', min_age, type_=Integer),
                    bindparam('max', max_age, type_=Integer),
                ) for min_age, max_age in self.age_ranges
            )
            query = query.filter(or_(*conditions))

        return query

    def for_filter(self, tag=None, state=None, duration=None, age_range=None):
        """ Returns a new collection instance.

        The given tag is excluded if already in the list, included if not
        yet in the list. Same goes for the given state.

        """

        assert tag or state or duration or age_range

        duration = int(duration) if duration is not None else None

        def toggle(collection, item):
            if item is None:
                return collection

            if item in collection:
                return collection - {item}
            else:
                return collection | {item}

        toggled = (
            toggle(collection, item) for collection, item in (
                (self.tags, tag),
                (self.states, state),
                (self.durations, duration),
                (self.age_ranges, age_range)
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

        query = self.query_base().with_entities(
            distinct(self.model_class._tags.keys()))

        return {key for row in query.all() if row[0] for key in row[0]}

    def get_unique_name(self, name):
        """ Given a desired name, finds a variant of that name that's not
        yet used. So if 'foobar' is already used, 'foobar-1' will be returned.

        """
        name = normalize_for_url(name)

        existing = Activity.name.like('{}%'.format(name))
        existing = self.query().filter(existing)
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
        self.session.delete(activity)
        self.session.flush()
