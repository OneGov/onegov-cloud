from __future__ import annotations

from onegov.core.orm import Base
from onegov.core.orm.mixins import dict_markup_property
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.search import Searchable

from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import Text
from sqlalchemy.orm import relationship
from uuid import uuid4


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import uuid
    from datetime import date
    from onegov.parliament.models import ParliamentarianRole


class ParliamentaryGroup(Base, ContentMixin, TimestampMixin, Searchable):
    """ Fraktion """

    __tablename__ = 'par_parliamentary_groups'

    fts_public = True
    fts_properties = {
        'title': {'type': 'localized', 'weight': 'A'},
        'description': {'type': 'localized', 'weight': 'B'},
    }

    type: Column[str] = Column(
        Text,
        nullable=False,
        default=lambda: 'generic'
    )

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'generic',
    }

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
        UUID,   # type:ignore[arg-type]
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

    #: The description
    description = dict_markup_property('content')

    #: A parliamentary group may have n role
    roles: relationship[list[ParliamentarianRole]]
    roles = relationship(
        'ParliamentarianRole',
        cascade='all, delete-orphan',
        back_populates='parliamentary_group'
    )

    def __repr__(self) -> str:
        return f'<ParliamentaryGroup {self.name}>'
