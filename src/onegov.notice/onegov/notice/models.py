from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UTCDateTime
from onegov.core.orm.types import UUID
from onegov.user import User
from onegov.user import UserGroup
from sqlalchemy import Column
from sqlalchemy import Enum
from sqlalchemy import ForeignKey
from sqlalchemy import Text
from sqlalchemy.dialects.postgresql import HSTORE
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import backref
from sqlalchemy.orm import relationship
from uuid import uuid4


class OfficialNotice(Base, ContentMixin, TimestampMixin):

    """ Defines an official notice. """

    __tablename__ = 'official_notices'

    #: the type of the item, this can be used to create custom polymorphic
    #: subclasses of this class. See
    #: `<http://docs.sqlalchemy.org/en/improve_toc/\
    #: orm/extensions/declarative/inheritance.html>`_.
    type = Column(Text, nullable=True)

    __mapper_args__ = {
        'polymorphic_on': type
    }

    #: The internal ID of the notice.
    id = Column(UUID, primary_key=True, default=uuid4)

    #: A nice ID usable for the url, readable by humans.
    name = Column(Text)

    #: The state of the notice.
    state = Column(
        Enum(
            'drafted', 'submitted', 'published', 'rejected', 'accepted',
            name='official_notice_state'
        ),
        nullable=False,
        default='drafted'
    )

    #: The title of the notice.
    title = Column(Text, nullable=False)

    #: The text of the notice.
    text = Column(Text, nullable=True)

    #: The issues this notice appears in.
    _issues = Column(
        MutableDict.as_mutable(HSTORE), name='issues', nullable=True
    )

    @property
    def issues(self):
        return self._issues or {}

    @issues.setter
    def issues(self, value):
        if isinstance(value, dict):
            self._issues = value
        else:
            self._issues = {item: None for item in value}

    #: The date of the first issue of the notice.
    first_issue = Column(UTCDateTime, nullable=True)

    #: The category if the notice.
    category = Column(Text, nullable=True)

    #: The organization this notice belongs to.
    organization = Column(Text, nullable=True)

    #: The user that owns this notice.
    user_id = Column(UUID, ForeignKey(User.id), nullable=True)
    user = relationship(
        User, backref=backref('official_notices', lazy='select')
    )

    #: The group that owns this notice.
    group_id = Column(UUID, ForeignKey(UserGroup.id), nullable=True)
    group = relationship(
        UserGroup, backref=backref('official_notices', lazy='select')
    )

    def submit(self):
        """ Submit a drafted notice. """

        assert self.state == 'drafted' or self.state == 'rejected'
        self.state = 'submitted'

    def reject(self):
        """ Reject a submitted notice. """

        assert self.state == 'submitted'
        self.state = 'rejected'

    def accept(self):
        """ Accept a submitted notice. """

        assert self.state == 'submitted'
        self.state = 'accepted'

    def publish(self):
        """ Publish an accepted notice. """

        assert self.state == 'accepted'
        self.state = 'published'
