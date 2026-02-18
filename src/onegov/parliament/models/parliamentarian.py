from __future__ import annotations

from datetime import date
from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import dict_property, content_property
from onegov.core.orm.mixins import TimestampMixin
from onegov.file import AssociatedFiles
from onegov.file import NamedFile
from onegov.parliament import _
from sqlalchemy import and_, or_, exists
from sqlalchemy import Enum
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Mapped
from uuid import uuid4
from uuid import UUID


from typing import Any, Literal, TypeAlias, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.parliament.models import (
        CommissionMembership,
        ParliamentarianRole,
    )
    from sqlalchemy.sql import ColumnElement

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


class Parliamentarian(Base, ContentMixin, TimestampMixin, AssociatedFiles):

    __tablename__ = 'par_parliamentarians'

    type: Mapped[str] = mapped_column(default=lambda: 'generic')

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'generic',
    }

    @property
    def title(self) -> str:
        return f'{self.first_name} {self.last_name}'

    #: Internal ID
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4
    )

    #: External ID
    #
    # Note: Value can only be None if the data is imported from an Excel file.
    # Fixme: The excel data import will not be used in the future so we will be
    # able to make this Non-Nullable soon.
    external_kub_id: Mapped[UUID | None] = mapped_column(
        default=uuid4,
        unique=True
    )

    #: The first name
    first_name: Mapped[str]

    #: The last name
    last_name: Mapped[str]

    #: The personnel number
    personnel_number: Mapped[str | None]

    #: The contract number
    contract_number: Mapped[str | None]

    #: Wahlkreis
    district: Mapped[str | None]

    #: The gender value
    gender: Mapped[Gender] = mapped_column(
        Enum(
            *GENDERS.keys(),
            name='pas_gender'
        ),
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
    shipping_method: Mapped[ShippingMethod] = mapped_column(
        Enum(
            *SHIPPING_METHODS.keys(),
            name='pas_shipping_methods'
        ),
        default='a'
    )

    #: The shipping method as translated text
    @property
    def shipping_method_label(self) -> str:
        return SHIPPING_METHODS.get(self.shipping_method, '')

    #: The shipping address
    shipping_address: Mapped[str | None]

    #: The shipping address addition
    shipping_address_addition: Mapped[str | None]

    #: The shipping address zip code
    shipping_address_zip_code: Mapped[str | None]

    #: The shipping address city
    shipping_address_city: Mapped[str | None]

    #: The private address
    private_address: Mapped[str | None]

    #: The private address addition
    private_address_addition: Mapped[str | None]

    #: The private address zip code
    private_address_zip_code: Mapped[str | None]

    #: The private address city
    private_address_city: Mapped[str | None]

    #: The date of birth
    date_of_birth: Mapped[date | None]

    #: The date of death
    date_of_death: Mapped[date | None]

    #: The place of origin
    place_of_origin: Mapped[str | None]

    party: Mapped[str | None]

    #: The occupation
    occupation: Mapped[str | None]

    #: The academic title
    academic_title: Mapped[str | None]

    #: The salutation
    salutation: Mapped[str | None]

    #: The salutation used in the address
    salutation_for_address: Mapped[str | None]

    #: The salutation used for letters
    salutation_for_letter: Mapped[str | None]

    #: How bills should be delivered
    forwarding_of_bills: Mapped[str | None]

    #: The private phone number
    phone_private: Mapped[str | None]

    #: The mobile phone number
    phone_mobile: Mapped[str | None]

    #: The business phone number
    phone_business: Mapped[str | None]

    #: The primary email address
    email_primary: Mapped[str | None]

    #: The secondary email address
    email_secondary: Mapped[str | None]

    #: The website
    website: Mapped[str | None]

    #: The remarks
    remarks: Mapped[str | None]

    #: A picture
    picture = NamedFile()

    #: A parliamentarian may have n roles
    roles: Mapped[list[ParliamentarianRole]] = relationship(
        cascade='all, delete-orphan',
        back_populates='parliamentarian',
        order_by='desc(ParliamentarianRole.start)',
    )

    #: A parliamentarian's interest ties
    interests: dict_property[dict[str, Any]] = content_property(default=dict)

    @hybrid_property
    def active(self) -> bool:
        if not self.roles and not self.commission_memberships:
            return True

        for role in self.roles:
            if role.end is None or role.end >= date.today():
                return True

        for membership in self.commission_memberships:
            if membership.end is None or membership.end >= date.today():
                return True

        return False

    @active.inplace.expression
    @classmethod
    def _active_expression(cls) -> ColumnElement[bool]:
        from onegov.parliament.models import (
            CommissionMembership,
            ParliamentarianRole,
        )

        return or_(
            and_(
                ~exists().where(
                    ParliamentarianRole.parliamentarian_id == cls.id),
                ~exists().where(
                    CommissionMembership.parliamentarian_id == cls.id)
            ),
            exists().where(
                and_(
                    ParliamentarianRole.parliamentarian_id == cls.id,
                    or_(
                        ParliamentarianRole.end.is_(None),
                        ParliamentarianRole.end >= date.today()
                    )
                )
            ),
            exists().where(
                and_(
                    CommissionMembership.parliamentarian_id == cls.id,
                    or_(
                        CommissionMembership.end.is_(None),
                        CommissionMembership.end >= date.today()
                    )
                )
            )
        )

    def active_during(self, start: date, end: date) -> bool:
        if not self.roles:
            return True

        for role in self.roles:
            role_start = role.start if role.start is not None else date.min
            role_end = role.end if role.end is not None else date.max
            if role_end >= start and role_start <= end:
                return True

        for membership in self.commission_memberships:
            membership_start = (
                membership.start) if membership.start is not None else date.min
            membership_end = (
                membership.end) if membership.end is not None else date.max
            if membership_end >= start and membership_start <= end:
                return True

        return False

    #: A parliamentarian may be part of n commissions
    commission_memberships: Mapped[list[CommissionMembership]] = relationship(
        cascade='all, delete-orphan',
        back_populates='parliamentarian',
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
