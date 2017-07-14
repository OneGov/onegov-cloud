from onegov.chat import MessageCollection
from onegov.gazette import _
from onegov.gazette.models import GazetteNotice
from onegov.gazette.models import UserGroup
from onegov.notice import OfficialNoticeCollection
from onegov.user import User
from sqlalchemy import func
from sqlalchemy import String
from uuid import uuid4


TRANSLATIONS = {
    'drafted': _("drafted"),
    'submitted': _("submitted"),
    'rejected': _("rejected"),
    'published': _("published"),
}


class GazetteNoticeCollection(OfficialNoticeCollection):
    """ Manage a list of gazette specific official notices. """

    def query(self):
        query = self.session.query(GazetteNotice)
        if self.state:
            query = query.filter(GazetteNotice.state == self.state)
        return query

    def add(self, title, text, category, issues, user_id):
        """ Add a new notice.

        A unique, URL-friendly name is created automatically for this notice
        using the title and optionally numbers for duplicate names.

        A entry is added automatically to the audit trail.

        Returns the created notice.
        """

        notice = GazetteNotice(
            id=uuid4(),
            state='drafted',
            title=title,
            name=self._get_unique_name(title),
            category=category,
            user_id=user_id
        )
        notice.text = text
        notice.issues = issues
        self.session.add(notice)
        self.session.flush()

        audit_trail = MessageCollection(self.session, type='gazette_notice')
        audit_trail.add(
            channel_id=str(notice.id),
            owner=str(user_id),
            text=_("created")
        )

        return notice

    def count_by_category(self, principal):
        """ Returns the total number of notices by categories.

        Returns a tuple ``(category number, category name, number of notices)``
        for each category defined in the principal. Filters by the state of
        the collection.

        """

        result = self.session.query(
            GazetteNotice.category,
            func.count(GazetteNotice.category)
        )
        result = result.group_by(GazetteNotice.category)
        if self.state:
            result = result.filter(GazetteNotice.state == self.state)
        result = dict(result)
        return sorted([
            (key, ' / '.join(value), result.get(key, 0))
            for key, value in principal.categories_flat.items()
        ])

    def count_by_user(self):
        """ Returns the total number of notices by users.

        Returns a tuple ``(user ID, number of notices)``
        for each user with a notice. Filters by the state of the collection.

        """

        result = self.session.query(
            func.cast(GazetteNotice.user_id, String),
            func.count(GazetteNotice.user_id)
        )
        if self.state:
            result = result.filter(GazetteNotice.state == self.state)
        result = result.group_by(GazetteNotice.user_id)
        return result.all()

    def count_by_group(self):
        """ Returns the total number of notices by groups.

        Returns a tuple ``(Group name, name, number of notices)`` for each
        group defined. Filters by the state of the collection.

        """
        users = self.session.query(func.cast(User.id, String), User.data)
        users = {user[0]: (user[1] or {}).get('group', None) for user in users}

        result = {
            group[0]: [group[1], 0]
            for group in self.session.query(
                func.cast(UserGroup.id, String),
                UserGroup.name
            )
        }
        result[''] = ['', 0]
        for user, value in self.count_by_user():
            key = users.get(user, '') or ''
            if key not in result:
                key = ''
            result[key][1] += value
        if not result[''][1]:
            del result['']

        return sorted(result.values())
