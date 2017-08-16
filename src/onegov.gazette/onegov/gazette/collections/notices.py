from onegov.chat import MessageCollection
from onegov.core.utils import groupbylist
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
    'accepted': _("accepted"),
    'published': _("published"),
}


class GazetteNoticeCollection(OfficialNoticeCollection):
    """ Manage a list of gazette specific official notices. """

    @property
    def model_class(self):
        return GazetteNotice

    def __init__(
        self,
        session,
        page=0,
        state=None,
        term=None,
        order=None,
        direction=None,
        issues=None,
        from_date=None,
        to_date=None,
        source=None
    ):
        super(GazetteNoticeCollection, self).__init__(
            session=session,
            page=page,
            state=state,
            term=term,
            order=order,
            direction=direction,
            issues=issues
        )
        self.from_date = from_date
        self.to_date = to_date
        self.source = source

    def add(self, title, text, organization_id, category_id, user_id, issues,
            principal):
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
            text=text,
            name=self._get_unique_name(title),
            user_id=user_id,
            issues=issues
        )
        notice.organization_id = organization_id
        notice.category_id = category_id
        notice.apply_meta(principal)
        self.session.add(notice)
        self.session.flush()

        audit_trail = MessageCollection(self.session, type='gazette_notice')
        audit_trail.add(
            channel_id=str(notice.id),
            owner=str(user_id),
            meta={'event': _("created")}
        )

        return notice

    def on_request(self, request):
        """ Limits the issues to the date filters. """
        self.issues = None
        if self.from_date or self.to_date:
            issues = request.app.principal.issues_by_date
            self.issues = [
                str(issue) for date_, issue in issues.items()
                if (
                    ((not self.from_date) or (date_ >= self.from_date)) and
                    ((not self.to_date) or (date_ <= self.to_date))
                )
            ]

    def count_by_organization(self):
        """ Returns the total number of notices by organizations.

        Returns a tuple ``(organization name, number of notices)``
        for each organization. Filters by the state of the collection.

        """
        result = self.session.query(
            GazetteNotice.organization,
            GazetteNotice._issues.keys()
        )
        result = result.filter(
            GazetteNotice.organization.isnot(None),
            func.array_length(GazetteNotice._issues.keys(), 1) != 0
        )
        if self.state:
            result = result.filter(GazetteNotice.state == self.state)
        if self.issues:
            result = result.filter(GazetteNotice._issues.has_any(self.issues))
        result = result.order_by(GazetteNotice.organization)

        issues = set(self.issues or [])
        operation = issues.intersection if issues else issues.union
        return [
            (
                group[0],
                sum([len(operation(set(x[1]))) for x in group[1]])
            )
            for group in groupbylist(result, lambda a: a[0])
        ]

    def count_by_category(self):
        """ Returns the total number of notices by categories.

        Returns a tuple ``(category name, number of notices)``
        for each category. Filters by the state of the collection.

        """
        result = self.session.query(
            GazetteNotice.category,
            GazetteNotice._issues.keys()
        )
        result = result.filter(
            GazetteNotice.category.isnot(None),
            func.array_length(GazetteNotice._issues.keys(), 1) != 0
        )
        if self.state:
            result = result.filter(GazetteNotice.state == self.state)
        if self.issues:
            result = result.filter(GazetteNotice._issues.has_any(self.issues))
        result = result.order_by(GazetteNotice.category)

        issues = set(self.issues or [])
        operation = issues.intersection if issues else issues.union
        return [
            (
                group[0],
                sum([len(operation(set(x[1]))) for x in group[1]])
            )
            for group in groupbylist(result, lambda a: a[0])
        ]

    def count_by_user(self):
        """ Returns the total number of notices by users.

        Returns a tuple ``(user ID, number of notices)``
        for each user with a notice. Filters by the state of the collection.

        """
        result = self.session.query(
            func.cast(GazetteNotice.user_id, String),
            GazetteNotice._issues.keys()
        )
        result = result.filter(
            GazetteNotice.user_id.isnot(None),
            func.array_length(GazetteNotice._issues.keys(), 1) != 0
        )
        if self.state:
            result = result.filter(GazetteNotice.state == self.state)
        if self.issues:
            result = result.filter(GazetteNotice._issues.has_any(self.issues))
        result = result.order_by(GazetteNotice.user_id)

        issues = set(self.issues or [])
        operation = issues.intersection if issues else issues.union
        return [
            (
                group[0],
                sum([len(operation(set(x[1]))) for x in group[1]])
            )
            for group in groupbylist(result, lambda a: a[0])
        ]

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
