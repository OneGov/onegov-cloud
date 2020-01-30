from datetime import datetime
from sedate import utcnow
from sqlalchemy import desc

from onegov.core.collection import Pagination, GenericCollection
from onegov.fsi.collections.course import CourseCollection
from onegov.fsi.collections.notification_template import \
    CourseNotificationTemplateCollection
from onegov.fsi.models.course import Course
from onegov.fsi.models.course_event import CourseEvent


class CourseEventCollection(GenericCollection, Pagination):

    def __init__(
            self, session,
            page=0,
            from_date=None,
            upcoming_only=False,
            past_only=False,
            limit=None,
            show_hidden=False,
            course_id=None
    ):
        super().__init__(session)
        self.page = page
        # filter newer than from date
        self.from_date = from_date              # ignores upcoming_only
        self.upcoming_only = upcoming_only      # active if from_date not set
        self.past_only = past_only
        self.limit = limit
        self.show_hidden = show_hidden
        self.course_id = course_id

        if from_date:
            assert isinstance(from_date, datetime)

    @property
    def model_class(self):
        return CourseEvent

    @property
    def course(self):
        if not self.course_id:
            return None
        return CourseCollection(self.session).by_id(self.course_id)

    def query(self):
        query = super().query()
        if not self.show_hidden:
            query = query.filter(CourseEvent.hidden_from_public == False)
        if self.from_date:
            query = query.filter(CourseEvent.start > self.from_date)
        elif self.past_only:
            query = query.filter(CourseEvent.start <= utcnow())
        elif self.upcoming_only:
            query = query.filter(CourseEvent.start >= utcnow())
        if self.course_id:
            query = query.filter(CourseEvent.course_id == self.course_id)

        query = query.order_by(CourseEvent.start)

        if self.limit:
            query = query.limit(self.limit)

        return query

    def subset(self):
        return self.query()

    @property
    def page_index(self):
        return self.page

    def page_by_index(self, index):
        return self.__class__(
            self.session, index,
            from_date=self.from_date,
            upcoming_only=self.upcoming_only,
            past_only=self.past_only,
            limit=self.limit
        )

    @classmethod
    def latest(cls, session, limit=5):
        return cls(session, upcoming_only=True, limit=limit)

    def next_event(self):
        return self.query().filter(
            self.model_class.start > utcnow()).order_by(
            self.model_class.start
        ).first()

    def get_past_reminder_date(self):
        return super().query().filter(
            self.model_class.scheduled_reminder > utcnow())

    def add(self, **kwargs):
        # store the course instead of the course_id, for Elasticsearch to
        # properly work (which needs access to the course)
        course = self.session.query(Course).filter_by(
            id=kwargs['course_id']).one()

        course_event = super().add(course=course, **kwargs)
        tc = CourseNotificationTemplateCollection(
            self.session, course_event_id=course_event.id)
        tc.auto_add_templates_if_not_existing()
        return course_event
