from onegov.core.collection import Pagination
from onegov.election_day.models import Screen


class ScreenCollectionPagination(Pagination):

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


class ScreenCollection(ScreenCollectionPagination):

    def query(self):
        return self.session.query(Screen).order_by(Screen.number)

    def by_id(self, id):
        return self.query().filter(Screen.id == id).first()

    def by_number(self, number):
        return self.query().filter(Screen.number == number).first()

    def add(self, source):
        self.session.add(source)
        self.session.flush()

    def delete(self, source):
        self.session.delete(source)
        self.session.flush()
