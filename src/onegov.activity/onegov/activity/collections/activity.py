from onegov.activity.models import Activity
from onegov.core.utils import normalize_for_url, increment_name


class ActivityCollection(object):

    def __init__(self, session):
        self.session = session

    def query(self):
        return self.session.query(Activity)

    def get_unique_name(self, name):
        name = normalize_for_url(name)

        existing = Activity.name.like('{}%'.format(name))
        existing = self.query().filter(existing)
        existing = existing.with_entities(Activity.name)
        existing = set(r.scalar() for r in existing.all())

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
            user=user.id,
            lead=lead,
            text=text
        )

        self.session.add(activity)
        self.session.flush()

        return activity

    def delete(self, activity):
        self.session.delete(activity)
        self.sesison.flush()
