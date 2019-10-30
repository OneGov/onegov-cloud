from sqlalchemy import desc

from onegov.core.collection import Pagination
from onegov.fsi.models.course import Course


class CourseCollection(Pagination):

    def __init__(self, session, page=0, creator=None):
        self.session = session
        self.page = page
        self.creator = creator      # to filter courses of a creator

    def __eq__(self, other):
        return self.page == other.page and self.creator == other.creator

    def query(self):
        query = self.session.query(Course).order_by(desc(Course.created))
        if self.creator:
            query = query.filter_by(user_id=self.creator.id)
        return query

    def subset(self):
        return self.query()

    @property
    def page_index(self):
        return self.page

    def page_by_index(self, index):
        return self.__class__(self.session, index, self.creator)
