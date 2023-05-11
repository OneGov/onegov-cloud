from onegov.core.orm import Base
from onegov.core.orm.mixins import content_property
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.file import AssociatedFiles
from onegov.file import NamedFile
from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy.orm import backref
from sqlalchemy.orm import relationship
from uuid import uuid4


class Assembly(Base, ContentMixin, TimestampMixin, AssociatedFiles):

    __tablename__ = 'landsgemeinde_assemblies'

    #: Internal number of the event
    id = Column(UUID, primary_key=True, default=uuid4)

    #: The date of the assembly
    date = Column(Date, nullable=False, unique=True)

    #: The overview (text) over the assembly
    overview = content_property()

    #: The memorial of the assembly
    memorial_pdf = NamedFile()

    #: The protocol of the assembly
    protocol_pdf = NamedFile()

    #: The audio of the assembly
    audio_mp3 = NamedFile()

    # todo: ?
    # @hybrid_property
    # def counted(self):
    #     """ True if all agenda items have been counted. """
    #
    #     count = self.agenda_items.count()
    #     return (sum(1 for r in self.agenda_items if r.counted) == count)
    #
    # @counted.expression
    # def counted(self):
    #     expr = select([
    #         func.coalesce(func.bool_and(AssemblyAgendaItem.counted), False)
    #     ])
    #     expr = expr.where(AssemblyAgendaItem.election_id == self.id)
    #     expr = expr.label('counted')
    #
    #     return expr
    #
    # @property
    # def progress(self):
    #     """ Returns a tuple with the first value being the number of counted
    #     agenda items and the second value being the number of total
    #     agenda items.
    #
    #     """
    #
    #     query = object_session(self).query(AssemblyAgendaItem)
    #     query = query.with_entities(AssemblyAgendaItem.counted)
    #     query = query.filter(AssemblyAgendaItem.assembly_id == self.id)
    #
    #     results = query.all()
    #
    #     return sum(1 for r in results if r[0]), len(results)

    #: An assembly contains n agenda items
    agenda_items = relationship(
        'AgendaItem',
        cascade='all, delete-orphan',
        backref=backref('assembly'),
        lazy='dynamic',
        order_by='AgendaItem.number',
    )

    # todo: ???
    #
    # @cached_property
    # def cached_items(self):
    #     return self.agenda_items.options(
    #         undefer(AssemblyAgendaItem.content)
    #     ).order_by(AssemblyAgendaItem.number).all()
    #
    # @property
    # def active_item(self):
    #     result = None
    #     if not self.completed:
    #         for agenda_item in self.cached_items:
    #             result = agenda_item
    #             if not agenda_item.counted:
    #                 break
    #     return result
