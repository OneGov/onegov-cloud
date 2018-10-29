from onegov.core.crypto import random_token
from onegov.core.orm.abstract import associated
from onegov.core.orm.mixins import meta_property
from onegov.core.utils import linkify
from onegov.core.utils import normalize_for_url
from onegov.file import File
from onegov.file.utils import as_fileintent
from onegov.people import Agency


class AgencyPdf(File):
    __mapper_args__ = {'polymorphic_identity': 'agency_pdf'}


class ExtendedAgency(Agency):

    __mapper_args__ = {'polymorphic_identity': 'extended'}

    es_type_name = 'extended_agency'

    export_fields = meta_property(default=list)

    state = meta_property()  # todo: `is_visible`?

    pdf = associated(AgencyPdf, 'pdf', 'one-to-one')

    trait = 'agency'

    @property
    def pdf_file(self):
        if self.pdf:
            return self.pdf.reference.file

    @pdf_file.setter
    def pdf_file(self, value):
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
        return '<p>{}</p>'.format(linkify(self.portrait).replace('\n', '<br>'))

    def proxy(self):
        return AgencyProxy(self)


class AgencyProxy(object):
    """ A proxy/alias for an agency.

    The agencies are routed as adjacency lists and the path is fully absorbed
    which prevents to add views such as ``/edit`` to be added directy.

    """

    def __init__(self, agency):
        self.id = agency.id
