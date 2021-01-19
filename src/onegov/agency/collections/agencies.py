from onegov.agency.models import ExtendedAgency
from onegov.people import AgencyCollection


class ExtendedAgencyCollection(AgencyCollection):

    __listclass__ = ExtendedAgency

    # Used to create link for root pdf based on timestamp
    def __init__(self, session, root_pdf_modified=None, browse=None):
        super(ExtendedAgencyCollection, self).__init__(session)
        self.root_pdf_modified = root_pdf_modified
        self.browse = browse
