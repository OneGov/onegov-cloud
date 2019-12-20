from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin, TimestampMixin
from onegov.core.orm.types import UUID
from sqlalchemy import Column, Text, Date, Enum, ForeignKey
from sqlalchemy.orm import relationship
from uuid import uuid4


class Volunteer(Base, ContentMixin, TimestampMixin):
    """ Describes a volunteer that has signed up to fulfill an
    occasion need.

    """

    __tablename__ = 'volunteers'

    #: The id of the record, may be used publicly
    id = Column(UUID, primary_key=True, default=uuid4)

    #: The state of the volunteer
    state = Column(
        Enum(
            'open',
            'contacted',
            'confirmed',
            name='volunteer_state'
        ),
        nullable=False,
        default='open'
    )

    #: The need the volunteer signed up for
    need_id = Column(UUID, ForeignKey('occasion_needs.id'), nullable=False)
    need = relationship('OccasionNeed')

    #: A token linking multiple volunteer records (volunteers sign up for
    #: multiple needs at once, and are then multiplexed here)
    token = Column(UUID, nullable=False, default=uuid4)

    #: The first name of the volunteer
    first_name = Column(Text, nullable=False)

    #: The last name of the volunteer
    last_name = Column(Text, nullable=False)

    #: The address of the volunteer
    address = Column(Text, nullable=False)

    #: The zip code of the volunteer
    zip_code = Column(Text, nullable=False)

    #: The place of the volunteer
    place = Column(Text, nullable=False)

    #: The organisation of the volunteer
    organisation = Column(Text, nullable=True)

    #: The birth_date of the volunteer
    birth_date = Column(Date, nullable=False)

    #: The e-mail address of the volunteer
    email = Column(Text, nullable=False)

    #: The phone number of the volunteer
    phone = Column(Text, nullable=False)
