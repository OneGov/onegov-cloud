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


class AgencyPdf(File):
    """ A PDF containing all data of an agency and its suborganizations. """

    __mapper_args__ = {'polymorphic_identity': 'agency_pdf'}


class ExtendedAgency(Agency, AccessExtension, PublicationExtension):
    """ An extended version of the standard agency from onegov.people. """

    __mapper_args__ = {'polymorphic_identity': 'extended'}

    es_type_name = 'extended_agency'

    @property
    def es_public(self):
        return self.access == 'public' and self.published

    #: Defines which fields of a membership and person should be exported to
    #: the PDF. The fields are expected to contain two parts seperated by a
    #: point. The first part is either `membership` or `person`, the second
    #: the name of the attribute (e.g. `membership.title`).
    export_fields: dict_property[list[str]] = meta_property(default=list)

    #: The PDF for the agency and all its suborganizations.
    pdf = associated(AgencyPdf, 'pdf', 'one-to-one')

    role_mappings: 'relationship[list[RoleMapping]]' = relationship(
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

    @property
    def pdf_file(self):
        """ Returns the PDF content for the agency (and all its
        suborganizations).

        """

        if self.pdf:
            return self.pdf.reference.file

    @pdf_file.setter
    def pdf_file(self, value):
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
    def portrait_html(self):
        """ Returns the portrait that is saved as HTML from the redactor js
         plugin. """

        return self.portrait

    @property
    def location_address_html(self):
        return get_html_paragraph_with_line_breaks(self.location_address)

    @property
    def postal_address_html(self):
        return get_html_paragraph_with_line_breaks(self.postal_address)

    @property
    def opening_hours_html(self):
        return get_html_paragraph_with_line_breaks(self.opening_hours)

    def proxy(self):
        """ Returns a proxy object to this agency allowing alternative linking
        paths. """

        return AgencyProxy(self)

    def add_person(self, person_id, title, **kwargs):
        """ Appends a person to the agency with the given title. """

        order_within_agency = kwargs.pop('order_within_agency', 2 ** 16)
        session = object_session(self)

        orders_for_person = session.query(
            ExtendedAgencyMembership.order_within_person
        ).filter_by(person_id=person_id)

        orders_for_person = [orders for orders, in orders_for_person]

        if orders_for_person:
            try:
                order_within_person = max(orders_for_person) + 1
            except ValueError:
                order_within_person = 0
        else:
            order_within_person = 0

        membership = ExtendedAgencyMembership(
            person_id=person_id,
            title=title,
            order_within_agency=order_within_agency,
            order_within_person=order_within_person,
            **kwargs
        )
        self.memberships.append(membership)

        for order, membership in enumerate(self.memberships):
            membership.order_within_agency = order

        session.flush()

        return membership

    def deletable(self, request):
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

    def __init__(self, agency):
        self.id = agency.id
