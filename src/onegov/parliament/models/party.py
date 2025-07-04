from __future__ import annotations

from onegov.core.orm import Base
from onegov.core.orm.mixins import dict_markup_property
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
    from onegov.parliament.models.parliamentarian_role import (
        ParliamentarianRole
    )


class Party(Base, ContentMixin, TimestampMixin, ORMSearchable):

    __tablename__ = 'par_parties'

    #: The type of the party
    type: Column[str] = Column(
        Text,
        nullable=False,
        default=lambda: 'generic'
    )

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'generic',
    }

    es_public = True
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

    #: External ID
    external_kub_id: Column[uuid.UUID | None] = Column(
        UUID,  # type:ignore[arg-type]
        nullable=True,
        default=uuid4,
        unique=True
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

    #: The portrait
    portrait = dict_markup_property('content')

    #: The description
    description = dict_markup_property('content')

    #: A party may have n roles
    roles: relationship[list[ParliamentarianRole]]
    roles = relationship(
        'ParliamentarianRole',
        cascade='all, delete-orphan',
        back_populates='party'
    )

    def __repr__(self) -> str:
        return f'<Party {self.name}>'


class RISParty(Party):

    __mapper_args__ = {
        'polymorphic_identity': 'ris_party',
    }

    es_type_name = 'ris_party'
