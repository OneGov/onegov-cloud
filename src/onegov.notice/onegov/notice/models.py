from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.user.model import User
from sqlalchemy import Column
from sqlalchemy import Enum
from sqlalchemy import ForeignKey
from sqlalchemy import Text
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
            'drafted', 'submitted', 'published', 'rejected',
            name='official_notice_state'
        ),
        nullable=False,
        default='drafted'
    )

    #: The title of the notice.
    title = Column(Text, nullable=False)

    @property
    def text(self):
        """ Returns the text of the notice. """

        return (self.content or {}).get('text', '')

    @text.setter
    def text(self, value):
        """ Sets the text of the notice. """

        if self.content is None:
            self.content = {}
        self.content['text'] = value

    #: The category if the notice.
    category = Column(Text, nullable=True)

    #: The user that owns this notice.
    user_id = Column(UUID, ForeignKey(User.id), nullable=True)
    user = relationship(
        User, backref=backref('official_notices', lazy='dynamic')
    )

    def submit(self):
        """ Submit a drafted notice. """

        assert self.state == 'drafted' or self.state == 'rejected'
        self.state = 'submitted'

    def publish(self):
        """ Publish a submitted notice. """

        assert self.state == 'submitted'
        self.state = 'published'

    def reject(self):
        """ Reject a submitted notice. """

        assert self.state == 'submitted'
        self.state = 'rejected'
