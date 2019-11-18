from onegov.core.collection import GenericCollection, Pagination
from onegov.fsi.models.course import Course


class CourseCollection(GenericCollection, Pagination):
    def __init__(self, session, page=0):
        super().__init__(session)
        self.page = page

    @property
    def model_class(self):
        return Course

    def subset(self):
        return self.query()

    @property
    def page_index(self):
        return self.page

    def page_by_index(self, index):
        return self.__class__(self.session, index)
