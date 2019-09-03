from onegov.agency.models import ExtendedAgency
from onegov.people import AgencyCollection


class ExtendedAgencyCollection(AgencyCollection):

    __listclass__ = ExtendedAgency

    # Used to create link for root pdf based on timestamp
    def __init__(self, *args, **kwargs):
        root_pdf_modified = kwargs.pop('root_pdf_modified')
        super(ExtendedAgencyCollection, self).__init__(*args, **kwargs)
        self.root_pdf_modified = root_pdf_modified


