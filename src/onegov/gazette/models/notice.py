from __future__ import annotations

from collections import OrderedDict
from datetime import date
from onegov.chat import Message
from onegov.core.orm.mixins import content_property
from onegov.core.orm.mixins import dict_property
from onegov.core.orm.mixins import meta_property
from onegov.file import AssociatedFiles
from onegov.file import File
from onegov.gazette import _
from onegov.gazette.models.category import Category
from onegov.gazette.models.issue import Issue
from onegov.gazette.models.issue import IssueName
from onegov.gazette.models.organization import Organization
from onegov.gazette.observer import observes
from onegov.notice import OfficialNotice
from onegov.user import User
from onegov.user import UserCollection
from sedate import as_datetime
from sedate import standardize_date
from sedate import utcnow
from sqlalchemy.orm import backref
from sqlalchemy.orm import object_session
from sqlalchemy.orm import relationship


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterable
    from onegov.core.types import AppenderQuery
    from onegov.gazette.request import GazetteRequest
    from onegov.user import UserGroup
    from sqlalchemy.orm import Session


class CachedUserNameMixin:
    """ Mixin providing a cached version of the user name.

    There needs to be:

    * a ``user`` relationship (which has no dynamic backref)
    * a meta column

    The observer needs to be registered in the children::

        @observes('user', 'user.realname', 'user.username')
        def user_observer(self, user, realname, username):
            if hasattr(self, '_user_observer'):
                self._user_observer(user, realname, username)

    """

    if TYPE_CHECKING:
        user: relationship[User | None] | relationship[User]

    #: The name of the user in case he gets deleted.
    _user_name: dict_property[str | None] = meta_property('user_name')

    @property
    def user_name(self) -> str | None:
        """ Returns the name of the owner.

        If the user has been deleted, the last known name in brackets is
        returned.
        """
        if self.user:
            return self.user.realname or self.user.username
        return '({})'.format(self._user_name) if self._user_name else None

    def _user_observer(
        self,
        user: User | None,
        realname: str | None,
        username: str | None
    ) -> None:
        """ Upates the last known name of the owner.

        This never deletes the stored name, set ``self._user_name`` yourself
        if you want to clear it.

        """
        user_name = user.realname or user.username if user else None
        user_name = user_name or realname or username or self._user_name
        self._user_name = user_name


class CachedGroupNameMixin:
    """ Mixin providing a cached version of the group name.

    There needs to be:

    * a ``group`` relationship (which has no dynamic backref)
    * a meta column

    The observer needs to be registered in the children::

        @observes('group', 'group.name')
        def group_observer(self, group, name):
            if hasattr(self, '_group_observerr'):
                self._group_observerr(user, realname, username)

    """

    if TYPE_CHECKING:
        group: relationship[UserGroup | None] | relationship[UserGroup]

    #: The name of the group in case the owner and its group get deleted.
    _group_name: dict_property[str | None] = meta_property('group_name')

    @property
    def group_name(self) -> str | None:
        """ Returns the name of the group this notice belongs to.

        If the group has been deleted, the last known name in brackets is
        returned.
        """

        if self.group:
            return self.group.name
        return '({})'.format(self._group_name) if self._group_name else None

    def _group_observer(
        self,
        group: UserGroup | None,
        name: str | None
    ) -> None:
        """ Upates the last known name of the group.

        This never deletes the stored name, set ``self._group_name`` yourself
        if you want to clear it.

        """

        group_name = group.name if group else None
        group_name = group_name or name or self._group_name
        self._group_name = group_name


class GazetteNoticeFile(File):
    __mapper_args__ = {'polymorphic_identity': 'gazette_notice'}

    if TYPE_CHECKING:
        # we manually add the backref AssociatedFiles creates
        linked_official_notices: relationship[list[GazetteNotice]]


class GazetteNotice(
    OfficialNotice, CachedUserNameMixin, CachedGroupNameMixin, AssociatedFiles
):
    """ An official notice with extras.

    We use a combination of the categories/organizations HSTORE and the
    individual category/organization columns. The ID of the category/
    organization is stored in the HSTORE column and the actual name ist copied
    when calling ``apply_meta``.

    We store only the issue names (year-number) in the HSTORE.

    It's possible to add a changelog entry by calling ``add_change``. Changelog
    entries are created for state changes by default.

    The user name accessible by ``user_name`` gets cached in case the user is
    deleted.

    The group name accessible by ``group_name`` gets cached in case the group
    is deleted.

    """

    __mapper_args__ = {'polymorphic_identity': 'gazette'}

    #: True, if the official notice only appears in the print version
    print_only: dict_property[bool | None] = meta_property('print_only')

    #: True, if the official notice needs to be paid for
    at_cost: dict_property[bool | None] = meta_property('at_cost')

    #: The billing address in case the official notice need to be paid for
    billing_address: dict_property[str | None]
    billing_address = content_property('billing_address')

    changes: relationship[AppenderQuery[GazetteNoticeChange]] = relationship(
        'GazetteNoticeChange',
        back_populates='notice',
        primaryjoin=(
            'foreign(GazetteNoticeChange.channel_id)'
            '== cast(GazetteNotice.id, TEXT)'
        ),
        lazy='dynamic',
        cascade='all,delete-orphan',
        order_by='desc(GazetteNoticeChange.id)'
    )

    @observes('user', 'user.realname', 'user.username')
    def user_observer(
        self,
        user: User | None,
        realname: str | None,
        username: str | None
    ) -> None:
        self._user_observer(user, realname, username)

    @observes('group', 'group.name')
    def group_observer(
        self,
        group: UserGroup | None,
        name: str | None
    ) -> None:
        self._group_observer(group, name)

    def add_change(
        self,
        request: GazetteRequest,
        event: str,
        text: str | None = None
    ) -> None:
        """ Adds en entry to the changelog. """

        session = object_session(self)
        identity = request.identity
        username = identity.userid if identity else None
        if username:
            user = UserCollection(session).by_username(username)
            owner = str(user.id) if user else None
        else:
            owner = None

        self.changes.append(
            GazetteNoticeChange(
                channel_id=str(self.id),
                owner=owner,
                text=text or '',
                meta={'event': event}
            )
        )

    def submit(self, request: GazetteRequest) -> None:  # type:ignore
        """ Submit a drafted notice.

        This automatically adds en entry to the changelog.

        """

        super().submit()
        self.add_change(request, _('submitted'))

    def reject(  # type:ignore[override]
        self,
        request: GazetteRequest,
        comment: str
    ) -> None:
        """ Reject a submitted notice.

        This automatically adds en entry to the changelog.

        """

        super().reject()
        self.add_change(request, _('rejected'), comment)

    def accept(self, request: GazetteRequest) -> None:  # type:ignore
        """ Accept a submitted notice.

        This automatically adds en entry to the changelog.

        """

        super().accept()
        self.add_change(request, _('accepted'))

    def publish(self, request: GazetteRequest) -> None:  # type:ignore
        """ Publish an accepted notice.

        This automatically adds en entry to the changelog.

        """

        super().publish()
        self.add_change(request, _('published'))

    @property
    def rejected_comment(self) -> str:
        """ Returns the comment of the last rejected change log entry. """

        for change in self.changes:
            if change.event == 'rejected':
                return change.text or ''

        return ''

    @property
    def issues(self) -> dict[str, str | None]:
        """ Returns the issues sorted (by year/number). """

        issues = self._issues or {}
        keys = sorted(
            IssueName.from_string(issue)
            for issue in (self._issues or {})
        )
        return OrderedDict((str(key), issues[str(key)]) for key in keys)

    # FIXME: asymmetric properties don't work
    @issues.setter
    def issues(self, value: dict[str, str | None] | Iterable[str]) -> None:
        if isinstance(value, dict):
            self._issues = value
        else:
            self._issues = dict.fromkeys(value, None)

    @property
    def issue_objects(self) -> list[Issue]:
        if self._issues:
            query = object_session(self).query(Issue)
            query = query.filter(Issue.name.in_(self._issues.keys()))
            query = query.order_by(Issue.date)
            return query.all()
        return []

    def set_publication_number(self, issue: str, number: int) -> None:
        assert issue in self.issues
        issues = dict(self.issues)
        issues[issue] = str(number)
        self._issues = issues

    @property
    def category_id(self) -> str | None:
        """ The ID of the category. We store this the ID in the HSTORE (we use
        only one!) and additionaly store the title of the category in the
        category column.

        """
        return next(iter(self.categories.keys()), None)

    @category_id.setter
    def category_id(self, value: str | None) -> None:
        self.categories = {} if value is None else {value: None}

    @property
    def category_object(self) -> Category | None:
        if self.category_id:
            query = object_session(self).query(Category)
            query = query.filter(Category.name == self.category_id)
            return query.first()
        return None

    @property
    def organization_id(self) -> str | None:
        """ The ID of the organization. We store this the ID in the HSTORE (we
        use only one!) and additionaly store the title of the organization in
        the organization column.

        """
        return next(iter(self.organizations.keys()), None)

    @organization_id.setter
    def organization_id(self, value: str | None) -> None:
        self.organizations = {} if value is None else {value: None}

    @property
    def organization_object(self) -> Organization | None:
        if self.organization_id:
            query = object_session(self).query(Organization)
            query = query.filter(Organization.name == self.organization_id)
            return query.first()
        return None

    @property
    def overdue_issues(self) -> bool:
        """ Returns True, if any of the issue's deadline is reached. """

        if self._issues:
            session = object_session(self)
            query = session.query(Issue)
            query = query.filter(Issue.name.in_(self._issues.keys()))
            query = query.filter(Issue.deadline < utcnow())
            return session.query(query.exists()).scalar()

        return False

    @property
    def expired_issues(self) -> bool:
        """ Returns True, if any of the issue's issue date is reached. """
        if self._issues:
            session = object_session(self)
            query = session.query(Issue)
            query = query.filter(Issue.name.in_(self._issues.keys()))
            query = query.filter(Issue.date <= date.today())
            return session.query(query.exists()).scalar()

        return False

    @property
    def invalid_category(self) -> bool:
        """ Returns True, if the category is invalid or inactive. """
        query = object_session(self).query(Category.active)
        row = query.filter(Category.name == self.category_id).first()
        return (not row[0]) if row else True

    @property
    def invalid_organization(self) -> bool:
        """ Returns True, if the organization is invalid or inactive. """
        query = object_session(self).query(Organization.active)
        row = query.filter(Organization.name == self.organization_id).first()
        return (not row[0]) if row else True

    def apply_meta(self, session: Session) -> None:
        """ Updates the category, organization and issue date from the meta
        values.

        """
        self.organization = None
        query = session.query(Organization.title)
        row = query.filter(Organization.name == self.organization_id).first()
        if row:
            self.organization = row[0]

        self.category = None
        query = session.query(Category.title)
        row = query.filter(Category.name == self.category_id).first()
        if row:
            self.category = row[0]

        self.first_issue = None
        if self._issues:
            date_query = session.query(Issue.date)
            date_query = date_query.filter(Issue.name.in_(self._issues.keys()))
            date_row = date_query.order_by(Issue.date).first()
            if date_row:
                self.first_issue = standardize_date(
                    as_datetime(date_row[0]), 'UTC'
                )


class GazetteNoticeChange(Message, CachedUserNameMixin):
    """ A changelog entry for an official notice. """

    __mapper_args__ = {'polymorphic_identity': 'gazette_notice'}

    #: the user which made this change
    user: relationship[User | None] = relationship(
        User,
        primaryjoin=(
            'foreign(GazetteNoticeChange.owner) == cast(User.id, TEXT)'
        ),
        backref=backref('changes', lazy='select')
    )

    @observes('user', 'user.realname', 'user.username')
    def user_observer(
        self,
        user: User | None,
        realname: str | None,
        username: str | None
    ) -> None:
        self._user_observer(user, realname, username)

    #: the notice which this change belongs to
    notice: relationship[GazetteNotice] = relationship(
        GazetteNotice,
        primaryjoin=(
            'foreign(GazetteNoticeChange.channel_id)'
            '== cast(GazetteNotice.id, TEXT)'
        ),
        back_populates='changes'
    )

    #: the event
    event: dict_property[str | None] = meta_property('event')
