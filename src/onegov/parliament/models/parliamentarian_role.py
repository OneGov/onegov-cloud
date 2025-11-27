from __future__ import annotations

from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.parliament import _
from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import Enum
from sqlalchemy import ForeignKey
from sqlalchemy import Text
from sqlalchemy.orm import relationship
from uuid import uuid4


from typing import Literal, TypeAlias, TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from datetime import date

    from onegov.parliament.models import Parliamentarian
    from onegov.parliament.models import ParliamentaryGroup

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

PARLIAMENTARIAN_ROLES: dict[Role, str] = {
    'none': _('none'),
    'member': _('Member'),
    'vote_counter': _('Vote counter'),
    'vice_president': _('Vice president'),
    'president': _('President'),
}

PARTY_ROLES: dict[PartyRole, str] = {
    'none': _('none'),
    'member': _('Member'),
    'media_manager': _('Media Manager'),
    'vote_counter': _('Vote counter'),
    'vice_president': _('Vice president'),
    'president': _('President'),
}

PARLIAMENTARY_GROUP_ROLES: dict[PartyRole, str] = {
    'none': _('none'),
    'member': _('Member'),
    'vote_counter': _('Vote counter'),
    'vice_president': _('Vice president'),
    'president': _('President of the parliamentary group'),
}


class ParliamentarianRole(Base, TimestampMixin):

    __tablename__ = 'par_parliamentarian_roles'

    type: Column[str] = Column(
        Text,
        nullable=False,
        default=lambda: 'generic'
    )

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'generic',
    }

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
        ForeignKey('par_parliamentarians.id'),
        nullable=False
    )

    #: The parliamentarian
    parliamentarian: relationship[Parliamentarian] = relationship(
        'Parliamentarian',
        back_populates='roles',
        lazy='joined'
    )

    #: The role value
    role: Column[Role] = Column(
        Enum(
            *PARLIAMENTARIAN_ROLES.keys(),  # type:ignore[arg-type]
            name='par_parliamentarian_role'
        ),
        nullable=False,
        default='member'
    )

    #: The role as translated text
    @property
    def role_label(self) -> str:
        return PARLIAMENTARIAN_ROLES.get(self.role, '')

    #: The party role value
    party_role: Column[PartyRole] = Column(
        Enum(
            *PARTY_ROLES.keys(),  # type:ignore[arg-type]
            name='par_party_role'
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
        ForeignKey('par_parliamentary_groups.id'),
        nullable=True
    )

    #: The parliamentary group
    parliamentary_group: relationship[ParliamentaryGroup | None]
    parliamentary_group = relationship(
        'ParliamentaryGroup',
        back_populates='roles'
    )

    #: The parliamentary group role value
    parliamentary_group_role: Column[ParliamentaryGroupRole] = Column(
        Enum(
            *PARLIAMENTARY_GROUP_ROLES.keys(),  # type:ignore[arg-type]
            name='par_parliamentary_group_role'
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
        return f'<{self.__class__.__name__} role={self.role}>'
