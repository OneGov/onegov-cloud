from __future__ import annotations

from datetime import date
from onegov.core.orm import Base
from onegov.core.orm.mixins import dict_markup_property
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import TimestampMixin
from onegov.pas.i18n import _
from onegov.search import ORMSearchable
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Mapped
from uuid import uuid4
from uuid import UUID


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.pas.models import PASParliamentarianRole


class Party(Base, ContentMixin, TimestampMixin, ORMSearchable):

    __tablename__ = 'par_parties'

    fts_type_title = _('Parties')
    fts_public = False
    fts_title_property = 'name'
    fts_properties = {'name': {'type': 'text', 'weight': 'A'}}

    #: The polymorphic type of party
    type: Mapped[str] = mapped_column(default=lambda: 'generic')

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'pas_party',
    }

    @property
    def title(self) -> str:
        return self.name

    #: Internal ID
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4
    )

    #: External ID
    external_kub_id: Mapped[UUID | None] = mapped_column(
        default=uuid4,
        unique=True
    )

    #: the name
    name: Mapped[str]

    #: The start date
    start: Mapped[date | None]

    #: The end date
    end: Mapped[date | None]

    #: The portrait
    portrait = dict_markup_property('content')

    #: The description
    description = dict_markup_property('content')

    #: A party may have n roles
    roles: Mapped[list[PASParliamentarianRole]] = relationship(
        cascade='all, delete-orphan',
        back_populates='party'
    )

    def __repr__(self) -> str:
        return f'<Party {self.name}>'
