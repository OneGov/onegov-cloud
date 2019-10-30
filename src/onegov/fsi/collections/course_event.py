from datetime import datetime
from uuid import uuid4

from sqlalchemy import desc

from onegov.core.collection import Pagination
from onegov.fsi.models.course_attendee import CourseAttendee
from onegov.fsi.models.course_event import CourseEvent
from onegov.fsi.models.reservation import Reservation


class CourseEventCollection(Pagination):

    def __init__(
            self, session,
            page=0,
            creator=None,
            course_id=None,
            from_date=None,
            upcoming_only=True,
            past_only=False
         ):
        self.session = session
        self.page = page
        self.creator = creator      # to filter courses events of a creator
        self.course_id = course_id

        # filter newer than from date
        self.from_date = from_date              # ignores upcoming_only
        self.upcoming_only = upcoming_only      # active if from_date not set
        self.past_only = past_only

    def __eq__(self, other):
        return (self.page == other.page
                and self.creator == other.creator
                and self.course_id == other.course_id
                and self.from_date == other.from_date
                and self.upcoming_only == other.upcoming_only
                and self.past_only == other.past_only
                )

    def query(self):
        query = self.session.query(CourseEvent).order_by(
            desc(CourseEvent.created))
        if self.creator:
            query = query.filter_by(user_id=self.creator.id)
        if self.course_id:
            query = query.filter_by(course_id=self.course_id)
        if self.from_date:
            query = query.filter(CourseEvent.start > self.from_date)
        elif self.past_only:
            query = query.filter(CourseEvent.start <= datetime.today())
        elif self.upcoming_only:
            query = query.filter(CourseEvent.start >= datetime.today())
        return query

    def subset(self):
        return self.query()

    @property
    def page_index(self):
        return self.page

    def page_by_index(self, index):
        return self.__class__(
            self.session, index,
            creator=self.creator,
            course_id=self.course_id,
            from_date=self.from_date,
            upcoming_only=self.upcoming_only,
            past_only=self.past_only,
        )

    def add_placeholder(self, title, course_event):
        assert isinstance(course_event, CourseEvent)
        placeholder = CourseAttendee.as_placeholder(
            dummy_desc=title, id=uuid4())
        self.session.add(placeholder)
        self.session.add(
            Reservation(
                attendee_id=placeholder.id,
                course_event_id=course_event.id))
        self.session.flush()
