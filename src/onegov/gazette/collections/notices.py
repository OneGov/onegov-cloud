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
from operator import itemgetter
from sqlalchemy import desc
from sqlalchemy import func
from sqlalchemy import or_
from sqlalchemy import String
from uuid import uuid4


from typing import Any
from typing import Literal
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable
    from collections.abc import Collection
    from collections.abc import Iterable
    from collections.abc import Sized
    from onegov.gazette.request import GazetteRequest
    from onegov.notice.models import NoticeState
    from datetime import date
    from sqlalchemy.orm import Query
    from sqlalchemy.orm import Session
    from sqlalchemy.sql import ColumnElement
    from typing import TypeVar
    from typing_extensions import Self
    from uuid import UUID

    _T = TypeVar('_T')
    _StrColumnLike = ColumnElement[str] | ColumnElement[str | None]


TRANSLATIONS: dict[str | None, str] = {
    'drafted': _("drafted"),
    'submitted': _("submitted"),
    'rejected': _("rejected"),
    'accepted': _("accepted"),
    'published': _("published"),
    'imported': _("imported"),
}


class GazetteNoticeCollection(OfficialNoticeCollection[GazetteNotice]):
    """ Manage a list of gazette specific official notices. """

    batch_size = 20

    @property
    def model_class(self) -> type[GazetteNotice]:
        return GazetteNotice

    def __init__(
        self,
        session: 'Session',
        page: int = 0,
        state: 'NoticeState | None' = None,
        term: str | None = None,
        order: str | None = None,
        direction: Literal['asc', 'desc'] | None = None,
        issues: 'Collection[str] | None ' = None,
        categories: 'Collection[str] | None ' = None,
        organizations: 'Collection[str] | None ' = None,
        user_ids: list['UUID'] | None = None,
        group_ids: list['UUID'] | None = None,
        from_date: 'date | None' = None,
        to_date: 'date | None' = None,
        source: 'UUID | None' = None,
        own: bool | None = None
    ) -> None:

        # get the issues from the date filters
        if issues is None and (from_date or to_date):
            query = session.query(Issue.name)
            if from_date:
                query = query.filter(Issue.date >= from_date)
            if to_date:
                query = query.filter(Issue.date <= to_date)
            issues = [issue for issue, in query]

        super().__init__(
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
        self.own_user_id: str | None = None

    def on_request(self, request: 'GazetteRequest') -> None:
        if self.own and request.identity and request.identity.userid:
            id_ = self.session.query(User.id)
            row = id_.filter_by(username=request.identity.userid).first()
            self.own_user_id = str(row[0]) if row else None

    def page_by_index(self, index: int) -> 'Self':
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

    def for_state(self, state: 'NoticeState') -> 'Self':
        """ Returns a new instance of the collection with the given state. """

        result = super().for_state(state)
        result.from_date = self.from_date
        result.to_date = self.to_date
        result.source = self.source
        result.own = self.own
        return result

    def for_term(self, term: str | None) -> 'Self':
        """ Returns a new instance of the collection with the given term. """

        result = super().for_term(term)
        result.from_date = self.from_date
        result.to_date = self.to_date
        result.source = self.source
        result.own = self.own
        return result

    def for_order(
        self,
        order: str,
        direction: Literal['asc', 'desc'] | None = None
    ) -> 'Self':
        """ Returns a new instance of the collection with the given ordering.
        Inverts the direction if the new ordering is the same as the old one
        and an explicit ordering is not defined.

        """

        result = super().for_order(order, direction)
        result.from_date = self.from_date
        result.to_date = self.to_date
        result.source = self.source
        result.own = self.own
        return result

    def for_organizations(
        self,
        organizations: 'Collection[str] | None'
    ) -> 'Self':
        """ Returns a new instance of the collection with the given
        organizations.

        """

        result = super().for_organizations(organizations)
        result.from_date = self.from_date
        result.to_date = self.to_date
        result.source = self.source
        result.own = self.own
        return result

    def for_categories(self, categories: 'Collection[str] | None') -> 'Self':
        """ Returns a new instance of the collection with the given categories.

        """

        result = super().for_categories(categories)
        result.from_date = self.from_date
        result.to_date = self.to_date
        result.source = self.source
        result.own = self.own
        return result

    def for_dates(
        self,
        from_date: 'date | None',
        to_date: 'date | None'
    ) -> 'Self':
        """ Returns a new instance of the collection with the given dates. """

        return self.__class__(
            self.session,
            state=self.state,
            term=self.term,
            order=self.order,
            direction=self.direction,
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
    def term_columns(self) -> list['_StrColumnLike']:
        """ The columns used for full text search. """

        return super().term_columns + [
            self.model_class.meta['group_name'].astext,
            self.model_class.meta['user_name'].astext,
        ]

    def filter_query(
        self,
        query: 'Query[GazetteNotice]'
    ) -> 'Query[GazetteNotice]':
        """ Allows additionally to filter for notices with changes made by a
        given user.

        """

        if self.own_user_id:
            subquery = super().filter_query(query)
            subquery = subquery.with_entities(GazetteNotice.id.distinct())
            subquery = subquery.join(self.model_class.changes, isouter=True)
            subquery = subquery.filter(
                GazetteNoticeChange.owner == self.own_user_id
            )
            return query.filter(GazetteNotice.id.in_(subquery.subquery()))

        return super().filter_query(query)

    def add(  # type: ignore[override]
        self,
        title: str,
        text: str | None,
        organization_id: str | None,
        category_id: str | None,
        user: User,
        issues: 'dict[str, str | None] | Iterable[str]',
        **kwargs: Any
    ) -> GazetteNotice:
        """ Add a new notice.

        A unique, URL-friendly name is created automatically for this notice
        using the title and optionally numbers for duplicate names.

        A entry is added automatically to the audit trail.

        Returns the created notice.
        """

        notice = GazetteNotice(  # type:ignore[misc]
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

        audit_trail: MessageCollection[GazetteNoticeChange]
        audit_trail = MessageCollection(self.session, type='gazette_notice')
        audit_trail.add(
            channel_id=str(notice.id),
            owner=str(user.id) if user else '',
            meta={'event': _("created")}
        )

        return notice

    def count_by_organization(self) -> list[tuple[str, int]]:
        """ Returns the total number of notices by organizations.

        Returns a tuple ``(organization name, number of notices)``
        for each organization. Filters by the state of the collection.

        """
        issue_keys = GazetteNotice._issues.keys()  # type:ignore[attr-defined]
        result: Query[tuple[str, list[str]]] = self.session.query(
            GazetteNotice.organization,
            issue_keys
        )
        result = result.filter(
            GazetteNotice.organization.isnot(None),
            func.array_length(issue_keys, 1) != 0
        )
        if self.state:
            result = result.filter(GazetteNotice.state == self.state)
        if self.issues:
            result = result.filter(
                GazetteNotice._issues.has_any(self.issues)  # type:ignore
            )
        result = result.order_by(GazetteNotice.organization)

        issues = set(self.issues or ())
        operation: Callable[[list[str]], Sized]
        if issues:
            operation = issues.intersection
        else:
            # while issues.union also works it doesn't convey the
            # intent very well, that we just count the original
            # issues without filtering them
            def operation(x: list[str]) -> 'Sized':
                return x
        return [
            (
                group[0],
                sum(len(operation(x[1])) for x in group[1])
            )
            for group in groupbylist(result, itemgetter(0))
        ]

    def count_by_category(self) -> list[tuple[str, int]]:
        """ Returns the total number of notices by categories.

        Returns a tuple ``(category name, number of notices)``
        for each category. Filters by the state of the collection.

        """
        issue_keys = GazetteNotice._issues.keys()  # type:ignore[attr-defined]
        result = self.session.query(
            GazetteNotice.category,
            issue_keys
        )
        result = result.filter(
            GazetteNotice.category.isnot(None),
            func.array_length(issue_keys, 1) != 0
        )
        if self.state:
            result = result.filter(GazetteNotice.state == self.state)
        if self.issues:
            result = result.filter(
                GazetteNotice._issues.has_any(self.issues)  # type:ignore
            )
        result = result.order_by(GazetteNotice.category)

        issues = set(self.issues or ())
        operation: Callable[[list[str]], Sized]
        if issues:
            operation = issues.intersection
        else:
            # while issues.union also works it doesn't convey the
            # intent very well, that we just count the original
            # issues without filtering them
            def operation(x: list[str]) -> 'Sized':
                return x
        return [
            (
                group[0],
                sum(len(operation(x[1])) for x in group[1])
            )
            for group in groupbylist(result, itemgetter(0))
        ]

    def count_by_group(self) -> list[tuple[str, int]]:
        """ Returns the total number of notices by groups.

        Returns a tuple ``(group name, number of notices)``
        for each group. Filters by the state of the collection.

        """
        issue_keys = GazetteNotice._issues.keys()  # type:ignore[attr-defined]
        result = self.session.query(
            UserGroup.name,
            issue_keys
        )
        result = result.filter(
            GazetteNotice.group_id == UserGroup.id,
            func.array_length(issue_keys, 1) != 0
        )
        if self.state:
            result = result.filter(GazetteNotice.state == self.state)
        if self.issues:
            result = result.filter(
                GazetteNotice._issues.has_any(self.issues)  # type:ignore
            )
        result = result.order_by(UserGroup.name)

        issues = set(self.issues or ())
        operation: Callable[[list[str]], Sized]
        if issues:
            operation = issues.intersection
        else:
            # while issues.union also works it doesn't convey the
            # intent very well, that we just count the original
            # issues without filtering them
            def operation(x: list[str]) -> 'Sized':
                return x
        return [
            (
                group[0],
                sum(len(operation(x[1])) for x in group[1])
            )
            for group in groupbylist(result, itemgetter(0))
        ]

    def count_rejected(self) -> list[tuple[str, int]]:
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

        result: dict[str, int] = {}
        for id_, changes in groupby(query, itemgetter(0)):
            marker = False
            for notice, state, user_id, user_name in changes:
                if state == 'submitted':
                    name = users.get(user_id) or user_name
                    if marker and name:
                        result.setdefault(name, 0)
                        result[name] = result[name] + 1
                marker = state == 'rejected'
        return sorted(result.items(), key=itemgetter(1), reverse=True)

    @property
    def used_issues(self) -> tuple[Issue, ...]:
        """ Returns all issues currently in use. """

        session = self.session

        used_query = session.query(
            GazetteNotice._issues.keys().label('list')  # type:ignore
        )
        used = list({value for item in used_query for value in item.list})

        result = session.query(Issue)
        result = result.filter(Issue.name.in_(used))
        result = result.order_by(desc(Issue.date))
        return tuple(result)

    @property
    def used_organizations(self) -> tuple[Organization, ...]:
        """ Returns all organizations currently in use. """

        session = self.session

        used_query = session.query(
            GazetteNotice._organizations.keys().label('list')  # type:ignore
        )
        used = list({value for item in used_query for value in item.list})

        result = session.query(Organization)
        result = result.filter(Organization.name.in_(used))
        result = result.order_by(Organization.title)
        return tuple(result)

    @property
    def used_categories(self) -> tuple[Category, ...]:
        """ Returns all categories currently in use. """

        session = self.session

        used_query = session.query(
            GazetteNotice._categories.keys().label('list')  # type:ignore
        )
        used = list({value for item in used_query for value in item.list})

        result = session.query(Category)
        result = result.filter(Category.name.in_(used))
        result = result.order_by(Category.title)
        return tuple(result)
