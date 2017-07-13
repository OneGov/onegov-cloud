from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.user import User
from sqlalchemy import Column
from sqlalchemy import Text
from sqlalchemy.orm import object_session
from uuid import uuid4


class UserGroup(Base, TimestampMixin):
    """ The group a user belongs to.

    The group is stored in the data field of the user.

    It should be probably possible to add a relation by defining the primary
    join something like:

        "foreign(coalesce(User.data, '{}'::json))->>'group'))
            == cast(UserGroup.id, TEXT)"

    But we don't really need the groups any other than for informational
    purpose.

    """

    __tablename__ = 'user_groups'

    #: The internal ID of the notice.
    id = Column(UUID, primary_key=True, default=uuid4)

    #: The name of the group
    name = Column(Text, nullable=True)

    @property
    def number_of_users(self):
        """ Returns the number of users in this group. """

        session = object_session(self)
        query = session.query(User.data).filter(User.data.isnot(None))
        return len([
            data for data in query if data[0].get('group') == str(self.id)
        ])
