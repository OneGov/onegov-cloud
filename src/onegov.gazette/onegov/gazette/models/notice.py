from collections import OrderedDict
from onegov.chat import Message
from onegov.core.orm.mixins import meta_property
from onegov.gazette import _
from onegov.gazette.models.principal import Issue
from onegov.notice import OfficialNotice
from onegov.user import User
from onegov.user import UserCollection
from sedate import as_datetime
from sedate import standardize_date
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


class GazetteNotice(OfficialNotice, CachedUserNameMixin, CachedGroupNameMixin):
    """ An official notice with extras.

    Instead of using categories and organizations directly, the IDs defined
    in the principal are used: The IDs are stored in the meta and the values
    are copied to the columns when calling ``apply_meta``.

    It's possible to add a changelog entry by calling ``add_change``. Changelog
    entries are created for state changes by default.

    The user name accessible by ``user_name`` gets cached in case the user is
    deleted.

    The group name accessible by ``group_name`` gets cached in case the group
    is deleted.

    """

    __mapper_args__ = {'polymorphic_identity': 'gazette'}

    #: True, if the official notice needs to be paid for
    at_cost = meta_property('at_cost')

    #: The ID of the organization. We store this in addition to the
    #: organization name to allow changing organization names.
    organization_id = meta_property('organization_id')

    #: The ID of the category. We store this in addition to the
    #: category name to allow changing category names.
    category_id = meta_property('category_id')

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
        except:
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
        keys = (Issue.from_string(issue) for issue in (self._issues or {}))
        keys = sorted(keys, key=lambda x: (x.year, x.number))
        return OrderedDict((str(key), issues[str(key)]) for key in keys)

    @issues.setter
    def issues(self, value):
        if isinstance(value, dict):
            self._issues = value
        else:
            self._issues = {item: None for item in value}

    def apply_meta(self, principal):
        """ Updates the category, organization and issue date from the meta
        values.

        """
        self.organization = principal.organizations.get(self.organization_id)
        self.category = principal.categories.get(self.category_id)

        issues = [Issue.from_string(issue) for issue in self.issues]
        issues = [principal.issue(issue) for issue in issues]
        issues = sorted([issue.issue_date for issue in issues if issue])
        if issues:
            self.first_issue = standardize_date(
                as_datetime(issues[0]), 'Europe/Zurich'
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
