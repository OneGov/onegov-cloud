from sqlalchemy import desc

from onegov.core.collection import Pagination
from onegov.fsi.models.course import Course


class CourseCollection(Pagination):

    def __init__(self, session, page=0, creator_id=None):
        self.session = session
        self.page = page
        self.creator_id = creator_id    # to filter courses of a creator

    def __eq__(self, other):
        return self.page == other.page and self.creator_id == other.creator_id

    def query(self):
        query = self.session.query(Course).order_by(desc(Course.created))
        if self.creator_id:
            query = query.filter_by(user_id=self.creator_id)
        return query

    def subset(self):
        return self.query()

    @property
    def page_index(self):
        return self.page

    def page_by_index(self, index):
        return self.__class__(self.session, index, self.creator_id)
