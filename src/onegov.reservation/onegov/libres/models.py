from libres import new_scheduler
from libres.db.models import Allocation
from libres.db.models.base import ORMBase
from onegov.core.orm.mixins import ContentMixin, TimestampMixin
from onegov.core.orm.types import UUID
from sqlalchemy import Column, Integer, Text
from sqlalchemy.orm import relationship
from uuid import uuid4


class Resource(ORMBase, ContentMixin, TimestampMixin):
    """ A resource holds a single calendar with allocations and reservations.

    Note that this resource is not defined on the onegov.core declarative base.
    Instead it is defined using the libres base. This means we can't join
    data outside the libres models.

    This should however not be a problem as this onegov module is self
    contained and does not link to other onegov modules, except for core.

    If we ever want to link to other models (say link a reservation to a user),
    then we have to switch to a unified base. Ideally we would find a way
    to merge these bases somehow.

    """

    __tablename__ = 'resources'

    #: the unique id
    id = Column(UUID, primary_key=True, default=uuid4)

    #: a nice id for the url, readable by humans
    name = Column(Text, primary_key=False, unique=True)

    #: the title of the resource
    title = Column(Text, primary_key=False, nullable=False)

    #: the timezone this resource resides in
    timezone = Column(Text, nullable=False)

    #: the first hour shown on the calendar
    first_hour = Column(Integer, nullable=False, default=7)

    #: the last hour shown on the calendar
    last_hour = Column(Integer, nullable=False, default=18)

    #: the type of the resource, this can be used to create custom polymorphic
    #: subclasses. See `<http://docs.sqlalchemy.org/en/improve_toc/
    #: orm/extensions/declarative/inheritance.html>`_.
    type = Column(Text, nullable=True)

    __mapper_args__ = {
        "polymorphic_on": 'type'
    }

    allocations = relationship(
        Allocation,
        cascade="all, delete-orphan",
        primaryjoin='Resource.id == Allocation.resource',
        foreign_keys='Allocation.resource'
    )

    def get_scheduler(self, libres_context):
        assert self.id, "the id needs to be set"
        assert self.timezone, "the timezone needs to be set"

        return new_scheduler(libres_context, self.id, self.timezone)
