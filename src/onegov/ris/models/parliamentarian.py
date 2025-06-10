from __future__ import annotations

from datetime import date
from sqlalchemy import Column, or_
from sqlalchemy import Date
from sqlalchemy import Enum
from sqlalchemy import Text
from sqlalchemy.orm import relationship
from uuid import uuid4

from onegov.core.orm import Base
from onegov.core.orm.types import UUID
from onegov.file import AssociatedFiles
from onegov.file import NamedFile
from onegov.ris import _
from onegov.ris.models.parliamentarian_role import RISParliamentarianRole
from onegov.search import ORMSearchable

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.orm import Session
    from typing import Literal
    from typing import TypeAlias

    from onegov.ris.models.membership import RISCommissionMembership
    from onegov.ris.models.parliamentary_group import RISParliamentaryGroup
    from onegov.ris.models.party import RISParty
    from onegov.ris.models.political_business import (
        RISPoliticalBusinessParticipation
    )

    Gender: TypeAlias = Literal[
        'male',
        'female',
    ]

GENDERS: dict[Gender, str] = {
    'male': _('male'),
    'female': _('female'),
}


class RISParliamentarian(Base, AssociatedFiles, ORMSearchable):
    __tablename__ = 'ris_parliamentarians'

    es_public = False
    es_properties = {
        'first_name': {'type': 'text'},
        'last_name': {'type': 'text'},
    }

    @property
    def es_suggestion(self) -> tuple[str, ...]:
        return (
            f'{self.first_name} {self.last_name}',
            f'{self.last_name} {self.first_name}'
        )

    @property
    def title(self) -> str:
        return f'{self.first_name} {self.last_name}'

    #: Internal ID
    id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: The first name
    first_name: Column[str] = Column(
        Text,
        nullable=False
    )

    #: The last name
    last_name: Column[str] = Column(
        Text,
        nullable=False
    )

    #: The personnel number
    personnel_number: Column[str | None] = Column(
        Text,
        nullable=True
    )

    #: The gender value
    gender: Column[Gender] = Column(
        Enum(
            *GENDERS.keys(),  # type:ignore[arg-type]
            name='ris_gender'
        ),
        nullable=False,
        default='male'
    )

    #: The gender as translated text
    @property
    def gender_label(self) -> str:
        return GENDERS.get(self.gender, '')

    @property
    def formal_greeting(self) -> str:
        # fixme: Use salutation
        """Returns the formal German greeting based on gender."""
        if self.gender == 'female':
            return 'Frau ' + self.first_name + ' ' + self.last_name
        return 'Herr ' + self.first_name + ' ' + self.last_name

    #: The private address
    private_address: Column[str | None] = Column(
        Text,
        nullable=True
    )

    #: The private address addition
    private_address_addition: Column[str | None] = Column(
        Text,
        nullable=True
    )

    #: The private address zip code
    private_address_zip_code: Column[str | None] = Column(
        Text,
        nullable=True
    )

    #: The private address city
    private_address_city: Column[str | None] = Column(
        Text,
        nullable=True
    )

    #: The date of birth
    date_of_birth: Column[date | None] = Column(
        Date,
        nullable=True
    )

    #: The date of death
    date_of_death: Column[date | None] = Column(
        Date,
        nullable=True
    )

    #: The place of origin
    place_of_origin: Column[str | None] = Column(
        Text,
        nullable=True
    )

    #: The occupation
    occupation: Column[str | None] = Column(
        Text,
        nullable=True
    )

    #: The academic title
    academic_title: Column[str | None] = Column(
        Text,
        nullable=True
    )

    #: The salutation
    salutation: Column[str | None] = Column(
        Text,
        nullable=True
    )

    #: The private phone number
    phone_private: Column[str | None] = Column(
        Text,
        nullable=True
    )

    #: The mobile phone number
    phone_mobile: Column[str | None] = Column(
        Text,
        nullable=True
    )

    #: The business phone number
    phone_business: Column[str | None] = Column(
        Text,
        nullable=True
    )

    #: The primary email address
    email_primary: Column[str | None] = Column(
        Text,
        nullable=True
    )

    #: The secondary email address
    email_secondary: Column[str | None] = Column(
        Text,
        nullable=True
    )

    #: The website
    website: Column[str | None] = Column(
        Text,
        nullable=True
    )

    #: The remarks
    remarks: Column[str | None] = Column(
        Text,
        nullable=True
    )

    #: A picture
    picture = NamedFile()

    #: A parliamentarian may have n roles
    roles: relationship[list[RISParliamentarianRole]]
    roles = relationship(
        'RISParliamentarianRole',
        cascade='all, delete-orphan',
        back_populates='parliamentarian',
        order_by='desc(ParliamentarianRole.start)'
    )

    #: political businesses participations [0..n]
    political_businesses: relationship[list[RISPoliticalBusinessParticipation]]
    political_businesses = relationship(
        'RISPoliticalBusinessParticipation',
        back_populates='parliamentarian',
        lazy='joined'
    )

    def get_party_during_period(
            self, start_date: date, end_date: date, session: Session
    ) -> RISParty | None:
        """Get the party this parliamentarian belonged to during a specific
        period."""

        role = (
            session.query(RISParliamentarianRole)
            .filter(
                RISParliamentarianRole.parliamentarian_id == self.id,
                RISParliamentarianRole.party_id.isnot(
                    None
                ),
                or_(
                    RISParliamentarianRole.end.is_(None),
                    RISParliamentarianRole.end >= start_date,
                ),
                RISParliamentarianRole.start
                <= end_date,
            )
            .order_by(RISParliamentarianRole.start.desc())
            .first()
        )

        return role.party if role else None

    @property
    def active(self) -> bool:
        if not self.roles:
            return True
        for role in self.roles:
            if role.end is None or role.end >= date.today():
                return True
        return False

    def active_during(self, start: date, end: date) -> bool:
        if not self.roles:
            return True
        for role in self.roles:
            role_start = role.start if role.start is not None else date.min
            role_end = role.end if role.end is not None else date.max
            if role_end >= start and role_start <= end:
                return True
        return False

    @property
    def display_name(self) -> str:
        return f'{self.first_name} {self.last_name}'

    #: A parliamentarian may be a member of n commissions
    commission_memberships: relationship[list[RISCommissionMembership]]
    commission_memberships = relationship(
        'RISCommissionMembership',
        cascade='all, delete-orphan',
        back_populates='parliamentarian'
    )

    political_groups: relationship[list[RISParliamentaryGroup]]
    political_groups = relationship(
        'RISParliamentaryGroup',
        back_populates='members',
        primaryjoin='RISParliamentarian.id == '
                    'RISParliamentaryGroup.parliamentarian_id',
    )

    def __repr__(self) -> str:
        info = [
            f'id={self.id}',
            f"last_name='{self.last_name}'",
            f"first_name='{self.first_name}'",
        ]
        if self.academic_title:
            info.append(f"title='{self.academic_title}'")
        if self.salutation:
            info.append(f"salutation='{self.salutation}'")
        if self.email_primary:
            info.append(
                f"email='{self.email_primary}'")

        return f"<Parliamentarian {', '.join(info)}>"
