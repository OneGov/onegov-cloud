from __future__ import annotations

from onegov.core.collection import Pagination
from onegov.core.utils import increment_name
from onegov.core.utils import normalize_for_url
from onegov.notice.models import OfficialNotice
from onegov.user import User
from onegov.user import UserGroup
from sqlalchemy import asc
from sqlalchemy import cast
from sqlalchemy import desc
from sqlalchemy import func
from sqlalchemy import inspect
from sqlalchemy import or_
from sqlalchemy import String
from sqlalchemy_utils.functions import escape_like


from typing import Any, Literal, TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Collection
    from markupsafe import Markup
    from onegov.notice.models import NoticeState
    from sqlalchemy.orm import Query, Session
    from sqlalchemy.sql import ColumnElement
    from typing import Self, TypeAlias
    from uuid import UUID

    _StrColumnLike: TypeAlias = (
        ColumnElement[str]
        | ColumnElement[str | None]
        | ColumnElement[Markup]
        | ColumnElement[Markup | None]
    )


_N = TypeVar('_N', bound=OfficialNotice)


def get_unique_notice_name(
    name: str,
    session: Session,
    model_class: type[OfficialNotice]
) -> str:
    """ Create a unique, URL-friendly name. """

    # it's possible for `normalize_for_url` to return an empty string...
    name = normalize_for_url(name) or 'notice'

    while session.query(
        session.query(model_class.name)
        .filter(model_class.name == name)
        .exists()
    ).scalar():
        name = increment_name(name)

    return name


class OfficialNoticeCollection(Pagination[_N]):
    """ Manage a list of official notices. """

    def __init__(
        self,
        session: Session,
        page: int = 0,
        state: NoticeState | None = None,
        term: str | None = None,
        order: str | None = None,
        direction: Literal['asc', 'desc'] | None = None,
        issues: Collection[str] | None = None,
        categories: Collection[str] | None = None,
        organizations: Collection[str] | None = None,
        user_ids: list[UUID] | None = None,
        group_ids: list[UUID] | None = None
    ):
        super().__init__(page)
        self.session = session
        self.state = state
        self.term = term
        self.order = order or 'first_issue'
        self.direction = direction or 'asc'
        self.issues = issues
        self.categories = categories
        self.organizations = organizations
        self.user_ids = user_ids or []
        self.group_ids = group_ids or []

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, OfficialNoticeCollection):
            return False

        return (
            self.model_class == other.model_class
            and self.page == other.page
            and self.state == other.state
            and self.term == other.term
            and self.order == other.order
            and self.direction == other.direction
            and self.issues == other.issues
            and self.categories == other.categories
            and self.organizations == other.organizations
            and self.user_ids == other.user_ids
            and self.group_ids == other.group_ids
        )

    def subset(self) -> Query[_N]:
        return self.query()

    @property
    def page_index(self) -> int:
        return self.page

    def page_by_index(self, index: int) -> Self:
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
            group_ids=self.group_ids
        )

    def for_state(self, state: NoticeState) -> Self:
        """ Returns a new instance of the collection with the given state. """

        return self.__class__(
            self.session,
            state=state,
            term=self.term,
            order=self.order,
            direction=self.direction,
            issues=self.issues,
            categories=self.categories,
            organizations=self.organizations,
            user_ids=self.user_ids,
            group_ids=self.group_ids
        )

    def for_term(self, term: str | None) -> Self:
        """ Returns a new instance of the collection with the given term. """

        return self.__class__(
            self.session,
            state=self.state,
            term=term,
            order=self.order,
            direction=self.direction,
            issues=self.issues,
            categories=self.categories,
            organizations=self.organizations,
            user_ids=self.user_ids,
            group_ids=self.group_ids
        )

    def for_order(
        self,
        order: str,
        direction: Literal['asc', 'desc'] | None = None
    ) -> Self:
        """ Returns a new instance of the collection with the given ordering.
        Inverts the direction if the new ordering is the same as the old one
        and an explicit ordering is not defined.

        """
        if direction is not None:
            descending = direction == 'desc'
        elif self.order != order:
            descending = False
        else:
            descending = self.direction != 'desc'

        return self.__class__(
            self.session,
            state=self.state,
            term=self.term,
            order=order,
            direction='desc' if descending else 'asc',
            issues=self.issues,
            categories=self.categories,
            organizations=self.organizations,
            user_ids=self.user_ids,
            group_ids=self.group_ids
        )

    def for_organizations(
        self,
        organizations: Collection[str] | None
    ) -> Self:
        """ Returns a new instance of the collection with the given
        organizations.

        """

        return self.__class__(
            self.session,
            state=self.state,
            term=self.term,
            order=self.order,
            direction=self.direction,
            issues=self.issues,
            categories=self.categories,
            organizations=organizations,
            user_ids=self.user_ids,
            group_ids=self.group_ids
        )

    def for_categories(self, categories: Collection[str] | None) -> Self:
        """ Returns a new instance of the collection with the given categories.

        """

        return self.__class__(
            self.session,
            state=self.state,
            term=self.term,
            order=self.order,
            direction=self.direction,
            issues=self.issues,
            categories=categories,
            organizations=self.organizations,
            user_ids=self.user_ids,
            group_ids=self.group_ids
        )

    @property
    def model_class(self) -> type[_N]:
        return OfficialNotice  # type:ignore[return-value]

    @property
    def term_columns(self) -> list[_StrColumnLike]:
        """ The columns used for full text search. """

        return [
            cast(self.model_class.id, String),
            self.model_class.title,
            self.model_class.text,
            self.model_class.author_name,
            self.model_class.author_place,
            self.model_class.category,
            self.model_class.organization,
            self.model_class.note,
            UserGroup.name,
            User.realname,
            User.username
        ]

    def filter_query(self, query: Query[_N]) -> Query[_N]:
        """ Filters the given query by the state of the collection. """

        if self.state:
            query = query.filter(self.model_class.state == self.state)
        if self.term:
            term = f'%{escape_like(self.term)}%'
            query = query.filter(or_(
                *(column.ilike(term) for column in self.term_columns)
            ))
        if self.user_ids:
            query = query.filter(self.model_class.user_id.in_(self.user_ids))
        if self.group_ids:
            query = query.filter(self.model_class.group_id.in_(self.group_ids))
        if self.issues:
            query = query.filter(
                # FIXME: SQLAlchemy 2.0 hopefully has better support for this
                self.model_class._issues.has_any(self.issues)  # type:ignore
            )
        if self.categories:
            query = query.filter(
                # FIXME: SQLAlchemy 2.0 hopefully has better support for this
                self.model_class._categories.has_any(  # type:ignore
                    self.categories
                )
            )
        if self.organizations:
            query = query.filter(
                # FIXME: SQLAlchemy 2.0 hopefully has better support for this
                self.model_class._organizations.has_any(  # type:ignore
                    self.organizations
                )
            )

        return query

    def order_query(self, query: Query[_N]) -> Query[_N]:
        """ Orders the given query by the state of the collection. """

        direction = desc if self.direction == 'desc' else asc
        if self.order in inspect(self.model_class).columns.keys():
            attribute = getattr(self.model_class, self.order)
        elif self.order == 'group.name':
            attribute = func.coalesce(UserGroup.name, '')
        elif self.order == 'user.realname':
            attribute = func.coalesce(User.realname, '')
        elif self.order == 'user.username':
            attribute = func.coalesce(User.username, '')
        elif self.order == 'user.name':
            attribute = func.coalesce(User.realname, User.username, '')
        else:
            attribute = self.model_class.first_issue

        return query.order_by(None).order_by(direction(attribute))

    def query(self) -> Query[_N]:
        """ Returns a filtered and sorted query.

        Filters by:
        - notice.state matches state
        - notice.user_id is in user_ids
        - notice.group_id is in group_ids
        - notice.issues has any of the issues
        - term is in title, text, category, organization, groupname, usernames

        Orders by:
        - any notice columns
        - group name (group.name)
        - users real name (user.realname)
        - username (user.username)
        - username or users real name (user.name)

        """

        query = self.session.query(self.model_class)
        query = query.join(self.model_class.group, isouter=True)
        query = query.join(self.model_class.user, isouter=True)
        query = self.filter_query(query)
        query = self.order_query(query)
        return query

    def _get_unique_name(self, name: str) -> str:
        """ Create a unique, URL-friendly name. """

        return get_unique_notice_name(name, self.session, self.model_class)

    def add(
        self,
        title: str,
        text: str | None,
        # FIXME: replace this with the actual allowed keywords
        **optional: Any
    ) -> _N:
        """ Add a new notice.

        A unique, URL-friendly name is created automatically for this notice
        using the title and optionally numbers for duplicate names.

        Returns the created notice.
        """
        issues = optional.pop('issues', None)
        categories = optional.pop('categories', None)
        organizations = optional.pop('organizations', None)
        notice = self.model_class(
            state='drafted',
            name=self._get_unique_name(title),
            title=title,
            text=text,
            **optional
        )
        if issues:
            notice.issues = issues
        if categories:
            notice.categories = categories
        if organizations:
            notice.organizations = organizations

        self.session.add(notice)
        self.session.flush()

        return notice

    def delete(self, notice: OfficialNotice) -> None:
        """ Delete an notice. """

        self.session.delete(notice)
        self.session.flush()

    def by_name(self, name: str) -> _N | None:
        """ Returns a notice by its URL-friendly name. """

        query = self.session.query(self.model_class)
        query = query.filter(self.model_class.name == name)
        return query.first()

    def by_id(self, id: UUID) -> _N | None:
        """ Returns a notice by its id. """

        query = self.session.query(self.model_class)
        query = query.filter(self.model_class.id == id)
        return query.first()
