from uuid import uuid4
from sqlalchemy import Column, Text, ForeignKey, JSON, Enum
from onegov.core.orm import Base
from onegov.core.orm.types import UUID
from onegov.core.orm.mixins import meta_property
from sqlalchemy.orm import relationship

ATTENDEE_TITLES = ('mr', 'ms', 'none')


class CourseAttendee(Base):

    __tablename__ = 'fsi_attendees'

    user_id = Column(UUID, ForeignKey('users.id'), nullable=True)
    title = Column(
        Enum(*ATTENDEE_TITLES, name='title'), nullable=False, default='none')

    id = Column(UUID, primary_key=True, default=uuid4)
    first_name = Column(Text)
    last_name = Column(Text)
    email = Column(Text)
    address = meta_property('address')

    # Description of attendee is a placeholder
    dummy_desc = Column(Text)

    def __str__(self):
        return f'{self.last_name or "", self.first_name or self.dummy_desc}'

    meta = Column(JSON, nullable=True, default=dict)

    reservations = relationship(
        'Reservation',
        backref='attendee',
        lazy='dynamic',
        cascade='all, delete-orphan')

    @property
    def course_events(self):
        raise NotImplementedError
