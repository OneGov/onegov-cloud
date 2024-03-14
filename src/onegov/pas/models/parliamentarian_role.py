from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.pas import _
from onegov.pas.models.parliamentarian import Parliamentarian
from onegov.pas.models.parliamentary_group import ParliamentaryGroup
from onegov.pas.models.party import Party
from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import Enum
from sqlalchemy import ForeignKey
from sqlalchemy import Text
from sqlalchemy.orm import relationship
from uuid import uuid4

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from datetime import date
    from typing import Literal
    from typing_extensions import TypeAlias

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
        'member',
        'vote_counter',
        'president',
    ]

PARLIAMENTARIAN_ROLES: dict['Role', str] = {
    'none': _('none'),
    'member': _('Member'),
    'vote_counter': _('Vote counter'),
    'vice_president': _('Vice president'),
    'president': _('President'),
}

PARTY_ROLES: dict['PartyRole', str] = {
    'none': _('none'),
    'member': _('Member'),
    'media_manager': _('Media Manager'),
    'vote_counter': _('Vote counter'),
    'vice_president': _('Vice president'),
    'president': _('President'),
}

PARLIAMENTARY_GROUP_ROLES: dict['PartyRole', str] = {
    'none': _('none'),
    'member': _('Member'),
    'vote_counter': _('Vote counter'),
    'vice_president': _('Vice president'),
    'president': _('President of the parliamentary group'),
}


class ParliamentarianRole(Base, ContentMixin, TimestampMixin):

    __tablename__ = 'pas_parliamentarian_roles'

    #: Internal ID
    id: 'Column[uuid.UUID]' = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
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

    #: The id of the parliamentarian
    parliamentarian_id: 'Column[uuid.UUID]' = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey('pas_parliamentarians.id'),
        nullable=False
    )

    #: The parliamentarian
    parliamentarian: 'relationship[Parliamentarian]' = relationship(
        Parliamentarian,
        back_populates='roles'
    )

    #: The role value
    role: 'Column[Role]' = Column(
        Enum(
            *PARLIAMENTARIAN_ROLES.keys(),  # type:ignore[arg-type]
            name='pas_pariliamentarian_role'
        ),
        nullable=False,
        default='member'
    )

    #: The role as translated text
    @property
    def role_label(self) -> str:
        return PARLIAMENTARIAN_ROLES.get(self.role, '')

    #: The id of the party
    party_id: 'Column[uuid.UUID|None]' = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey('pas_parties.id'),
        nullable=True
    )

    #: The party
    party: 'relationship[Party|None]' = relationship(
        Party,
        back_populates='roles'
    )

    #: The party role value
    party_role: 'Column[PartyRole]' = Column(
        Enum(
            *PARTY_ROLES.keys(),  # type:ignore[arg-type]
            name='pas_party_role'
        ),
        nullable=False,
        default='member'
    )

    #: The party role as translated text
    @property
    def party_role_label(self) -> str:
        return PARTY_ROLES.get(self.party_role, '')

    #: The id of the parliamentary group
    parliamentary_group_id: 'Column[uuid.UUID|None]' = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey('pas_parliamentary_groups.id'),
        nullable=True
    )

    #: The parliamentary group
    parliamentary_group: 'relationship[ParliamentaryGroup|None]'
    parliamentary_group = relationship(
        ParliamentaryGroup,
        back_populates='roles'
    )

    #: The parliamentary group role value
    parliamentary_group_role: 'Column[ParliamentaryGroupRole]' = Column(
        Enum(
            *PARLIAMENTARY_GROUP_ROLES.keys(),  # type:ignore[arg-type]
            name='pas_parliamentary_group_role'
        ),
        nullable=False,
        default='member'
    )

    #: The parliamentary group role as translated text
    @property
    def parliamentary_group_role_label(self) -> str:
        return PARLIAMENTARY_GROUP_ROLES.get(self.parliamentary_group_role, '')

    #: The district
    district: 'Column[str|None]' = Column(
        Text,
        nullable=True
    )

    #: Additional information
    additional_information: 'Column[str|None]' = Column(
        Text,
        nullable=True
    )
