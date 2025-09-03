from __future__ import annotations

from onegov.agency.models.membership import ExtendedAgencyMembership
from onegov.agency.utils import get_html_paragraph_with_line_breaks
from onegov.core.crypto import random_token
from onegov.core.orm.abstract import associated
from onegov.core.orm.mixins import dict_property
from onegov.core.orm.mixins import meta_property
from onegov.core.utils import normalize_for_url
from onegov.file import File
from onegov.file.utils import as_fileintent
from onegov.org.models.extensions import AccessExtension
from onegov.org.models.extensions import PublicationExtension
from onegov.people import Agency
from onegov.user import RoleMapping
from sqlalchemy.orm import object_session
from sqlalchemy.orm import relationship


from typing import Any
from typing import IO
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from depot.io.interfaces import StoredFile
    from markupsafe import Markup
    from onegov.agency.request import AgencyRequest
    from onegov.core.types import AppenderQuery
    from uuid import UUID


class AgencyPdf(File):
    """ A PDF containing all data of an agency and its suborganizations. """

    __mapper_args__ = {'polymorphic_identity': 'agency_pdf'}


class ExtendedAgency(Agency, AccessExtension, PublicationExtension):
    """ An extended version of the standard agency from onegov.people. """

    __mapper_args__ = {'polymorphic_identity': 'extended'}

    es_type_name = 'extended_agency'

    @property
    def es_public(self) -> bool:  # type:ignore[override]
        return self.access == 'public' and self.published

    #: Defines which fields of a membership and person should be exported to
    #: the PDF. The fields are expected to contain two parts seperated by a
    #: point. The first part is either `membership` or `person`, the second
    #: the name of the attribute (e.g. `membership.title`).
    export_fields: dict_property[list[str]] = meta_property(default=list)

    #: IDs used for audm synchronisation
    #: Use organization path as unique identifier since AUDM lacks external IDs
    #: This is the name of all parent organisations joined
    organisation_path: dict_property[str | None] = meta_property()

    #: The PDF for the agency and all its suborganizations.
    pdf = associated(AgencyPdf, 'pdf', 'one-to-one')

    role_mappings: relationship[list[RoleMapping]] = relationship(
        RoleMapping,
        primaryjoin=(
            "and_("
            "foreign(RoleMapping.content_id) == cast(ExtendedAgency.id, TEXT),"
            "RoleMapping.content_type == 'agencies'"
            ")"
        ),
        backref='agency',
        sync_backref=False,
        viewonly=True,
        lazy='dynamic'
    )  # type:ignore[call-arg]

    trait = 'agency'

    if TYPE_CHECKING:
        # we only allow relating to other ExtendedAgency
        parent: relationship[ExtendedAgency | None]
        children: relationship[list[ExtendedAgency]]  # type:ignore

        @property
        def root(self) -> ExtendedAgency: ...
        @property
        def ancestors(self) -> Iterator[ExtendedAgency]: ...
        # we only allow ExtendedAgencyMembership memberships
        memberships: relationship[  # type:ignore[assignment]
            AppenderQuery[ExtendedAgencyMembership]
        ]

    @property
    def pdf_file(self) -> StoredFile | None:
        """ Returns the PDF content for the agency (and all its
        suborganizations).

        """

        try:
            return self.pdf.reference.file if self.pdf else None
        except (OSError, Exception):
            return None

    # FIXME: asymmetric property
    @pdf_file.setter
    def pdf_file(self, value: IO[bytes] | bytes) -> None:
        """ Sets the PDF content for the agency (and all its
        suborganizations). Automatically sets a nice filename. Replaces only
        the reference, if possible.

        """

        filename = '{}.pdf'.format(normalize_for_url(self.title))
        pdf = AgencyPdf(id=random_token())
        pdf.reference = as_fileintent(value, filename)
        pdf.name = filename
        self.pdf = pdf

    @property
    def portrait_html(self) -> Markup | None:
        """ Returns the portrait that is saved as HTML from the redactor js
        plugin. """

        return self.portrait

    @property
    def location_address_html(self) -> Markup:
        return get_html_paragraph_with_line_breaks(self.location_address)

    @property
    def postal_address_html(self) -> Markup:
        return get_html_paragraph_with_line_breaks(self.postal_address)

    @property
    def opening_hours_html(self) -> Markup:
        return get_html_paragraph_with_line_breaks(self.opening_hours)

    def proxy(self) -> AgencyProxy:
        """ Returns a proxy object to this agency allowing alternative linking
        paths. """

        return AgencyProxy(self)

    def add_person(  # type:ignore[override]
        self,
        person_id: UUID,
        title: str,
        *,
        order_within_agency: int = 2 ** 16,
        **kwargs: Any
    ) -> ExtendedAgencyMembership:
        """ Appends a person to the agency with the given title. """

        session = object_session(self)
        orders_for_person = session.query(
            ExtendedAgencyMembership.order_within_person
        ).filter_by(person_id=person_id)

        order_within_person = max(
            (order for order, in orders_for_person),
            # if this person has no memberships yet, then we start at 0
            default=-1
        ) + 1

        membership = ExtendedAgencyMembership(
            person_id=person_id,
            title=title,
            order_within_agency=order_within_agency,
            order_within_person=order_within_person,
            **kwargs
        )
        self.memberships.append(membership)

        # re-order all memberships cannot be done here, because the order
        # within the agency is not yet set. do be done once all memberships
        # are added to the agency.
        # for order, _membership in enumerate(self.memberships):
        #     _membership.order_within_agency = order

        session.flush()

        return membership

    def deletable(self, request: AgencyRequest) -> bool:
        if request.is_admin:
            return True
        if self.memberships.first() or self.children:
            return False
        return True


class AgencyProxy:
    """ A proxy/alias for an agency.

    The agencies are routed as adjacency lists and the path is fully absorbed
    which prevents to add views such as ``/edit`` to be added directy.

    """

    def __init__(self, agency: Agency) -> None:
        self.id = agency.id
