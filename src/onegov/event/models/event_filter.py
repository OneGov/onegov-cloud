from functools import lru_cache
from uuid import uuid4

from sqlalchemy import Column, Text
from sqlalchemy.orm import object_session

from onegov.core.orm import Base
from onegov.core.orm.types import UUID
from onegov.event.types import EventConfigurationStorage, EventConfiguration
from onegov.form import flatten_fieldsets, parse_formcode


class EventFilter(Base):
    """

    """

    __tablename__ = 'event_filters'

    #: An internal id for references (not public)
    id: 'Column[UUID]' = Column(UUID, primary_key=True, default=uuid4)

    #: The custom form definition of the event filters
    structure: 'Column[str | None]' = Column(Text, nullable=False)

    #: The configuration of the contained entries
    configuration = Column(EventConfigurationStorage, nullable=False)

    @property
    def entry_cls_name(self):
        return 'EventFilter'

    @property
    def entry_cls(self):
        return self.__class__._decl_class_registry[self.entry_cls_name]

    @property
    def fields(self):
        return self.fields_from_structure(self.structure)

    @staticmethod
    @lru_cache(maxsize=1)
    def fields_from_structure(structure):
        return tuple(flatten_fieldsets(parse_formcode(structure)))

    @classmethod
    def instance_from_object(self, object):
        session = object_session(object)
        return session.query(EventFilter).first() or None

    def update(self, structure, configuration):
        self.structure = structure
        self.configuration = EventConfiguration(order=[],
                                                keywords=configuration)
