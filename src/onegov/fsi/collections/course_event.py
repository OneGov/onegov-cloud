from __future__ import annotations

from datetime import datetime
from sedate import utcnow
from sqlalchemy import desc

from onegov.core.collection import Pagination, GenericCollection
from onegov.fsi.collections.course import CourseCollection
from onegov.fsi.collections.notification_template import (
    CourseNotificationTemplateCollection)
from onegov.fsi.models.course import Course
from onegov.fsi.models.course_event import CourseEvent


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Query, Session
    from typing import Self
    from uuid import UUID


class CourseEventCollection(
    GenericCollection[CourseEvent],
    Pagination[CourseEvent]
):

    batch_size = 10

    def __init__(
        self,
        session: Session,
        page: int = 0,
        from_date: datetime | None = None,
        upcoming_only: bool = False,
        past_only: bool = False,
        limit: int | None = None,
        show_hidden: bool = False,
        show_locked: bool = True,
        course_id: UUID | None = None,
        sort_desc: bool = False
    ) -> None:

        super().__init__(session)
        self.page = page
        # filter newer than from date
        self.from_date = from_date              # ignores upcoming_only
        self.upcoming_only = upcoming_only      # active if from_date not set
        self.past_only = past_only
        self.limit = limit
        self.show_hidden = show_hidden
        self.show_locked = show_locked
        self.course_id = course_id
        self.sort_desc = sort_desc

        if from_date:
            assert isinstance(from_date, datetime)

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, self.__class__)
            and self.page == other.page
            and self.from_date == other.from_date
            and self.upcoming_only == other.upcoming_only
            and self.past_only == other.past_only
            and self.limit == other.limit
            and self.show_hidden == other.show_hidden
            and self.course_id == other.course_id
            and self.sort_desc == other.sort_desc
        )

    @property
    def model_class(self) -> type[CourseEvent]:
        return CourseEvent

    @property
    def course(self) -> Course | None:
        if not self.course_id:
            return None
        return CourseCollection(self.session).by_id(self.course_id)

    def query(self) -> Query[CourseEvent]:
        query = super().query()
        if not self.show_hidden:
            query = query.filter(CourseEvent.hidden_from_public == False)
            query = query.join(Course)
            query = query.filter(Course.hidden_from_public == False)
        if not self.show_locked:
            query = query.filter(CourseEvent.locked_for_subscriptions == False)
        if self.from_date:
            query = query.filter(CourseEvent.start > self.from_date)
        elif self.past_only:
            query = query.filter(CourseEvent.start <= utcnow())
        elif self.upcoming_only:
            query = query.filter(CourseEvent.start >= utcnow())
        if self.course_id:
            query = query.filter(CourseEvent.course_id == self.course_id)

        ordering = CourseEvent.start
        query = query.order_by(desc(ordering) if self.sort_desc else ordering)

        if self.limit:
            query = query.limit(self.limit)

        return query

    def subset(self) -> Query[CourseEvent]:
        return self.query()

    @property
    def page_index(self) -> int:
        return self.page

    def page_by_index(self, index: int) -> Self:
        return self.__class__(
            self.session,
            page=index,
            from_date=self.from_date,
            upcoming_only=self.upcoming_only,
            past_only=self.past_only,
            limit=self.limit,
            show_hidden=self.show_hidden,
            show_locked=self.show_locked,
            course_id=self.course_id,
            sort_desc=self.sort_desc
        )

    @classmethod
    def latest(cls, session: Session, limit: int = 5) -> Self:
        return cls(session, upcoming_only=True, limit=limit)

    def next_event(self) -> Query[CourseEvent]:
        return self.query().filter(
            self.model_class.start > utcnow()).order_by(None).order_by(
            self.model_class.start)

    def get_past_reminder_date(self) -> Query[CourseEvent]:
        return super().query().filter(
            self.model_class.scheduled_reminder > utcnow())

    def add(self, **kwargs: Any) -> CourseEvent:
        # store the course instead of the course_id, for Elasticsearch to
        # properly work (which needs access to the course)
        course = self.session.query(Course).filter_by(
            id=kwargs['course_id']).one()

        course_event = super().add(course=course, **kwargs)
        tc = CourseNotificationTemplateCollection(
            self.session, course_event_id=course_event.id)
        tc.auto_add_templates_if_not_existing()
        return course_event


class PastCourseEventCollection(CourseEventCollection):
    """This is used for past events to do the audit """

    def __init__(
        self,
        session: Session,
        page: int = 0,
        show_hidden: bool = False,
        show_locked: bool = True,
        course_id: UUID | None = None
    ) -> None:
        super().__init__(
            session,
            page=page,
            past_only=True,
            show_hidden=show_hidden,
            show_locked=show_locked,
            course_id=course_id,
            sort_desc=True
        )

    def page_by_index(self, index: int) -> Self:
        return self.__class__(
            self.session,
            page=index,
            show_hidden=self.show_hidden,
            show_locked=self.show_locked,
            course_id=self.course_id,
        )

    def query(self) -> Query[CourseEvent]:
        return super().query().filter(self.model_class.status == 'confirmed')
