from onegov.agency.models import ExtendedAgency
from onegov.core.collection import GenericCollection, Pagination
from onegov.people import AgencyCollection


class ExtendedAgencyCollection(AgencyCollection):

    __listclass__ = ExtendedAgency

    # Used to create link for root pdf based on timestamp
    def __init__(self, session, root_pdf_modified=None, browse=None):
        super(ExtendedAgencyCollection, self).__init__(session)
        self.root_pdf_modified = root_pdf_modified
        self.browse = browse


class PaginatedAgencyCollection(GenericCollection, Pagination):

    def __init__(self, session, page=0):
        super().__init__(session)
        self.page = page

    @property
    def model_class(self):
        return ExtendedAgency

    def __eq__(self, other):
        return other.page == self.page

    def subset(self):
        return self.query()

    @property
    def page_index(self):
        return self.page

    def page_by_index(self, index):
        return self.__class__(self.session, page=index)
