from __future__ import annotations

from datetime import date
from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.parliament import _
from sqlalchemy import Enum
from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Mapped
from uuid import uuid4
from uuid import UUID


from typing import Literal, TypeAlias, TYPE_CHECKING
if TYPE_CHECKING:
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

    type: Mapped[str] = mapped_column(default=lambda: 'generic')

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'generic',
    }

    #: Internal ID
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4
    )

    #: The start date
    start: Mapped[date | None]

    #: The end date
    end: Mapped[date | None]

    #: The id of the parliamentarian
    parliamentarian_id: Mapped[UUID] = mapped_column(
        ForeignKey('par_parliamentarians.id'),
    )

    #: The parliamentarian
    parliamentarian: Mapped[Parliamentarian] = relationship(
        back_populates='roles',
        lazy='joined'
    )

    #: The role value
    role: Mapped[Role] = mapped_column(
        Enum(
            *PARLIAMENTARIAN_ROLES.keys(),
            name='par_parliamentarian_role'
        ),
        default='member'
    )

    #: The role as translated text
    @property
    def role_label(self) -> str:
        return PARLIAMENTARIAN_ROLES.get(self.role, '')

    #: The party role value
    party_role: Mapped[PartyRole] = mapped_column(
        Enum(
            *PARTY_ROLES.keys(),
            name='par_party_role'
        ),
        default='member'
    )

    #: The party role as translated text
    @property
    def party_role_label(self) -> str:
        return PARTY_ROLES.get(self.party_role, '')

    #: The id of the parliamentary group
    parliamentary_group_id: Mapped[UUID | None] = mapped_column(
        ForeignKey('par_parliamentary_groups.id')
    )

    #: The parliamentary group
    parliamentary_group: Mapped[ParliamentaryGroup | None] = relationship(
        back_populates='roles'
    )

    #: The parliamentary group role value
    parliamentary_group_role: Mapped[ParliamentaryGroupRole] = mapped_column(
        Enum(
            *PARLIAMENTARY_GROUP_ROLES.keys(),
            name='par_parliamentary_group_role'
        ),
        default='member'
    )

    #: The parliamentary group role as translated text
    @property
    def parliamentary_group_role_label(self) -> str:
        return PARLIAMENTARY_GROUP_ROLES.get(self.parliamentary_group_role, '')

    #: The district
    district: Mapped[str | None]

    #: Additional information
    additional_information: Mapped[str | None]

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} role={self.role}>'
