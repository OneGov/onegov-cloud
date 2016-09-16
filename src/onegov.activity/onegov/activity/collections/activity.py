from onegov.activity.models import Activity
from onegov.core.utils import normalize_for_url, increment_name


class ActivityCollection(object):

    def __init__(self, session):
        self.session = session

    def query(self):
        return self.session.query(Activity)

    def by_id(self, id):
        return self.query().filter(Activity.id == id).first()

    def by_name(self, name):
        return self.query().filter(Activity.name == name).first()

    def by_user(self, user):
        return self.query().filter(Activity.user_id == user.id)

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

    def add(self, title, user, lead=None, text=None, tags=None,
            type=None, name=None):

        name = name or self.get_unique_name(title)
        activity_class = Activity.get_polymorphic_class(type, Activity)

        activity = activity_class(
            name=name,
            title=title,
            tags=tags,
            type=type,
            user_id=user.id,
            lead=lead,
            text=text
        )

        self.session.add(activity)
        self.session.flush()

        return activity

    def delete(self, activity):
        self.session.delete(activity)
        self.sesison.flush()
