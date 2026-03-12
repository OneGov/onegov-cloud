from __future__ import annotations

from onegov.agency.observer import observes
from onegov.core.orm.mixins import dict_property
from onegov.core.orm.mixins import meta_property
from onegov.org.models.extensions import AccessExtension
from onegov.org.models.extensions import PublicationExtension
from onegov.org.utils import narrowest_access
from onegov.people import AgencyMembership
from sqlalchemy.orm import object_session
from sqlalchemy.orm import Mapped
from sqlalchemy.orm.attributes import set_committed_value


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from datetime import datetime
    from onegov.agency.models import ExtendedAgency
    from onegov.agency.models import ExtendedPerson


class ExtendedAgencyMembership(AgencyMembership, AccessExtension,
                               PublicationExtension):
    """ An extended version of the standard membership from onegov.people. """

    __mapper_args__ = {'polymorphic_identity': 'extended'}

    fts_public = True

    @property
    def fts_access(self) -> str:
        self._fetch_if_necessary()
        return narrowest_access(
            self.access,
            self.agency.meta.get('access', 'public'),
            self.person.meta.get('access', 'public'),
        )

    @property
    def fts_publication_start(self) -> datetime | None:
        self._fetch_if_necessary()
        return max((dt for dt in (
            self.publication_start,
            self.agency.publication_start,
            self.person.publication_start
        ) if dt is not None), default=None)

    @property
    def fts_publication_end(self) -> datetime | None:
        self._fetch_if_necessary()
        return min((dt for dt in (
            self.publication_end,
            self.agency.publication_end,
            self.person.publication_end
        ) if dt is not None), default=None)

    def _fetch_if_necessary(self) -> None:
        session = object_session(self)
        if session is None:
            return

        if self.person_id is not None and self.person is None:
            # retrieve the person
            from onegov.agency.models import ExtendedPerson  # type: ignore[unreachable]
            set_committed_value(
                self,
                'person',
                session.get(ExtendedPerson, self.person_id)
            )
        if self.agency_id is not None and self.agency is None:
            # retrieve the agency
            from onegov.agency.models import ExtendedAgency  # type: ignore[unreachable]
            set_committed_value(
                self,
                'agency',
                session.get(ExtendedAgency, self.agency_id)
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
        # NOTE: We only relate to extended versions
        agency: Mapped[ExtendedAgency]
        person: Mapped[ExtendedPerson]

    # force fts update when access/published of agency/person changes
    @observes(
        'agency.meta',
        'agency.publication_start',
        'agency.publication_end',
        'person.meta',
        'person.publication_start',
        'person.publication_end',
    )
    def _force_fts_update(self, *_ignored: object) -> None:
        self.modified = self.modified
