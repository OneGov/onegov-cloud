from onegov.activity.models import Activity
from onegov.core.collection import Pagination
from onegov.core.utils import normalize_for_url, increment_name
from sqlalchemy import desc


class ActivityCollection(Pagination):

    def __init__(self, session, type='*', page=0):
        self.session = session
        self.type = type
        self.page = page

    def __eq__(self, other):
        self.type == type and self.page == other.page

    def subset(self):
        query = self.query()
        query = query.order_by(desc(Activity.title))

        return query

    @property
    def page_index(self):
        return self.page

    def page_by_index(self, index):
        return self.__class__(self.session, self.type, index)

    def query(self):
        if self.type != '*':
            model_class = Activity.get_polymorphic_class(self.type, Activity)
            query = self.session.query(model_class)
            return query.filter(model_class.type == self.type)

        return self.session.query(Activity)

    def by_id(self, id):
        return self.query().filter(Activity.id == id).first()

    def by_name(self, name):
        return self.query().filter(Activity.name == name).first()

    def by_user(self, user):
        return self.query().filter(Activity.username == user.username)

    def by_username(self, username):
        return self.query().filter(Activity.username == username)

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
        activity_class = Activity.get_polymorphic_class(type, Activity)

        activity = activity_class(
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
        self.sesison.flush()
