from itertools import groupby
from onegov.chat import MessageCollection
from onegov.core.utils import groupbylist
from onegov.gazette import _
from onegov.gazette.models import Category
from onegov.gazette.models import GazetteNotice
from onegov.gazette.models import Issue
from onegov.gazette.models import Organization
from onegov.gazette.models.notice import GazetteNoticeChange
from onegov.notice import OfficialNoticeCollection
from onegov.user import User
from onegov.user import UserGroup
from sqlalchemy import func
from sqlalchemy import or_
from sqlalchemy import String
from uuid import uuid4


TRANSLATIONS = {
    'drafted': _("drafted"),
    'submitted': _("submitted"),
    'rejected': _("rejected"),
    'accepted': _("accepted"),
    'published': _("published"),
    'imported': _("imported"),
}


class GazetteNoticeCollection(OfficialNoticeCollection):
    """ Manage a list of gazette specific official notices. """

    batch_size = 20

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
        categories=None,
        organizations=None,
        user_ids=None,
        group_ids=None,
        from_date=None,
        to_date=None,
        source=None,
        own=None
    ):
        # get the issues from the date filters
        issues = None
        if from_date or to_date:
            query = session.query(Issue.name)
            if from_date:
                query = query.filter(Issue.date >= from_date)
            if to_date:
                query = query.filter(Issue.date <= to_date)
            issues = [issue[0] for issue in query]

        super(GazetteNoticeCollection, self).__init__(
            session=session,
            page=page,
            state=state,
            term=term,
            order=order,
            direction=direction,
            issues=issues,
            categories=categories,
            organizations=organizations,
            user_ids=user_ids,
            group_ids=group_ids
        )
        self.from_date = from_date
        self.to_date = to_date
        self.source = source
        self.own = own
        self.own_user_id = None

    def on_request(self, request):
        if self.own and request.identity and request.identity.userid:
            id_ = self.session.query(User.id)
            id_ = id_.filter_by(username=request.identity.userid).first()
            self.own_user_id = str(id_[0]) if id_ else None

    def page_by_index(self, index):
        return self.__class__(
            self.session,
            page=index,
            state=self.state,
            term=self.term,
            order=self.order,
            direction=self.direction,
            issues=self.issues,
            categories=self.categories,
            organizations=self.organizations,
            user_ids=self.user_ids,
            group_ids=self.group_ids,
            from_date=self.from_date,
            to_date=self.to_date,
            source=self.source,
            own=self.own
        )

    def for_state(self, state):
        """ Returns a new instance of the collection with the given state. """

        result = super(GazetteNoticeCollection, self).for_state(state)
        result.from_date = self.from_date
        result.to_date = self.to_date
        result.source = self.source
        result.own = self.own
        return result

    def for_term(self, term):
        """ Returns a new instance of the collection with the given term. """

        result = super(GazetteNoticeCollection, self).for_term(term)
        result.from_date = self.from_date
        result.to_date = self.to_date
        result.source = self.source
        result.own = self.own
        return result

    def for_order(self, order, direction=None):
        """ Returns a new instance of the collection with the given ordering.
        Inverts the direction if the new ordering is the same as the old one
        and an explicit ordering is not defined.

        """

        result = super(GazetteNoticeCollection, self).for_order(
            order, direction
        )
        result.from_date = self.from_date
        result.to_date = self.to_date
        result.source = self.source
        result.own = self.own
        return result

    def for_organizations(self, organizations):
        """ Returns a new instance of the collection with the given
        organizations.

        """

        result = super(GazetteNoticeCollection, self).for_organizations(
            organizations
        )
        result.from_date = self.from_date
        result.to_date = self.to_date
        result.source = self.source
        result.own = self.own
        return result

    def for_categories(self, categories):
        """ Returns a new instance of the collection with the given categories.

        """

        result = super(GazetteNoticeCollection, self).for_categories(
            categories
        )
        result.from_date = self.from_date
        result.to_date = self.to_date
        result.source = self.source
        result.own = self.own
        return result

    def for_dates(self, from_date, to_date):
        """ Returns a new instance of the collection with the given dates. """

        return self.__class__(
            self.session,
            state=self.state,
            term=self.term,
            order=self.order,
            direction=self.direction,
            issues=self.issues,
            categories=self.categories,
            organizations=self.organizations,
            user_ids=self.user_ids,
            group_ids=self.group_ids,
            from_date=from_date,
            to_date=to_date,
            source=self.source,
            own=self.own
        )

    @property
    def term_columns(self):
        """ The columns used for full text search. """

        return super(GazetteNoticeCollection, self).term_columns + [
            self.model_class.meta['group_name'].astext,
            self.model_class.meta['user_name'].astext,
        ]

    def filter_query(self, query):
        """ Allows additionally to filter for notices with changes made by a
        given user.

        """

        if self.own_user_id:
            subquery = super(GazetteNoticeCollection, self).filter_query(query)
            subquery = subquery.with_entities(GazetteNotice.id.distinct())
            subquery = subquery.join(self.model_class.changes, isouter=True)
            subquery = subquery.filter(
                GazetteNoticeChange.owner == self.own_user_id
            )
            subquery = subquery.subquery()
            return query.filter(GazetteNotice.id.in_(subquery))

        return super(GazetteNoticeCollection, self).filter_query(query)

    def add(self, title, text, organization_id, category_id, user, issues,
            **kwargs):
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
            issues=issues,
            **kwargs
        )
        notice.user = user
        notice.group = user.group if user else None
        notice.organization_id = organization_id
        notice.category_id = category_id
        notice.apply_meta(self.session)
        self.session.add(notice)
        self.session.flush()

        audit_trail = MessageCollection(self.session, type='gazette_notice')
        audit_trail.add(
            channel_id=str(notice.id),
            owner=str(user.id) if user else '',
            meta={'event': _("created")}
        )

        return notice

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

    def count_by_group(self):
        """ Returns the total number of notices by groups.

        Returns a tuple ``(group name, number of notices)``
        for each group. Filters by the state of the collection.

        """
        result = self.session.query(
            UserGroup.name,
            GazetteNotice._issues.keys()
        )
        result = result.filter(
            GazetteNotice.group_id == UserGroup.id,
            func.array_length(GazetteNotice._issues.keys(), 1) != 0
        )
        if self.state:
            result = result.filter(GazetteNotice.state == self.state)
        if self.issues:
            result = result.filter(GazetteNotice._issues.has_any(self.issues))
        result = result.order_by(UserGroup.name)

        issues = set(self.issues or [])
        operation = issues.intersection if issues else issues.union
        return [
            (
                group[0],
                sum([len(operation(set(x[1]))) for x in group[1]])
            )
            for group in groupbylist(result, lambda a: a[0])
        ]

    def count_rejected(self):
        """ Returns the number of rejected notices by user.

        Returns a tuple ``(user name, number of rejections)``
        for each user. Does not filter by the state of the collection.

        """

        query = self.session.query(
            GazetteNoticeChange.channel_id,
            GazetteNoticeChange.meta['event'],
            GazetteNoticeChange.owner,
            GazetteNoticeChange.meta['user_name']
        )
        query = query.filter(
            or_(
                GazetteNoticeChange.meta['event'] == 'rejected',
                GazetteNoticeChange.meta['event'] == 'submitted'
            )
        )
        query = query.order_by(
            GazetteNoticeChange.channel_id,
            GazetteNoticeChange.created.desc()
        )

        users = dict(
            self.session.query(func.cast(User.id, String), User.realname).all()
        )

        result = {}
        for id_, changes in groupby(query, lambda x: x[0]):
            marker = False
            for notice, state, user_id, user_name in changes:
                if state == 'submitted':
                    name = users.get(user_id) or user_name
                    if marker and name:
                        result.setdefault(name, 0)
                        result[name] = result[name] + 1
                marker = state == 'rejected'
        return sorted(list(result.items()), key=lambda x: x[1], reverse=True)

    @property
    def used_issues(self):
        """ Returns all issues currently in use. """

        session = self.session

        used = session.query(GazetteNotice._issues.keys().label('list'))
        used = list(set([value for item in used for value in item.list]))

        result = session.query(Issue)
        result = result.filter(Issue.name.in_(used))
        result = result.order_by(Issue.name)
        return result.all()

    @property
    def used_organizations(self):
        """ Returns all organizations currently in use. """

        session = self.session

        used = session.query(GazetteNotice._organizations.keys().label('list'))
        used = list(set([value for item in used for value in item.list]))

        result = session.query(Organization)
        result = result.filter(Organization.name.in_(used))
        result = result.order_by(Organization.title)
        return result.all()

    @property
    def used_categories(self):
        """ Returns all categories currently in use. """

        session = self.session

        used = session.query(GazetteNotice._categories.keys().label('list'))
        used = list(set([value for item in used for value in item.list]))

        result = session.query(Category)
        result = result.filter(Category.name.in_(used))
        result = result.order_by(Category.title)
        return result.all()
