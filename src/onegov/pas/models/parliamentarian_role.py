from __future__ import annotations

from onegov.core.orm.types import UUID
from onegov.parliament.models import ParliamentarianRole
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from onegov.pas.models import Party


class PASParliamentarianRole(ParliamentarianRole):

    __mapper_args__ = {
        'polymorphic_identity': 'pas_parliamentarian_role',
    }

    #: The id of the party
    party_id: Column[uuid.UUID | None] = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey('par_parties.id'),
        nullable=True
    )

    #: The party
    party: relationship[Party | None] = relationship(
        'Party',
        back_populates='roles'
    )
