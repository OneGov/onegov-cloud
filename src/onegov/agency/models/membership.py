from __future__ import annotations

from onegov.core.orm.mixins import dict_property
from onegov.core.orm.mixins import meta_property
from onegov.org.models.extensions import AccessExtension
from onegov.org.models.extensions import PublicationExtension
from onegov.people import AgencyMembership


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.agency.models import ExtendedAgency
    from onegov.agency.models import ExtendedPerson
    from sqlalchemy.orm import relationship


class ExtendedAgencyMembership(AgencyMembership, AccessExtension,
                               PublicationExtension):
    """ An extended version of the standard membership from onegov.people. """

    __mapper_args__ = {'polymorphic_identity': 'extended'}

    es_type_name = 'extended_membership'

    @property
    def es_public(self) -> bool:  # type:ignore[override]
        if self.agency:
            if self.agency.meta.get('access', 'public') != 'public':
                return False
            if not self.agency.published:
                return False

        if self.person:
            if self.person.meta.get('access', 'public') != 'public':
                return False
            if not self.person.published:
                return False

        return self.access == 'public'

    # Todo: It is very unclear how this should be used. In the PDF rendering,
    # it is placed a middle column with 0.5 cm after the title.
    # On the agency, it is placed after the membership title, so not a prefix
    # but rather a suffix and it looks. For 0.5cm, the form should validate the
    # length of this, otherwise people complain about weird pdf
    #: The prefix character.
    prefix: dict_property[str | None] = meta_property()

    #: A note to the membership.
    note: dict_property[str | None] = meta_property()

    #: An addition to the membership.
    addition: dict_property[str | None] = meta_property()

    if TYPE_CHECKING:
        # NOTE: We only relate extended versions
        agency: relationship[ExtendedAgency]
        person: relationship[ExtendedPerson]
