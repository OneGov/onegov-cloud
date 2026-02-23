from __future__ import annotations

from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.mixins import UTCPublicationMixin
from onegov.core.orm.mixins import content_property
from onegov.core.orm.mixins import dict_property
from onegov.core.utils import generate_fts_phonenumbers
from onegov.people.models import AgencyMembership
from onegov.search import ORMSearchable
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import relationship
from sqlalchemy.orm import DynamicMapped
from sqlalchemy.orm import Mapped
from translationstring import TranslationString
from uuid import uuid4, UUID
from vobject import vCard
from vobject.vcard import Address
from vobject.vcard import Name

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Collection
    from vobject.base import Component


class Person(Base, ContentMixin, TimestampMixin, ORMSearchable,
             UTCPublicationMixin):
    """ A person. """

    __tablename__ = 'people'

    #: the type of the item, this can be used to create custom polymorphic
    #: subclasses of this class. See
    #: `<https://docs.sqlalchemy.org/en/improve_toc/\
    #: orm/extensions/declarative/inheritance.html>`_.
    type: Mapped[str] = mapped_column(default=lambda: 'generic')

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'generic',
    }

    # HACK: We don't want to set up translations in this module for this single
    #       string, we know we already have a translation in a different domain
    #       so we just manually specify it for now.
    fts_type_title = TranslationString('People', domain='onegov.org')
    fts_public = True
    fts_title_property = 'title'
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

    @property
    def organisation_texts(self) -> list[str]:
        parts = []
        if self.organisations_multiple:
            it = iter(self.organisations_multiple)
            for item in it:
                parts.append(f'{item} - {next(it).lstrip("-")}')
            return parts

        if self.organisation and self.sub_organisation:
            parts.append(f'{self.organisation} - {self.sub_organisation}')
        elif self.organisation:
            parts.append(self.organisation)
        elif self.sub_organisation:
            parts.append(self.sub_organisation)
        return parts

    #: the unique id, part of the url
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4
    )

    #: the salutation used for the person
    salutation: Mapped[str | None]

    #: the academic title of the person
    academic_title: Mapped[str | None]

    #: the first name of the person
    first_name: Mapped[str]

    #: the last name of the person
    last_name: Mapped[str]

    #: when the person was born
    born: Mapped[str | None]

    #: the profession of the person
    profession: Mapped[str | None]

    #: the function of the person
    function: Mapped[str | None]

    #: an organisation the person belongs to
    organisation: Mapped[str | None]

    #: multiple organisations the person belongs to
    organisations_multiple: dict_property[list[str] | None] = content_property(
    )

    # a sub organisation the person belongs to
    sub_organisation: Mapped[str | None]

    #: the political party the person belongs to
    political_party: Mapped[str | None]

    #: the parliamentary group the person belongs to
    parliamentary_group: Mapped[str | None]

    #: an URL leading to a picture of the person
    picture_url: Mapped[str | None]

    #: the email of the person
    email: Mapped[str | None]

    #: the phone number of the person
    phone: Mapped[str | None]

    #: the direct phone number of the person
    phone_direct: Mapped[str | None]

    #: the website related to the person
    website: Mapped[str | None]

    #: a second website related to the person
    website_2: Mapped[str | None]

    # agency does not use 'address' anymore. Instead, the 4 following items
    # are being used. The 'address' field is still used in org, town6,
    # volunteers and others
    #: the address of the person
    address: Mapped[str | None]

    #: the location address (street name and number) of the person
    location_address: Mapped[str | None]

    #: postal code of location and city of the person
    location_code_city: Mapped[str | None]

    #: the postal address (street name and number) of the person
    postal_address: Mapped[str | None]

    #: postal code and city of the person
    postal_code_city: Mapped[str | None]

    #: some remarks about the person
    notes: Mapped[str | None]

    memberships: DynamicMapped[AgencyMembership] = relationship(
        back_populates='person',
        cascade='all, delete-orphan',
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
