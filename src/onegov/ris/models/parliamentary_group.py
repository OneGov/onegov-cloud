from __future__ import annotations

from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import Text
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from uuid import uuid4

from onegov.core.orm import Base
from onegov.core.orm.mixins import dict_markup_property
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.search import ORMSearchable

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import uuid

    from datetime import date

    from onegov.ris.models import RISParliamentarian
    from onegov.ris.models import RISParliamentarianRole


class RISParliamentaryGroup(Base, ContentMixin, TimestampMixin, ORMSearchable):
    """ Fraktion """

    __tablename__ = 'ris_parliamentary_groups'

    es_public = False
    es_properties = {'name': {'type': 'text'}}

    @property
    def es_suggestion(self) -> str:
        return self.name

    @property
    def title(self) -> str:
        return self.name

    #: Internal ID
    id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: the name
    name: Column[str] = Column(
        Text,
        nullable=False
    )

    #: The start date
    start: Column[date | None] = Column(
        Date,
        nullable=True
    )

    #: The end date
    end: Column[date | None] = Column(
        Date,
        nullable=True
    )

    #: The description
    description = dict_markup_property('content')

    #: A parliamentary group may have n role
    roles: relationship[list[RISParliamentarianRole]]
    roles = relationship(
        'RISParliamentarianRole',
        back_populates='parliamentary_group',
    )

    # #: the id of the parliamentarian
    parliamentarian_id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey('ris_parliamentarians.id'),
        nullable=False
    )

    members: relationship[list[RISParliamentarian]] = relationship(
        'RISParliamentarian',
        back_populates='political_groups',
    )

    def __repr__(self) -> str:
        return f'<ParliamentaryGroup {self.name}>'
