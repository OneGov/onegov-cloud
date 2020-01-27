from onegov.core.collection import GenericCollection
from onegov.fsi.models.course import Course


class CourseCollection(GenericCollection):
    def __init__(self, session, auth_attendee=None):
        super().__init__(session)
        self.auth_attendee = auth_attendee

    @property
    def model_class(self):
        return Course

    def query(self):
        query = super().query()
        query = query.filter_by(hidden_from_public=False)
        return query.order_by(Course.name)

    def by_id(self, id):
        return super().query().filter(self.primary_key == id).first()
