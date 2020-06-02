from onegov.core.collection import GenericCollection
from onegov.fsi.models.course import Course


class CourseCollection(GenericCollection):
    def __init__(
            self,
            session,
            auth_attendee=None,
            show_hidden_from_public=False,
    ):
        super().__init__(session)
        self.auth_attendee = auth_attendee
        self.show_hidden_from_public = show_hidden_from_public

    @property
    def model_class(self):
        return Course

    def query(self, with_events=False):
        query = super().query()
        if not self.show_hidden_from_public:
            query = query.filter_by(hidden_from_public=False)
        if with_events:
            query = query.join(Course.events)
        return query.order_by(Course.name)

    def by_id(self, id):
        return super().query().filter(self.primary_key == id).first()
