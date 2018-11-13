from onegov.agency.models.membership import ExtendedAgencyMembership
from onegov.core.crypto import random_token
from onegov.core.orm.abstract import associated
from onegov.core.orm.mixins import meta_property
from onegov.core.utils import linkify
from onegov.core.utils import normalize_for_url
from onegov.file import File
from onegov.file.utils import as_fileintent
from onegov.org.models.extensions import HiddenFromPublicExtension
from onegov.people import Agency


class AgencyPdf(File):
    """ A PDF containing all data of an agency and its suborganizations. """

    __mapper_args__ = {'polymorphic_identity': 'agency_pdf'}


class ExtendedAgency(Agency, HiddenFromPublicExtension):
    """ An extended version of the standard agency from onegov.people. """

    __mapper_args__ = {'polymorphic_identity': 'extended'}

    es_type_name = 'extended_agency'

    @property
    def es_public(self):
        return not self.is_hidden_from_public

    #: Defines which fields of a membership and person should be exported to
    #: the PDF. The fields are expected to contain two parts seperated by a
    #: point. The first part is either `membership` or `person`, the second
    #: the name of the attribute (e.g. `membership.title`).
    export_fields = meta_property(default=list)

    #: The PDF for the agency and all its suborganizations.
    pdf = associated(AgencyPdf, 'pdf', 'one-to-one')

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
        if self.pdf:
            self.pdf.reference = as_fileintent(value, filename)
            self.pdf.name = filename
        else:
            pdf = AgencyPdf(id=random_token())
            pdf.reference = as_fileintent(value, filename)
            pdf.name = filename
            self.pdf = pdf

    @property
    def portrait_html(self):
        """ Returns the portrait as HTML. """

        return '<p>{}</p>'.format(linkify(self.portrait).replace('\n', '<br>'))

    def proxy(self):
        """ Returns a proxy object to this agency allowing alternative linking
        paths. """

        return AgencyProxy(self)

    def add_person(self, person_id, title, **kwargs):
        """ Appends a person to the agency with the given title. """

        order = kwargs.pop('order', 2 ** 16)

        self.memberships.append(
            ExtendedAgencyMembership(
                person_id=person_id,
                title=title,
                order=order,
                **kwargs
            )
        )

        for order, membership in enumerate(self.memberships):
            membership.order = order


class AgencyProxy(object):
    """ A proxy/alias for an agency.

    The agencies are routed as adjacency lists and the path is fully absorbed
    which prevents to add views such as ``/edit`` to be added directy.

    """

    def __init__(self, agency):
        self.id = agency.id
