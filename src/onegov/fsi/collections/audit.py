from __future__ import annotations

from functools import cached_property
from sedate import utcnow
from sqlalchemy import func, desc

from onegov.core.collection import GenericCollection, Pagination
from onegov.fsi.models import (
    CourseAttendee, CourseSubscription, CourseEvent, Course)


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from datetime import datetime
    from onegov.fsi.request import FsiRequest
    from sqlalchemy.orm import Query, Session
    from typing import NamedTuple, TypeVar
    from typing import Self
    from uuid import UUID

    T = TypeVar('T')

    class RankedSubscriptionRow(NamedTuple):
        attendee_id: UUID
        event_completed: bool
        name: str
        refresh_interval: int | None
        course_id: UUID
        start: datetime
        end: datetime
        rownum: int

    class LastSubscriptionRow(NamedTuple):
        attendee_id: UUID
        start: datetime
        end: datetime
        name: str
        event_completed: bool
        refresh_interval: int | None

    class AuditRow(NamedTuple):
        id: UUID
        first_name: str | None
        last_name: str | None
        organisation: str | None
        source_id: str | None
        start: datetime | None
        end: datetime | None
        event_completed: bool | None
        refresh_interval: int | None
        name: str | None


# FIXME: It's not quite kosher that we use a non-model row, so there
#        may be some methods with incorrect types
class AuditCollection(
    GenericCollection['AuditRow'],  # type:ignore[type-var]
    Pagination['AuditRow']  # type:ignore[type-var]
):
    """
    Displays the list of attendees filtered by a course and organisation
    for evaluation if they subscribed and completed a course event.

    The organisation filter should also be exact and not fuzzy.

    """

    batch_size = 20

    def __init__(
        self,
        session: Session,
        course_id: UUID | None,
        auth_attendee: CourseAttendee,
        organisations: list[str] | None = None,
        letter: str | None = None,
        page: int = 0,
        exclude_inactive: bool = True
    ) -> None:
        super().__init__(session)
        self.page = page

        # When using the class link, the option with a course is still
        self.course_id = course_id if course_id else (
            self.relevant_courses[0][0] if self.relevant_courses else None)

        self.auth_attendee = auth_attendee

        # e.g. SD / STVA or nothing in case of editor
        self.organisations = organisations or []
        self.letter = letter.upper() if letter else None
        self.exclude_inactive = exclude_inactive

    def subset(self) -> Query[AuditRow]:
        return self.query()

    @property
    def page_index(self) -> int:
        return self.page

    def page_by_index(self, index: int) -> Self:
        return self.__class__(
            self.session,
            page=index,
            course_id=self.course_id,
            auth_attendee=self.auth_attendee,
            organisations=self.organisations,
            letter=self.letter,
            exclude_inactive=self.exclude_inactive
        )

    def by_letter_and_orgs(
        self,
        letter: str | None = None,
        orgs: list[str] | None = None
    ) -> Self:
        return self.__class__(
            self.session,
            page=0,
            course_id=self.course_id,
            auth_attendee=self.auth_attendee,
            organisations=orgs if orgs is not None else self.organisations,
            letter=letter or self.letter,
            exclude_inactive=self.exclude_inactive
        )

    def by_letter(self, letter: str | None) -> Self:
        return self.__class__(
            self.session,
            page=0,
            course_id=self.course_id,
            auth_attendee=self.auth_attendee,
            organisations=self.organisations,
            exclude_inactive=self.exclude_inactive,
            letter=letter,
        )

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, self.__class__)
            and self.page == other.page
            and self.course_id == other.course_id
            and self.auth_attendee == other.auth_attendee
            and self.organisations == other.organisations
            and self.exclude_inactive == other.exclude_inactive
            and self.letter == other.letter
        )

    def ranked_subscription_query(
        self,
        past_only: bool = True
    ) -> Query[RankedSubscriptionRow]:
        """
        Ranks all subscriptions of all events of a course
        windowed over the attendee_id and ranked after completed, most recent
        Use this query to make a join with any collection of attendees.
        """
        ranked = self.session.query(
            CourseSubscription.attendee_id,
            CourseSubscription.event_completed,
            Course.name,
            Course.refresh_interval,
            CourseEvent.course_id,
            CourseEvent.start,
            CourseEvent.end,
            func.row_number().over(
                partition_by=CourseSubscription.attendee_id,
                order_by=[
                    desc(CourseSubscription.event_completed),
                    desc(CourseEvent.start)]
            ).label('rownum'),
        )
        ranked = ranked.join(
            CourseEvent, CourseEvent.id == CourseSubscription.course_event_id)
        ranked = ranked.join(
            Course, Course.id == CourseEvent.course_id)
        ranked = ranked.filter(
            CourseEvent.course_id == self.course_id,
            CourseSubscription.attendee_id.isnot(None)
        )
        if past_only:
            ranked = ranked.filter(CourseEvent.start < utcnow())
        return ranked

    def last_subscriptions(self) -> Query[LastSubscriptionRow]:
        """Retrieve the last completed subscription by attemdee for
        a given the course_id.
        """
        ranked = self.ranked_subscription_query().subquery('ranked')
        subquery = self.session.query(
            ranked.c.attendee_id,
            ranked.c.start,
            ranked.c.end,
            ranked.c.name,
            ranked.c.event_completed,
            ranked.c.refresh_interval,
        )
        return subquery.filter(ranked.c.rownum == 1)

    def filter_attendees_by_role(self, query: Query[T]) -> Query[T]:
        """Filter permissions of editor, exclude external, """
        if self.auth_attendee.role == 'admin':
            if not self.organisations:
                return query
            return query.filter(
                CourseAttendee.organisation.in_(self.organisations)
            )
        else:
            editors_permissions = self.auth_attendee.permissions or []
            return query.filter(
                CourseAttendee.organisation.in_(tuple(
                    p for p in editors_permissions
                    if p in self.organisations
                ) if self.organisations else editors_permissions)
            )

    def query(self) -> Query[AuditRow]:
        last = self.last_subscriptions().subquery()
        query = self.session.query(
            CourseAttendee.id,
            CourseAttendee.first_name,
            CourseAttendee.last_name,
            CourseAttendee.organisation,
            CourseAttendee.source_id,
            last.c.start.label('start'),
            last.c.end.label('end'),
            last.c.event_completed,
            last.c.refresh_interval,
            last.c.name
        )
        if self.letter:
            query = query.filter(
                func.upper(
                    func.unaccent(CourseAttendee.last_name)
                ).startswith(self.letter)
            )
        query = self.filter_attendees_by_role(query)
        if self.exclude_inactive:
            query = query.filter(CourseAttendee.active == True)
        query = query.join(
            last, CourseAttendee.id == last.c.attendee_id, isouter=True)
        query = query.order_by(
            CourseAttendee.last_name,
            CourseAttendee.first_name,
        )
        return query

    def next_subscriptions(
        self,
        request: FsiRequest
    ) -> dict[UUID, tuple[str, datetime]]:
        next_subscriptions: dict[UUID, tuple[str, datetime]] = {}
        if self.course_id:
            # FIXME: We can do this in a single query, this is N+1...
            query = request.session.query(CourseEvent)
            query = query.filter(CourseEvent.course_id == self.course_id)
            query = query.filter(CourseEvent.start >= utcnow())
            query = query.order_by(CourseEvent.start)
            for event in query:
                attendees = event.attendees.with_entities(CourseAttendee.id)
                for attendee in attendees:
                    next_subscriptions.setdefault(
                        attendee[0],
                        (request.link(event), event.start)
                    )
        return next_subscriptions

    @property
    def model_class(self) -> type[CourseAttendee]:  # type:ignore[override]
        return CourseAttendee

    @cached_property
    def course(self) -> Course | None:
        return self.session.query(Course).filter_by(
            id=self.course_id).first() if self.course_id else None

    @cached_property
    def used_letters(self) -> list[str]:
        """ Returns a list of all the distinct first letters of the peoples
        last names.

        """
        letter = func.left(CourseAttendee.last_name, 1)
        letter = func.upper(func.unaccent(letter))
        query = self.session.query(letter.distinct().label('letter'))
        query = query.order_by(letter)
        return [r.letter for r in query if r.letter]

    @cached_property
    def relevant_courses(self) -> tuple[tuple[UUID, str], ...]:
        return tuple(self.session.query(Course.id, Course.name).filter(
            Course.hidden_from_public == False,
            Course.mandatory_refresh != None
        ).tuples())
