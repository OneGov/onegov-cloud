from datetime import datetime
from sedate import utcnow
from sqlalchemy import desc, event

from onegov.core.collection import Pagination, GenericCollection
from onegov.fsi.models.course_event import CourseEvent
from onegov.fsi.models.reservation import Reservation


class CourseEventCollection(GenericCollection, Pagination):

    def __init__(
            self, session,
            page=0,
            from_date=None,
            upcoming_only=False,
            past_only=False,
            limit=None,
    ):
        super().__init__(session)
        self.page = page
        # filter newer than from date
        self.from_date = from_date              # ignores upcoming_only
        self.upcoming_only = upcoming_only      # active if from_date not set
        self.past_only = past_only
        self.limit = limit

        if from_date:
            assert isinstance(from_date, datetime)

    @property
    def model_class(self):
        return CourseEvent

    def query(self):
        query = super().query()
        if self.from_date:
            query = query.filter(CourseEvent.start > self.from_date)
        elif self.past_only:
            query = query.filter(CourseEvent.start <= utcnow())
        elif self.upcoming_only:
            query = query.filter(CourseEvent.start >= utcnow())

        query = query.order_by(desc(CourseEvent.start))

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

    def add_placeholder(self, title, course_event):
        assert isinstance(course_event, CourseEvent)
        reservation = Reservation.as_placeholder(
            dummy_desc=title, course_event_id=course_event.id)
        self.session.add(reservation)
        self.session.flush()

    @classmethod
    def latest(cls, session):
        return cls(session, upcoming_only=True, limit=5)

    def next_event(self):
        return self.query().filter(
            self.model_class.start > utcnow()).order_by(
            self.model_class.start
        ).first()
