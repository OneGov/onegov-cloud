from onegov.core.collection import Pagination
from onegov.election_day.models import DataSource
from onegov.election_day.models import DataSourceItem


class DataSourceCollectionPagination(Pagination):

    def __init__(self, session, page=0):
        self.session = session
        self.page = page

    def __eq__(self, other):
        return self.page == other.page

    def subset(self):
        return self.query()

    @property
    def page_index(self):
        return self.page

    def page_by_index(self, index):
        return self.__class__(self.session, index)


class DataSourceCollection(DataSourceCollectionPagination):

    def query(self):
        return self.session.query(DataSource).order_by(DataSource.name)

    def by_id(self, id):
        return self.query().filter(DataSource.id == id).first()

    def add(self, source):
        self.session.add(source)
        self.session.flush()

    def delete(self, source):
        self.session.delete(source)
        self.session.flush()


class DataSourceItemCollectionPagination(Pagination):

    def __init__(self, session, id=None, page=0):
        self.session = session
        self.id = id
        self.page = page

    def __eq__(self, other):
        return self.page == other.page

    def subset(self):
        return self.query()

    @property
    def page_index(self):
        return self.page

    def page_by_index(self, index):
        return self.__class__(self.session, self.id, index)


class DataSourceItemCollection(DataSourceItemCollectionPagination):

    def query(self):
        query = self.session.query(DataSourceItem)
        query = query.filter(DataSourceItem.source_id == self.id)
        query = query.order_by(DataSourceItem.district, DataSourceItem.number)
        return query

    def by_id(self, id):
        query = self.session.query(DataSourceItem)
        query = query.filter(DataSourceItem.id == id)
        return query.first()

    @property
    def source(self):
        query = self.session.query(DataSource)
        query = query.filter(DataSource.id == self.id)
        return query.first()

    def add(self, item):
        item.source_id = self.id
        self.session.add(item)
        self.session.flush()

    def delete(self, item):
        self.session.delete(item)
        self.session.flush()
