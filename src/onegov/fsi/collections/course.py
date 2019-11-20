from onegov.core.collection import GenericCollection
from onegov.fsi.models.course import Course


class CourseCollection(GenericCollection):
    def __init__(self, session):
        super().__init__(session)

    @property
    def model_class(self):
        return Course

    def query(self):
        query = super().query()
        return query
