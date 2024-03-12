from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.pas import _
from onegov.search import ORMSearchable
from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import Enum
from sqlalchemy import Text
from uuid import uuid4


GENDERS = {
    'male': _('male'),
    'female': _('female'),
}


SHIPPING_METHODS = {
    'a': _('A Mail'),
    'plus': _('A Mail Plus'),
    'registered': _('Registered'),
    'confidential': _('Confidential'),
    'personal': _('Personal / Confidential')
}


class Parliamentarian(Base, ContentMixin, TimestampMixin, ORMSearchable):

    __tablename__ = 'pas_parliamentarians'

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
    id = Column(UUID, primary_key=True, default=uuid4)

    #: The first name
    first_name = Column(Text, nullable=False)

    #: The last name
    last_name = Column(Text, nullable=False)

    #: The personnel number
    personnel_number = Column(Text, nullable=True)

    #: The contract number
    contract_number = Column(Text, nullable=True)

    #: The gender
    gender = Column(
        Enum(*GENDERS, name='pas_gender'),
        nullable=False,
        default='male'
    )

    #: An URL leading to a picture of the person
    picture_url = Column(Text, nullable=True)

    #: The shipping method
    shipping_method = Column(
        Enum(*SHIPPING_METHODS, name='pas_shipping_methods'),
        nullable=False,
        default='a'
    )

    #: The shipping address
    shipping_address = Column(Text, nullable=True)

    #: The shipping address addition
    shipping_address_addition = Column(Text, nullable=True)

    #: The shipping address zip code
    shipping_address_zip_code = Column(Text, nullable=True)

    #: The shipping address city
    shipping_address_city = Column(Text, nullable=True)

    #: The private address
    private_address = Column(Text, nullable=True)

    #: The private address addition
    private_address_addition = Column(Text, nullable=True)

    #: The private address zip code
    private_address_zip_code = Column(Text, nullable=True)

    #: The private address city
    private_address_city = Column(Text, nullable=True)

    #: The date of birth
    date_of_birth = Column(Date, nullable=True)

    #: The date of death
    date_of_death = Column(Date, nullable=True)

    #: The place of origin
    place_of_origin = Column(Text, nullable=True)

    #: The occupation
    occupation = Column(Text, nullable=True)

    #: The academic title
    academic_title = Column(Text, nullable=True)

    #: The salutation
    salutation = Column(Text, nullable=True)

    #: The salutation used in the address
    salutation_for_address = Column(Text, nullable=True)

    #: The salutation used for letters
    salutation_for_letter = Column(Text, nullable=True)

    #: How bills should be delivered
    forwarding_of_bills = Column(Text, nullable=True)

    #: The private phone number
    phone_private = Column(Text, nullable=True)

    #: The mobile phone number
    phone_mobile = Column(Text, nullable=True)

    #: The business phone number
    phone_business = Column(Text, nullable=True)

    #: The primary email address
    email_primary = Column(Text, nullable=True)

    #: The secondary email address
    email_secondary = Column(Text, nullable=True)

    #: The website
    website = Column(Text, nullable=True)

    #: The remarks
    remarks = Column(Text, nullable=True)
