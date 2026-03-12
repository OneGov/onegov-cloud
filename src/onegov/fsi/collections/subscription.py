from __future__ import annotations

from sqlalchemy import or_

from onegov.core.collection import GenericCollection, Pagination
from onegov.fsi.collections.attendee import CourseAttendeeCollection
from onegov.fsi.models.course_attendee import CourseAttendee
from onegov.fsi.models.course_event import CourseEvent
from onegov.fsi.models.course_subscription import CourseSubscription


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Query, Session
    from typing import Self
    from uuid import UUID


class SubscriptionsCollection(
    GenericCollection[CourseSubscription],
    Pagination[CourseSubscription]
):

    batch_size = 30

    def __init__(
        self,
        session: Session,
        attendee_id: UUID | None = None,
        course_event_id: UUID | None = None,
        external_only: bool = False,
        auth_attendee: CourseAttendee | None = None,
        page: int = 0
    ) -> None:
        super().__init__(session)
        self.attendee_id = attendee_id
        self.page = page
        # current attendee permissions of auth user
        self.course_event_id = course_event_id
        self.external_only = external_only
        self.auth_attendee = auth_attendee

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, self.__class__)
            and self.page == other.page
            and self.attendee_id == other.attendee_id
            and self.course_event_id == other.course_event_id
            and self.external_only == other.external_only
            and self.auth_attendee == other.auth_attendee
        )

    @property
    def model_class(self) -> type[CourseSubscription]:
        return CourseSubscription

    @property
    def course_event(self) -> CourseEvent | None:
        if self.course_event_id is None:
            return None
        return self.session.query(CourseEvent).filter_by(
            id=self.course_event_id).first()

    @property
    def attendee(self) -> CourseAttendee | None:
        if self.attendee_id is None:
            return None
        return self.session.query(CourseAttendee).filter_by(
            id=self.attendee_id).first()

    @property
    def attendee_collection(self) -> CourseAttendeeCollection:
        return CourseAttendeeCollection(
            self.session, external_only=self.external_only,
            auth_attendee=self.auth_attendee
        )

    @property
    def for_himself(self) -> bool:
        if not self.auth_attendee:
            return False
        return str(self.auth_attendee.id) == str(self.attendee_id)

    def query(self) -> Query[CourseSubscription]:
        query = super().query()
        if self.auth_attendee and self.auth_attendee.role == 'editor':
            query = query.join(CourseAttendee)
            query = query.filter(
                or_(CourseAttendee.organisation.in_(
                    self.auth_attendee.permissions or [], ),
                    CourseSubscription.attendee_id == self.auth_attendee.id)
            )
        if self.attendee_id:
            # Always set in path for members to their own
            query = query.filter(
                CourseSubscription.attendee_id == self.attendee_id)
        if self.course_event_id:
            query = query.filter(
                CourseSubscription.course_event_id == self.course_event_id)
        return query

    def by_id(
        self,
        id: UUID  # type:ignore[override]
    ) -> CourseSubscription | None:
        return super().query().filter(self.primary_key == id).first()

    def subset(self) -> Query[CourseSubscription]:
        return self.query()

    @property
    def page_index(self) -> int:
        return self.page

    def page_by_index(self, index: int) -> Self:
        return self.__class__(
            self.session, page=index,
            auth_attendee=self.auth_attendee,
            attendee_id=self.attendee_id,
            course_event_id=self.course_event_id,
            external_only=self.external_only
        )
