from __future__ import annotations

from onegov.parliament.models import ParliamentarianRole
from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Mapped
from uuid import UUID


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.pas.models import Party


class PASParliamentarianRole(ParliamentarianRole):

    __mapper_args__ = {
        'polymorphic_identity': 'pas_parliamentarian_role',
    }

    #: The id of the party
    party_id: Mapped[UUID | None] = mapped_column(ForeignKey('par_parties.id'))

    #: The party
    party: Mapped[Party | None] = relationship(back_populates='roles')
