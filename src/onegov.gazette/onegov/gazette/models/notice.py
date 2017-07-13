from onegov.chat import Message
from onegov.gazette import _
from onegov.notice import OfficialNotice
from onegov.user import User
from onegov.user import UserCollection
from sqlalchemy.orm import backref
from sqlalchemy.orm import object_session
from sqlalchemy.orm import relationship


class GazetteNotice(OfficialNotice):
    __mapper_args__ = {'polymorphic_identity': 'gazette'}

    @property
    def issues(self):
        """ Returns the issues this notice appears in. The result is a dict
        with the issue numbers as keys and an optional code as value.

        """

        return (self.meta or {}).get('issues', {})

    @issues.setter
    def issues(self, value):
        """ Sets the issues this notice appears in. """

        if not self.meta:
            self.meta = {}

        if isinstance(value, dict):
            self.meta['issues'] = value
        else:
            self.meta['issues'] = {item: None for item in value}

    def add_change(self, request, text):
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
                text=text
            )
        )

    def submit(self, request):
        """ Submit a drafted notice.

        This automatically adds en entry to the changelog.

        """

        super(GazetteNotice, self).submit()
        self.add_change(request, _("submitted"))

    def publish(self, request):
        """ Publish a submitted notice.

        This automatically adds en entry to the changelog.

        """

        super(GazetteNotice, self).publish()
        self.add_change(request, _("published"))

    def reject(self, request):
        """ Reject a submitted notice.

        This automatically adds en entry to the changelog.

        """

        super(GazetteNotice, self).reject()
        self.add_change(request, _("rejected"))


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
            'changes', lazy='dynamic', cascade='all,delete-orphan'
        )
    )
