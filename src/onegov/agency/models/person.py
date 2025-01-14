from __future__ import annotations

from onegov.agency.utils import get_html_paragraph_with_line_breaks
from onegov.org.models import Organisation
from onegov.org.models.extensions import AccessExtension
from onegov.org.models.extensions import PublicationExtension
from onegov.people import Person
from sqlalchemy.orm import object_session


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from markupsafe import Markup
    from onegov.agency.models import ExtendedAgencyMembership
    from onegov.agency.request import AgencyRequest
    from onegov.core.types import AppenderQuery
    from sqlalchemy.orm import relationship


class ExtendedPerson(Person, AccessExtension, PublicationExtension):
    """ An extended version of the standard person from onegov.people. """

    __mapper_args__ = {'polymorphic_identity': 'extended'}

    es_type_name = 'extended_person'

    @property
    def es_public(self) -> bool:  # type:ignore[override]
        return self.access == 'public' and self.published

    es_properties = {
        'title': {'type': 'text'},
        'function': {'type': 'localized'},
        'email': {'type': 'text'},
        'phone_internal': {'type': 'text'},
        'phone_es': {'type': 'text'}
    }

    @property
    def es_suggestion(self) -> tuple[str, ...]:
        suffix = f' ({self.function})' if self.function else ''
        result = {
            f'{self.last_name} {self.first_name}{suffix}',
            f'{self.first_name} {self.last_name}{suffix}',
            f'{self.phone_internal} {self.last_name} {self.first_name}{suffix}'
        }
        return tuple(result)

    if TYPE_CHECKING:
        # we only allow ExtendedAgencyMembership memberships
        memberships: relationship[  # type:ignore[assignment]
            AppenderQuery[ExtendedAgencyMembership]
        ]

    @property
    def phone_internal(self) -> str:
        org = object_session(self).query(Organisation).one()
        number = getattr(self, org.agency_phone_internal_field)
        digits = org.agency_phone_internal_digits
        return number.replace(' ', '')[-digits:] if number and digits else ''

    @property
    def phone_es(self) -> list[str]:
        result = [self.phone_internal]
        for number in (self.phone, self.phone_direct):
            if number:
                number = number.replace(' ', '')
                result.append(number)
                result.append(number[-7:])
                result.append(number[-9:])
                result.append('0' + number[-9:])
        return [r for r in result if r]

    @property
    def location_address_html(self) -> Markup:
        return get_html_paragraph_with_line_breaks(self.location_address)

    @property
    def postal_address_html(self) -> Markup:
        return get_html_paragraph_with_line_breaks(self.postal_address)

    @property
    def notes_html(self) -> Markup:
        return get_html_paragraph_with_line_breaks(self.notes)

    def deletable(self, request: AgencyRequest) -> bool:
        if request.is_admin:
            return True
        if self.memberships.first():
            return False
        return True
