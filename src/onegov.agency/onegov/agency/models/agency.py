from onegov.core.crypto import random_token
from onegov.core.orm.abstract import associated
from onegov.core.orm.mixins import meta_property
from onegov.file import File
from onegov.file.utils import as_fileintent
from onegov.people import Agency


class AgencyPdf(File):
    __mapper_args__ = {'polymorphic_identity': 'agency_pdf'}


class ExtendedAgency(Agency):

    __mapper_args__ = {'polymorphic_identity': 'extended'}

    es_type_name = 'extended_agency'

    export_fields = meta_property()
    state = meta_property()  # todo: `is_visible`?

    pdf = associated(AgencyPdf, 'pdf', 'one-to-one')

    @property
    def pdf_file(self):
        if self.pdf:
            return self.pdf.reference.file

    @pdf_file.setter
    def pdf_file(self, value):
        pdf = AgencyPdf(id=random_token())
        pdf.reference = as_fileintent(value, 'pdf')
        pdf.name = 'pdf'
        self.pdf = pdf
