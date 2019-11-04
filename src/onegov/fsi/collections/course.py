from sqlalchemy import desc

from onegov.core.collection import Pagination, SearcheableCollection
from onegov.fsi.models.course import Course


class CourseCollection(SearcheableCollection, Pagination):

    """
    Inherits from GenericCollection - SearchableCollection and add
    pagination mixing which does not inherit from any class.

    Only the GenericCollection defines __init__ method.

    """

    def __init__(
            self, session, page=0, creator_id=None, term=None, locale=None):
        super().__init__(session)
        self.session = session
        self.page = page
        self.creator_id = creator_id    # to filter courses of a creator
        self.term = term
        self.locale = locale

    def __eq__(self, other):
        return (self.page == other.page
                and self.creator_id == other.creator_id
                and self.term == other.term
                and self.locale == other.local)

    @property
    def model_class(self):
        return Course

    @property
    def term_filter_cols(self):
        return 'name', 'presenter_name', 'description'

    def query(self):
        query = super().query()
        if self.creator_id:
            query = query.filter_by(user_id=self.creator_id)
        return query.order_by(desc(Course.created))

    def subset(self):
        return self.query()

    @property
    def page_index(self):
        return self.page

    def page_by_index(self, index):
        return self.__class__(
            self.session,
            index,
            creator_id=self.creator_id,
            term=self.term,
            locale=self.locale
        )
