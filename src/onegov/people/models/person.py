from __future__ import annotations

from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.mixins import UTCPublicationMixin
from onegov.core.orm.mixins import content_property
from onegov.core.orm.types import UUID
from onegov.core.utils import generate_fts_phonenumbers
from onegov.people.models import AgencyMembership
from onegov.search import ORMSearchable
from sqlalchemy import Column
from sqlalchemy import Text
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import relationship
from uuid import uuid4
from vobject import vCard
from vobject.vcard import Address
from vobject.vcard import Name


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from collections.abc import Collection
    from onegov.core.orm.mixins.content import dict_property
    from onegov.core.types import AppenderQuery
    from vobject.base import Component


class Person(Base, ContentMixin, TimestampMixin, ORMSearchable,
             UTCPublicationMixin):
    """ A person. """

    __tablename__ = 'people'

    #: the type of the item, this can be used to create custom polymorphic
    #: subclasses of this class. See
    #: `<https://docs.sqlalchemy.org/en/improve_toc/\
    #: orm/extensions/declarative/inheritance.html>`_.
    type: Column[str] = Column(
        Text,
        nullable=False,
        default=lambda: 'generic'
    )

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'generic',
    }

    fts_public = True
    fts_properties = {
        'title': {'type': 'text', 'weight': 'A'},
        'function': {'type': 'localized', 'weight': 'B'},
        'email': {'type': 'text', 'weight': 'A'},
        'phone_fts': {'type': 'text', 'weight': 'A'},
    }

    @property
    def fts_suggestion(self) -> tuple[str, ...]:
        return (self.title, f'{self.first_name} {self.last_name}')

    # NOTE: When a person was last changed should not influence how
    #       relevant they are in the search results
    @property
    def fts_last_change(self) -> None:
        return None

    @property
    def phone_fts(self) -> list[str]:
        numbers = (self.phone, self.phone_direct)
        return generate_fts_phonenumbers(numbers)

    @property
    def title(self) -> str:
        """ Returns the Eastern-ordered name. """
        return f'{self.last_name} {self.first_name}'

    @property
    def spoken_title(self) -> str:
        """ Returns the Western-ordered name. Includes the academic title if
        available.

        """
        parts = []
        if self.academic_title:
            parts.append(self.academic_title)
        parts.append(self.first_name)
        parts.append(self.last_name)

        return ' '.join(parts)

    #: the unique id, part of the url
    id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: the salutation used for the person
    salutation: Column[str | None] = Column(Text, nullable=True)

    #: the academic title of the person
    academic_title: Column[str | None] = Column(Text, nullable=True)

    #: the first name of the person
    first_name: Column[str] = Column(Text, nullable=False)

    #: the last name of the person
    last_name: Column[str] = Column(Text, nullable=False)

    #: when the person was born
    born: Column[str | None] = Column(Text, nullable=True)

    #: the profession of the person
    profession: Column[str | None] = Column(Text, nullable=True)

    #: the function of the person
    function: Column[str | None] = Column(Text, nullable=True)

    #: an organisation the person belongs to
    organisation: Column[str | None] = Column(Text, nullable=True)

    #: multiple organisations the person belongs to
    organisations_multiple: dict_property[list[str] | None] = content_property(
    )

    # a sub organisation the person belongs to
    sub_organisation: Column[str | None] = Column(Text, nullable=True)

    #: the political party the person belongs to
    political_party: Column[str | None] = Column(Text, nullable=True)

    #: the parliamentary group the person belongs to
    parliamentary_group: Column[str | None] = Column(Text, nullable=True)

    #: an URL leading to a picture of the person
    picture_url: Column[str | None] = Column(Text, nullable=True)

    #: the email of the person
    email: Column[str | None] = Column(Text, nullable=True)

    #: the phone number of the person
    phone: Column[str | None] = Column(Text, nullable=True)

    #: the direct phone number of the person
    phone_direct: Column[str | None] = Column(Text, nullable=True)

    #: the website related to the person
    website: Column[str | None] = Column(Text, nullable=True)

    #: a second website related to the person
    website_2: Column[str | None] = Column(Text, nullable=True)

    # agency does not use 'address' anymore. Instead, the 4 following items
    # are being used. The 'address' field is still used in org, town6,
    # volunteers and others
    #: the address of the person
    address: Column[str | None] = Column(Text, nullable=True)

    #: the location address (street name and number) of the person
    location_address: Column[str | None] = Column(Text, nullable=True)

    #: postal code of location and city of the person
    location_code_city: Column[str | None] = Column(Text, nullable=True)

    #: the postal address (street name and number) of the person
    postal_address: Column[str | None] = Column(Text, nullable=True)

    #: postal code and city of the person
    postal_code_city: Column[str | None] = Column(Text, nullable=True)

    #: some remarks about the person
    notes: Column[str | None] = Column(Text, nullable=True)

    memberships: relationship[AppenderQuery[AgencyMembership]]
    memberships = relationship(
        AgencyMembership,
        back_populates='person',
        cascade='all, delete-orphan',
        lazy='dynamic',
    )

    def vcard_object(
        self,
        exclude: Collection[str] | None = None,
        include_memberships: bool = True
    ) -> Component:
        """ Returns the person as vCard (3.0) object.

        Allows to specify the included attributes, provides a reasonable
        default if none are specified. Always includes the first and last
        name.

        """

        def split_code_from_city(code_city: str) -> tuple[str, str]:
            """
            Splits a postal code and city into two parts. Supported are
            formats like '1234 City Name' and '12345 City Name'.

            """
            import re

            match = re.match(r'(\d{4,5})\s+(.*)', code_city)
            if match:
                code, city = match.groups()
            else:
                # assume no code is present
                code, city = '', code_city
            return code, city

        exclude = exclude or ['notes']
        result = vCard()

        prefix = ''
        if 'academic_title' not in exclude and self.academic_title:
            prefix = self.academic_title

        # mandatory fields
        line = result.add('n')
        line.value = Name(
            prefix=prefix,
            given=self.first_name,
            family=self.last_name,
        )
        line.charset_param = 'utf-8'

        line = result.add('fn')
        line.value = f'{prefix} {self.first_name} {self.last_name}'.strip()
        line.charset_param = 'utf-8'

        # optional fields
        if 'function' not in exclude and self.function:
            line = result.add('title')
            line.value = self.function
            line.charset_param = 'utf-8'

        if 'picture_url' not in exclude and self.picture_url:
            line = result.add('photo')
            line.value = self.picture_url

        if 'email' not in exclude and self.email:
            line = result.add('email')
            line.value = self.email

        if 'phone' not in exclude and self.phone:
            line = result.add('tel;type=work')
            line.value = self.phone

        if 'phone_direct' not in exclude and self.phone_direct:
            line = result.add('tel;type=work;type=pref')
            line.value = self.phone_direct

        if 'organisation' not in exclude and self.organisation:
            line = result.add('org')
            line.value = [
                '; '.join(
                    o for o in (self.organisation, self.sub_organisation) if o
                )
            ]
            line.charset_param = 'utf-8'

        if 'website' not in exclude and self.website:
            line = result.add('url')
            line.value = self.website

        if (
            'postal_address' not in exclude and self.postal_address
            and 'postal_code_city' not in exclude and self.postal_code_city
        ):
            line = result.add('adr')
            code, city = split_code_from_city(self.postal_code_city)
            line.value = Address(street=self.postal_address,
                                 code=code, city=city)
            line.charset_param = 'utf-8'

        if (
            'location_address' not in exclude and self.location_address
            and 'location_code_city' not in exclude and self.location_code_city
        ):
            line = result.add('adr')
            code, city = split_code_from_city(self.location_code_city)
            line.value = Address(street=self.location_address,
                                 code=code, city=city)
            line.charset_param = 'utf-8'

        if 'notes' not in exclude and self.notes:
            line = result.add('note')
            line.value = self.notes
            line.charset_param = 'utf-8'

        if include_memberships and (memberships := [
            f'{m.agency.title}, {m.title}' for m in self.memberships.options(
                # eagerly load the agency along with the membership
                joinedload(AgencyMembership.agency)
            )
        ]):
            line = result.add('org')
            line.value = ['; '.join(memberships)]
            line.charset_param = 'utf-8'

        return result

    def vcard(self, exclude: Collection[str] | None = None) -> str:
        """ Returns the person as vCard (3.0).

        Allows to specify the included attributes, provides a reasonable
        default if none are specified. Always includes the first and last
        name.

        """

        return self.vcard_object(exclude).serialize()

    @property
    def memberships_by_agency(self) -> list[AgencyMembership]:
        """ Returns the memberships sorted alphabetically by the agency. """

        def sortkey(membership: AgencyMembership) -> int:
            return membership.order_within_person

        return sorted(self.memberships, key=sortkey)
