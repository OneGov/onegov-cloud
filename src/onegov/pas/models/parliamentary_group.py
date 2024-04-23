from onegov.core.orm import Base
from onegov.core.orm.mixins import content_property
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.search import ORMSearchable
from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import Text
from sqlalchemy.orm import relationship
from uuid import uuid4

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from datetime import date
    from onegov.core.orm.mixins import dict_property
    from onegov.pas.models.parliamentarian_role import ParliamentarianRole


class ParliamentaryGroup(Base, ContentMixin, TimestampMixin, ORMSearchable):

    __tablename__ = 'pas_parliamentary_groups'

    es_public = False
    es_properties = {'name': {'type': 'text'}}

    @property
    def es_suggestion(self) -> str:
        return self.name

    @property
    def title(self) -> str:
        return self.name

    #: Internal ID
    id: 'Column[uuid.UUID]' = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: the name
    name: 'Column[str]' = Column(
        Text,
        nullable=False
    )

    #: The start date
    start: 'Column[date|None]' = Column(
        Date,
        nullable=True
    )

    #: The end date
    end: 'Column[date|None]' = Column(
        Date,
        nullable=True
    )

    #: The description
    description: 'dict_property[str | None]' = content_property()

    #: A parliamentary group may have n role
    roles: 'relationship[list[ParliamentarianRole]]'
    roles = relationship(
        'ParliamentarianRole',
        cascade='all, delete-orphan',
        back_populates='parliamentary_group'
    )
