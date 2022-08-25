from onegov.agency.models import ExtendedAgency
from onegov.core.collection import GenericCollection, Pagination
from onegov.people import AgencyCollection
from sqlalchemy import or_


class ExtendedAgencyCollection(AgencyCollection):

    __listclass__ = ExtendedAgency

    # Used to create link for root pdf based on timestamp
    def __init__(self, session, root_pdf_modified=None, browse=None):
        super(ExtendedAgencyCollection, self).__init__(session)
        self.root_pdf_modified = root_pdf_modified
        self.browse = browse


class PaginatedAgencyCollection(GenericCollection, Pagination):

    def __init__(self, session, page=0, parent=None, exclude_hidden=True):
        super().__init__(session)
        self.page = page
        self.parent = parent
        self.exclude_hidden = exclude_hidden

    @property
    def model_class(self):
        return ExtendedAgency

    def __eq__(self, other):
        return (
            other.page == self.page
            and other.parent == self.parent
        )

    def subset(self):
        return self.query()

    @property
    def page_index(self):
        return self.page

    def page_by_index(self, index):
        return self.__class__(self.session, page=index)

    def query(self):
        query = super().query()

        if self.exclude_hidden:
            query = query.filter(
                or_(
                    ExtendedAgency.meta['access'] == 'public',
                    ExtendedAgency.meta['access'] == None,
                ),
                ExtendedAgency.published.is_(True)
            )

        if self.parent:
            query = query.filter(ExtendedAgency.parent_id == self.parent)

        return query
