from onegov.chat import Message
from onegov.core.orm.mixins import meta_property
from onegov.gazette import _
from onegov.gazette.models.principal import Issue
from onegov.notice import OfficialNotice
from onegov.user import User
from onegov.user import UserCollection
from sedate import as_datetime
from sedate import standardize_date
from sqlalchemy.orm import backref
from sqlalchemy.orm import object_session
from sqlalchemy.orm import relationship


class GazetteNotice(OfficialNotice):
    __mapper_args__ = {'polymorphic_identity': 'gazette'}

    #: The ID of the organization. We store this in addition to the
    #: organization name to allow changing organization names.
    organization_id = meta_property('organization_id')

    #: The ID of the category. We store this in addition to the
    #: category name to allow changing category names.
    category_id = meta_property('category_id')

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


class GazetteNoticeChange(Message):
    """ A changelog entry for an official notice. """

    __mapper_args__ = {'polymorphic_identity': 'gazette_notice'}

    #: the user which made this change
    user = relationship(
        User,
        primaryjoin=(
            'foreign(GazetteNoticeChange.owner) == cast(User.id, TEXT)'
        ),
        backref=backref('changes', lazy='dynamic')
    )

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
