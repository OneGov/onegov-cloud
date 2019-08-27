from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UTCDateTime
from onegov.core.orm.types import UUID
from onegov.user import User
from onegov.user import UserGroup
from sedate import utcnow
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

    """ Defines an official notice.

    The notice follows a typcical state transition: drafted by an editor ->
    submitted by and editor to a publisher -> accepted by a publisher ->
    published by the publisher. It may be alternatively rejected by a publisher
    when submitted.

    The notice typically has a title and a text, belongs to a user and a user
    group, appears in one ore more issues and belongs to one or more categories
    and organizations.

    You can set the date of the first issue besides setting the issues (to
    allow filtering by date for example).

    You can set the category and organization directly instead of using the
    HSTOREs (or use both).

    """

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
            'drafted',
            'submitted',
            'rejected',
            'imported',
            'accepted',
            'published',
            name='official_notice_state'
        ),
        nullable=False,
        default='drafted'
    )

    #: The title of the notice.
    title = Column(Text, nullable=False)

    #: The text of the notice.
    text = Column(Text, nullable=True)

    #: The author of the notice.
    author_name = Column(Text, nullable=True)

    #: The place (part of the signature).
    author_place = Column(Text, nullable=True)

    #: The date (part of the signature)
    author_date = Column(UTCDateTime, nullable=True)

    #: A note to the notice.
    note = Column(Text, nullable=True)

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

    #: The expiry date of the notice
    expiry_date = Column(UTCDateTime, nullable=True)

    @property
    def expired(self):
        """ Returns True, if the notice is expired. """

        if self.expiry_date:
            return self.expiry_date < utcnow()
        return False

    #: The categories of this notice.
    _categories = Column(
        MutableDict.as_mutable(HSTORE), name='categories', nullable=True
    )

    @property
    def categories(self):
        return self._categories or {}

    @categories.setter
    def categories(self, value):
        if isinstance(value, dict):
            self._categories = value
        else:
            self._categories = {item: None for item in value}

    #: The category of the notice.
    category = Column(Text, nullable=True)

    #: The organization this notice belongs to.
    organization = Column(Text, nullable=True)

    #: The categories of this notice.
    _organizations = Column(
        MutableDict.as_mutable(HSTORE), name='organizations', nullable=True
    )

    @property
    def organizations(self):
        return self._organizations or {}

    @organizations.setter
    def organizations(self, value):
        if isinstance(value, dict):
            self._organizations = value
        else:
            self._organizations = {item: None for item in value}

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

    #: The source from where this notice has been imported.
    source = Column(Text, nullable=True)

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

        assert self.state == 'submitted' or self.state == 'imported'
        self.state = 'accepted'

    def publish(self):
        """ Publish an accepted notice. """

        assert self.state == 'accepted'
        self.state = 'published'
