from uuid import uuid4
from sqlalchemy import Column, Text, ForeignKey, JSON, Enum
from onegov.core.orm import Base
from onegov.core.orm.types import UUID
from onegov.core.orm.mixins import meta_property
from sqlalchemy.orm import relationship, backref


ATTENDEE_TITLES = ('mr', 'ms', 'none')


class Attendee(Base):

    __tablename__ = 'fsi_attendees'

    user_id = Column(UUID, ForeignKey('users.id'), nullable=True)
    title = Column(
        Enum(*ATTENDEE_TITLES, name='title'), nullable=False, default='none')

    id = Column(UUID, primary_key=True, default=uuid4)
    first_name = Column(Text, nullable=False)
    last_name = Column(Text, nullable=False)
    email = Column(Text, nullable=False, unique=True)
    address = meta_property('address')

    meta = Column(JSON, nullable=True, default=dict)

    reservations = relationship(
            'Reservation',
            backref=backref(
                'attendee',
            ))
