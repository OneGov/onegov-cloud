from uuid import uuid4

from sqlalchemy import Column, Boolean, Interval, ForeignKey, Text
from sqlalchemy.orm import relationship

from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.fsi.models.reservation import Reservation


class Course(Base, TimestampMixin):

    __tablename__ = 'fsi_courses'

    id = Column(UUID, primary_key=True, default=uuid4)

    description = Column(Text, nullable=False)
    # Short description
    name = Column(Text, nullable=False)

    presenter_name = Column(Text, nullable=False)
    presenter_company = Column(Text, nullable=False)

    # If the course has to be refreshed after some interval
    mandatory_refresh = Column(Boolean, nullable=False)
    # Refresh interval
    refresh_interval = Column(Interval, nullable=False)

    # Creator of this course
    user_id = Column(UUID, ForeignKey('users.id'), nullable=True)
    reservations = relationship(Reservation, backref='course_item')
