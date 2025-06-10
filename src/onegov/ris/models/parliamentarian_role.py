from __future__ import annotations

from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import Enum
from sqlalchemy import ForeignKey
from sqlalchemy import Text
from sqlalchemy.orm import relationship
from uuid import uuid4

from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin, ContentMixin
from onegov.core.orm.types import UUID
from onegov.ris import _


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import uuid
    from datetime import date
    from typing import Literal
    from typing import TypeAlias

    from onegov.ris.models.parliamentarian import RISParliamentarian
    from onegov.ris.models.parliamentary_group import RISParliamentaryGroup
    from onegov.ris.models.party import RISParty

    Role: TypeAlias = Literal[
        'none',
        'member',
        'vote_counter',
        'vice_president',
        'president',
    ]

    PartyRole: TypeAlias = Literal[
        'none',
        'member',
        'media_manager',
        'vote_counter',
        'vice_president',
        'president',
    ]

    ParliamentaryGroupRole: TypeAlias = Literal[
        'none',
        'non_permanent_member',
        'member',
        'substitute_member',
        'vote_counter',
        'secretary',
        'vice_president',
        'president',
    ]

PARLIAMENTARIAN_ROLES: dict[Role, str] = {
    'none': _('none'),
    'member': _('Member'),
    'vote_counter': _('Vote Counter'),
    'vice_president': _('Vice President'),
    'president': _('President'),
}

PARTY_ROLES: dict[PartyRole, str] = {
    'none': _('none'),
    'member': _('Member'),
    'media_manager': _('Media Manager'),
    'vote_counter': _('Vote Counter'),
    'vice_president': _('Vice President'),
    'president': _('President'),
}

PARLIAMENTARY_GROUP_ROLES: dict[ParliamentaryGroupRole, str] = {
    'none': _('none'),
    'non_permanent_member': _('Non-permanent Member'),
    'member': _('Member'),
    'substitute_member': _('Substitute Member'),
    'secretary': _('Secretary'),
    'vote_counter': _('Vote Counter'),
    'vice_president': _('Vice President'),
    'president': _('President'),
}


class RISParliamentarianRole(Base, ContentMixin, TimestampMixin):

    __tablename__ = 'ris_parliamentarian_roles'

    #: Internal ID
    id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
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

    #: The id of the parliamentarian
    parliamentarian_id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey('ris_parliamentarians.id'),
        nullable=False
    )

    #: The parliamentarian
    parliamentarian: relationship[RISParliamentarian] = relationship(
        'RISParliamentarian',
        back_populates='roles'
    )

    #: The parliament role name
    role: Column[Role] = Column(
        Enum(
            *PARLIAMENTARIAN_ROLES.keys(),  # type:ignore[arg-type]
            name='ris_parliamentarian_role'
        ),
        nullable=False,
        default='member'
    )

    #: The role as translated text
    @property
    def role_label(self) -> str:
        return PARLIAMENTARIAN_ROLES.get(self.role, '')

    #: Party ID as a foreign key
    party_id: Column[uuid.UUID | None] = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey('ris_parties.id'),
        nullable=True
    )

    #: The party
    party: relationship[RISParty | None] = relationship(
        'RISParty',
        back_populates='roles',
        primaryjoin='RISParliamentarianRole.party_id == RISParty.id'
    )

    #: The party role value
    party_role: Column[PartyRole] = Column(
        Enum(
            *PARTY_ROLES.keys(),  # type:ignore[arg-type]
            name='ris_party_role'
        ),
        nullable=False,
        default='member'
    )

    #: The party role as translated text
    @property
    def party_role_label(self) -> str:
        return PARTY_ROLES.get(self.party_role, '')

    #: The id of the parliamentary group
    parliamentary_group_id: Column[uuid.UUID | None] = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey('ris_parliamentary_groups.id'),
        nullable=True
    )

    #: The parliamentary group
    parliamentary_group: relationship[RISParliamentaryGroup | None]
    parliamentary_group = relationship(
        'RISParliamentaryGroup',
        back_populates='roles'
    )

    #: The parliamentary group role value
    parliamentary_group_role: Column[ParliamentaryGroupRole] = Column(
        Enum(
            *PARLIAMENTARY_GROUP_ROLES.keys(),  # type:ignore[arg-type]
            name='ris_parliamentary_group_role'
        ),
        nullable=False,
        default='member'
    )

    #: The parliamentary group role as translated text
    @property
    def parliamentary_group_role_label(self) -> str:
        return PARLIAMENTARY_GROUP_ROLES.get(self.parliamentary_group_role, '')

    #: The district
    district: Column[str | None] = Column(
        Text,
        nullable=True
    )

    #: Additional information
    additional_information: Column[str | None] = Column(
        Text,
        nullable=True
    )

    def __repr__(self) -> str:
        return (
            f'<ParliamentarianRole role={self.role} '
            f'party={self.party}'
        )
