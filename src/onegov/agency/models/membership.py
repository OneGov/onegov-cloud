from sqlalchemy import case, select
from sqlalchemy.ext.hybrid import hybrid_property

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
    from sqlalchemy.sql import ClauseElement


class ExtendedAgencyMembership(AgencyMembership, AccessExtension,
                               PublicationExtension):
    """ An extended version of the standard membership from onegov.people. """

    __mapper_args__ = {'polymorphic_identity': 'extended'}

    es_type_name = 'extended_membership'

    @hybrid_property
    def es_public(self) -> bool:
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

    @es_public.expression  # type:ignore[no-redef]
    def es_public(cls) -> 'ClauseElement':
        from onegov.agency.models import ExtendedAgency, ExtendedPerson

        person_meta = select([ExtendedPerson.meta]).where(
            ExtendedPerson.id == cls.person_id
        ).as_scalar()

        person_published = select([ExtendedPerson.published]).where(
            ExtendedPerson.id == cls.person_id
        ).as_scalar()

        agency_meta = select([ExtendedAgency.meta]).where(
            ExtendedAgency.id == cls.agency_id
        ).as_scalar()

        agency_published = select([ExtendedAgency.published]).where(
            ExtendedAgency.id == cls.agency_id
        ).as_scalar()

        return case(
            [
                (person_meta['access'] != 'public', False),
                (person_published != True, False),
                (agency_meta['access'] != 'public', False),
                (agency_published != True, False),
            ],
            else_=cls.meta['access'] == 'public'
        )

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
