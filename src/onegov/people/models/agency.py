from __future__ import annotations

from onegov.core.crypto import random_token
from onegov.core.orm.abstract import AdjacencyList
from onegov.core.orm.abstract import associated
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.mixins import UTCPublicationMixin
from onegov.core.orm.types import MarkupText
from onegov.core.utils import normalize_for_url
from onegov.file import File
from onegov.file.utils import as_fileintent
from onegov.file.utils import content_type_from_fileobj
from onegov.file.utils import extension_for_content_type
from onegov.gis import CoordinatesMixin
from onegov.people.models.membership import AgencyMembership
from onegov.search import ORMSearchable
from decimal import Decimal
from sqlalchemy import func
from sqlalchemy import Column
from sqlalchemy import Text
from sqlalchemy.orm import object_session
from sqlalchemy.orm import relationship
from translationstring import TranslationString


from typing import Any
from typing import IO
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from _typeshed import SupportsRichComparison
    from collections.abc import Callable
    from collections.abc import Iterator
    from depot.io.interfaces import StoredFile
    from markupsafe import Markup
    from onegov.core.types import AppenderQuery
    from typing import TypeAlias
    from uuid import UUID

    AgencySortKey: TypeAlias = Callable[['Agency'], SupportsRichComparison]
    AgencyMembershipSortKey: TypeAlias = Callable[
        [AgencyMembership],
        SupportsRichComparison
    ]


class AgencyOrganigram(File):
    __mapper_args__ = {'polymorphic_identity': 'agency_organigram'}


class Agency(AdjacencyList, ContentMixin, TimestampMixin, ORMSearchable,
             UTCPublicationMixin, CoordinatesMixin):
    """ An agency (organization) containing people through memberships. """

    __tablename__ = 'agencies'

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

    # HACK: We don't want to set up translations in this module for this single
    #       string, we know we already have a translation in a different domain
    #       so we just manually specify it for now.
    fts_type_title = TranslationString('Agencies', domain='onegov.agency')
    fts_public = True
    fts_properties = {
        'title': {'type': 'text', 'weight': 'A'},
        'description': {'type': 'localized', 'weight': 'B'},
        'portrait': {'type': 'localized', 'weight': 'B'},
    }

    # NOTE: When an agency was last changed should not influence how
    #       relevant it is in the search results
    @property
    def fts_last_change(self) -> None:
        return None

    #: a short description of the agency
    description: Column[str | None] = Column(Text, nullable=True)

    #: describes the agency
    portrait: Column[Markup | None] = Column(MarkupText, nullable=True)

    #: location address (street name and number) of agency
    location_address: Column[str | None] = Column(Text, nullable=True)

    #: location code and city of agency
    location_code_city: Column[str | None] = Column(Text, nullable=True)

    #: postal address (street name and number) of agency
    postal_address: Column[str | None] = Column(Text, nullable=True)

    #: postal code and city of agency
    postal_code_city: Column[str | None] = Column(Text, nullable=True)

    #: the phone number of agency
    phone: Column[str | None] = Column(Text, nullable=True)

    #: the direct phone number of agency
    phone_direct: Column[str | None] = Column(Text, nullable=True)

    #: the email of agency
    email: Column[str | None] = Column(Text, nullable=True)

    #: the website related to agency
    website: Column[str | None] = Column(Text, nullable=True)

    #: opening hours of agency
    opening_hours: Column[str | None] = Column(Text, nullable=True)

    #: a reference to the organization chart
    organigram = associated(AgencyOrganigram, 'organigram', 'one-to-one')

    memberships: relationship[AppenderQuery[AgencyMembership]]
    memberships = relationship(
        AgencyMembership,
        back_populates='agency',
        cascade='all, delete-orphan',
        lazy='dynamic',
        order_by='AgencyMembership.order_within_agency'
    )

    if TYPE_CHECKING:
        # override the attributes from AdjacencyList
        parent: relationship[Agency | None]
        children: relationship[list[Agency]]

        @property
        def root(self) -> Agency: ...
        @property
        def ancestors(self) -> Iterator[Agency]: ...

    @property
    def organigram_file(self) -> StoredFile | None:
        """ Returns the file-like content of the organigram. """

        try:
            return self.organigram.reference.file if self.organigram else None
        except (OSError, Exception):
            return None

    # FIXME: asymmetric property
    @organigram_file.setter
    def organigram_file(self, value: IO[bytes]) -> None:
        """ Sets the organigram, expects a file-like value. """

        assert value is not None
        filename = 'organigram-{}.{}'.format(
            normalize_for_url(self.title),
            extension_for_content_type(content_type_from_fileobj(value))
        )
        if self.organigram:
            self.organigram.reference = as_fileintent(value, filename)
            self.organigram.name = filename
        else:
            organigram = AgencyOrganigram(id=random_token())
            organigram.reference = as_fileintent(value, filename)
            organigram.name = filename
            self.organigram = organigram

    def add_person(
        self,
        person_id: UUID,
        title: str,
        *,
        order_within_agency: int = 2 ** 16,
        # FIXME: Specify the arguments supported by AgencyMembership
        **kwargs: Any
    ) -> AgencyMembership:
        """ Appends a person to the agency with the given title. """

        session = object_session(self)

        order_within_person = session.query(
            func.coalesce(func.max(AgencyMembership.order_within_person), -1)
        ).filter_by(person_id=person_id).scalar() + 1

        next_order_within_agency = session.query(
            func.coalesce(func.max(AgencyMembership.order_within_agency), -1)
        ).filter_by(agency_id=self.id).scalar() + 1

        if order_within_agency > next_order_within_agency:
            # just use the next available number
            order_within_agency = next_order_within_agency
        else:
            # move everyone after the desired position up by one
            for membership in self.memberships:
                if membership.order_within_agency >= order_within_agency:
                    membership.order_within_agency += 1

        membership = AgencyMembership(
            person_id=person_id,
            title=title,
            order_within_agency=order_within_agency,
            order_within_person=order_within_person,
            **kwargs
        )
        self.memberships.append(membership)

        session.flush()

        return membership

    def sort_children(
        self,
        sortkey: AgencySortKey | None = None
    ) -> None:
        """ Sorts the suborganizations.

        Sorts by the agency title by default.
        """
        if sortkey is None:
            def sortkey(agency: Agency) -> str:
                return normalize_for_url(agency.title)

        children = sorted(self.children, key=sortkey)
        for order, child in enumerate(children):
            child.order = Decimal(order)

    def sort_relationships(
        self,
        sortkey: AgencyMembershipSortKey | None = None
    ) -> None:
        """ Sorts the relationships.

        Sorts by last name, first name.by default.
        """

        if sortkey is None:
            def sortkey(membership: AgencyMembership) -> str:
                return normalize_for_url(membership.person.title)

        memberships = sorted(self.memberships, key=sortkey)
        for order, membership in enumerate(memberships):
            membership.order_within_agency = order
