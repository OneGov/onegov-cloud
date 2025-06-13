from __future__ import annotations

from datetime import date
from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.file import AssociatedFiles
from onegov.file import NamedFile
from onegov.parliament import _
from onegov.search import ORMSearchable
from sqlalchemy import Column, or_
from sqlalchemy import Date
from sqlalchemy import Enum
from sqlalchemy import Text
from sqlalchemy.orm import relationship
from uuid import uuid4


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Literal
    from typing import TypeAlias

    from sqlalchemy.orm import Session
    import uuid

    from onegov.parliament.models import (
        Attendence,
        CommissionMembership,
        PoliticalBusinessParticipation,
        Party,
        ParliamentarianRole,
    )

    Gender: TypeAlias = Literal[
        'male',
        'female',
    ]
    ShippingMethod: TypeAlias = Literal[
        'a',
        'plus',
        'registered',
        'confidential',
        'personal',
    ]


GENDERS: dict[Gender, str] = {
    'male': _('male'),
    'female': _('female'),
}


SHIPPING_METHODS: dict[ShippingMethod, str] = {
    'a': _('A mail'),
    'plus': _('A mail plus'),
    'registered': _('registered'),
    'confidential': _('confidential'),
    'personal': _('personal / confidential')
}


class Parliamentarian(Base, ContentMixin, TimestampMixin, AssociatedFiles,
                      ORMSearchable):

    __tablename__ = 'par_parliamentarians'

    parliamentarian_type: Column[str] = Column(
        Text,
        nullable=False,
        default=lambda: 'generic'
    )

    __mapper_args__ = {
        'polymorphic_on': parliamentarian_type,
        'polymorphic_identity': 'generic',
    }

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
        UUID,   # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: External ID
    #
    # Note: Value can only be None if the data is imported from an Excel file.
    # Fixme: The excel data import will not be used in the future so we will be
    # able to make this Non-Nullable soon.
    external_kub_id: Column[uuid.UUID | None] = Column(
        UUID,   # type:ignore[arg-type]
        nullable=True,
        default=uuid4,
        unique=True
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

    #: The contract number
    contract_number: Column[str | None] = Column(
        Text,
        nullable=True
    )

    #: The gender value
    gender: Column[Gender] = Column(
        Enum(
            *GENDERS.keys(),  # type:ignore[arg-type]
            name='pas_gender'
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

    #: The shipping method value
    shipping_method: Column[ShippingMethod] = Column(
        Enum(
            *SHIPPING_METHODS.keys(),   # type:ignore[arg-type]
            name='pas_shipping_methods'
        ),
        nullable=False,
        default='a'
    )

    #: The shipping method as translated text
    @property
    def shipping_method_label(self) -> str:
        return SHIPPING_METHODS.get(self.shipping_method, '')

    #: The shipping address
    shipping_address: Column[str | None] = Column(
        Text,
        nullable=True
    )

    #: The shipping address addition
    shipping_address_addition: Column[str | None] = Column(
        Text,
        nullable=True
    )

    #: The shipping address zip code
    shipping_address_zip_code: Column[str | None] = Column(
        Text,
        nullable=True
    )

    #: The shipping address city
    shipping_address_city: Column[str | None] = Column(
        Text,
        nullable=True
    )

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

    #: The salutation used in the address
    salutation_for_address: Column[str | None] = Column(
        Text,
        nullable=True
    )

    #: The salutation used for letters
    salutation_for_letter: Column[str | None] = Column(
        Text,
        nullable=True
    )

    #: How bills should be delivered
    forwarding_of_bills: Column[str | None] = Column(
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
    roles: relationship[list[ParliamentarianRole]]
    roles = relationship(
        'ParliamentarianRole',
        cascade='all, delete-orphan',
        back_populates='parliamentarian',
        order_by='desc(ParliamentarianRole.start)'
    )

    def get_party_during_period(
        self, start_date: date, end_date: date, session: Session
    ) -> Party | None:
        """Get the party this parliamentarian belonged to during a specific
        period."""

        from onegov.parliament.models.parliamentarian_role import (
            ParliamentarianRole
        )
        role = (
            session.query(ParliamentarianRole)
            .filter(
                ParliamentarianRole.parliamentarian_id == self.id,
                ParliamentarianRole.party_id.isnot(
                    None
                ),
                or_(
                    ParliamentarianRole.end.is_(None),
                    ParliamentarianRole.end >= start_date,
                ),
                ParliamentarianRole.start
                <= end_date,
            )
            .order_by(ParliamentarianRole.start.desc())
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

    #: A parliamentarian may be part of n commissions
    commission_memberships: relationship[list[CommissionMembership]]
    commission_memberships = relationship(
        'CommissionMembership',
        cascade='all, delete-orphan',
        back_populates='parliamentarian'
    )

    #: A parliamentarian may attend meetings
    attendences: relationship[list[Attendence]] = relationship(
        'Attendence',
        cascade='all, delete-orphan',
        back_populates='parliamentarian'
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


class RISParliamentarian(Parliamentarian):

    __mapper_args__ = {
        'polymorphic_identity': 'ris_parliamentarian',
    }

    es_type_name = 'ris_parliamentarian'

    #: political businesses participations [0..n]
    political_businesses: relationship[list[PoliticalBusinessParticipation]]
    political_businesses = relationship(
        'PoliticalBusinessParticipation',
        back_populates='parliamentarian',
        lazy='joined'
    )
