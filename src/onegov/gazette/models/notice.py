from collections import OrderedDict
from datetime import date
from onegov.chat import Message
from onegov.core.orm.mixins import content_property
from onegov.core.orm.mixins import meta_property
from onegov.file import AssociatedFiles
from onegov.file import File
from onegov.gazette import _
from onegov.gazette.models.category import Category
from onegov.gazette.models.issue import Issue
from onegov.gazette.models.issue import IssueName
from onegov.gazette.models.organization import Organization
from onegov.notice import OfficialNotice
from onegov.user import User
from onegov.user import UserCollection
from sedate import as_datetime
from sedate import standardize_date
from sedate import utcnow
from sqlalchemy_utils import observes
from sqlalchemy.orm import backref
from sqlalchemy.orm import object_session
from sqlalchemy.orm import relationship


class CachedUserNameMixin(object):
    """ Mixin providing a cached version of the user name. There needs to be:
    - a ``user`` relationship (which has no dynamic backref)
    - a meta column

    The observer needs to be registered in the children:

    @observes('user', 'user.realname', 'user.username')
    def user_observer(self, user, realname, username):
        if hasattr(self, '_user_observer'):
            self._user_observer(user, realname, username)

    """

    #: The name of the user in case he gets deleted.
    _user_name = meta_property('user_name')

    @property
    def user_name(self):
        """ Returns the name of the owner.

        If the user has been deleted, the last known name in brackets is
        returned.
        """
        if self.user:
            return self.user.realname or self.user.username
        return '({})'.format(self._user_name) if self._user_name else None

    def _user_observer(self, user, realname, username):
        """ Upates the last known name of the owner.

        This never deletes the stored name, set ``self._user_name`` yourself
        if you want to clear it.

        """
        user_name = user.realname or user.username if user else None
        user_name = user_name or realname or username or self._user_name
        self._user_name = user_name


class CachedGroupNameMixin(object):
    """ Mixin providing a cached version of the group name. There needs to be:
    - a ``group`` relationship (which has no dynamic backref)
    - a meta column

    The observer needs to be registered in the children:

    @observes('group', 'group.name')
    def group_observer(self, group, name):
        if hasattr(self, '_group_observerr'):
            self._group_observerr(user, realname, username)

    """

    #: The name of the group in case the owner and its group get deleted.
    _group_name = meta_property('group_name')

    @property
    def group_name(self):
        """ Returns the name of the group this notice belongs to.

        If the group has been deleted, the last known name in brackets is
        returned.
        """

        if self.group:
            return self.group.name
        return '({})'.format(self._group_name) if self._group_name else None

    def _group_observer(self, group, name):
        """ Upates the last known name of the group.

        This never deletes the stored name, set ``self._group_name`` yourself
        if you want to clear it.

        """

        group_name = group.name if group else None
        group_name = group_name or name or self._group_name
        self._group_name = group_name


class GazetteNoticeFile(File):
    __mapper_args__ = {'polymorphic_identity': 'gazette_notice'}


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
    print_only = meta_property('print_only')

    #: True, if the official notice needs to be paid for
    at_cost = meta_property('at_cost')

    #: The billing address in case the official notice need to be paid for
    billing_address = content_property('billing_address')

    @observes('user', 'user.realname', 'user.username')
    def user_observer(self, user, realname, username):
        if hasattr(self, '_user_observer'):
            self._user_observer(user, realname, username)

    @observes('group', 'group.name')
    def group_observer(self, group, name):
        if hasattr(self, '_group_observer'):
            self._group_observer(group, name)

    def add_change(self, request, event, text=None):
        """ Adds en entry to the changelog. """

        session = object_session(self)
        try:
            username = request.identity.userid
            owner = str(UserCollection(session).by_username(username).id)
        except Exception:
            owner = None

        self.changes.append(
            GazetteNoticeChange(
                channel_id=str(self.id),
                owner=owner,
                text=text or '',
                meta={'event': event}
            )
        )

    def submit(self, request):
        """ Submit a drafted notice.

        This automatically adds en entry to the changelog.

        """

        super(GazetteNotice, self).submit()
        self.add_change(request, _("submitted"))

    def reject(self, request, comment):
        """ Reject a submitted notice.

        This automatically adds en entry to the changelog.

        """

        super(GazetteNotice, self).reject()
        self.add_change(request, _("rejected"), comment)

    def accept(self, request):
        """ Accept a submitted notice.

        This automatically adds en entry to the changelog.

        """

        super(GazetteNotice, self).accept()
        self.add_change(request, _("accepted"))

    def publish(self, request):
        """ Publish an accepted notice.

        This automatically adds en entry to the changelog.

        """

        super(GazetteNotice, self).publish()
        self.add_change(request, _("published"))

    @property
    def rejected_comment(self):
        """ Returns the comment of the last rejected change log entry. """

        for change in self.changes:
            if change.event == 'rejected':
                return change.text

        return ''

    @property
    def issues(self):
        """ Returns the issues sorted (by year/number). """

        issues = self._issues or {}
        keys = [IssueName.from_string(issue) for issue in (self._issues or {})]
        keys = sorted(keys, key=lambda x: (x.year, x.number))
        return OrderedDict((str(key), issues[str(key)]) for key in keys)

    @issues.setter
    def issues(self, value):
        if isinstance(value, dict):
            self._issues = value
        else:
            self._issues = {item: None for item in value}

    @property
    def issue_objects(self):
        if self._issues:
            query = object_session(self).query(Issue)
            query = query.filter(Issue.name.in_(self._issues.keys()))
            query = query.order_by(Issue.date)
            return query.all()
        return []

    def set_publication_number(self, issue, number):
        assert issue in self.issues
        issues = dict(self.issues)
        issues[issue] = str(number)
        self._issues = issues

    @property
    def category_id(self):
        """ The ID of the category. We store this the ID in the HSTORE (we use
        only one!) and additionaly store the title of the category in the
        category column.

        """
        keys = list(self.categories.keys())
        return keys[0] if keys else None

    @category_id.setter
    def category_id(self, value):
        self.categories = [value]

    @property
    def category_object(self):
        if self.category_id:
            query = object_session(self).query(Category)
            query = query.filter(Category.name == self.category_id)
            return query.first()

    @property
    def organization_id(self):
        """ The ID of the organization. We store this the ID in the HSTORE (we
        use only one!) and additionaly store the title of the organization in
        the organization column.

        """
        keys = list(self.organizations.keys())
        return keys[0] if keys else None

    @organization_id.setter
    def organization_id(self, value):
        self.organizations = [value]

    @property
    def organization_object(self):
        if self.organization_id:
            query = object_session(self).query(Organization)
            query = query.filter(Organization.name == self.organization_id)
            return query.first()

    @property
    def overdue_issues(self):
        """ Returns True, if any of the issue's deadline is reached. """

        if self._issues:
            query = object_session(self).query(Issue)
            query = query.filter(Issue.name.in_(self._issues.keys()))
            query = query.filter(Issue.deadline < utcnow())
            if query.first():
                return True

        return False

    @property
    def expired_issues(self):
        """ Returns True, if any of the issue's issue date is reached. """
        if self._issues:
            query = object_session(self).query(Issue)
            query = query.filter(Issue.name.in_(self._issues.keys()))
            query = query.filter(Issue.date <= date.today())
            if query.first():
                return True

        return False

    @property
    def invalid_category(self):
        """ Returns True, if the category of the is invalid or inactive. """
        query = object_session(self).query(Category.active)
        query = query.filter(Category.name == self.category_id).first()
        return (not query[0]) if query else True

    @property
    def invalid_organization(self):
        """ Returns True, if the category of the is invalid or inactive. """
        query = object_session(self).query(Organization.active)
        query = query.filter(Organization.name == self.organization_id).first()
        return (not query[0]) if query else True

    def apply_meta(self, session):
        """ Updates the category, organization and issue date from the meta
        values.

        """
        self.organization = None
        query = session.query(Organization.title)
        query = query.filter(Organization.name == self.organization_id).first()
        if query:
            self.organization = query[0]

        self.category = None
        query = session.query(Category.title)
        query = query.filter(Category.name == self.category_id).first()
        if query:
            self.category = query[0]

        self.first_issue = None
        if self._issues:
            query = session.query(Issue.date)
            query = query.filter(Issue.name.in_(self._issues.keys()))
            query = query.order_by(Issue.date).first()
            if query:
                self.first_issue = standardize_date(
                    as_datetime(query[0]), 'UTC'
                )


class GazetteNoticeChange(Message, CachedUserNameMixin):
    """ A changelog entry for an official notice. """

    __mapper_args__ = {'polymorphic_identity': 'gazette_notice'}

    #: the user which made this change
    user = relationship(
        User,
        primaryjoin=(
            'foreign(GazetteNoticeChange.owner) == cast(User.id, TEXT)'
        ),
        backref=backref('changes', lazy='select')
    )

    @observes('user', 'user.realname', 'user.username')
    def user_observer(self, user, realname, username):
        if hasattr(self, '_user_observer'):
            self._user_observer(user, realname, username)

    #: the notice which this change belongs to
    notice = relationship(
        GazetteNotice,
        primaryjoin=(
            'foreign(GazetteNoticeChange.channel_id)'
            '== cast(GazetteNotice.id, TEXT)'
        ),
        backref=backref(
            'changes',
            lazy='dynamic',
            cascade='all,delete-orphan',
            order_by='desc(GazetteNoticeChange.id)'
        )
    )

    #: the event
    event = meta_property('event')
