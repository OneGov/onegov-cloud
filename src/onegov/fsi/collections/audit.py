from cached_property import cached_property
from sqlalchemy import func, desc

from onegov.core.collection import GenericCollection
from onegov.fsi.models import CourseAttendee, CourseReservation, CourseEvent, \
    Course


class AuditCollection(GenericCollection):
    """
    Displays the list of attendees filtered by a course and organisation
    for evauluation if they subscribed and completed a course event.

    The organisation filter should also be exact and not fuzzy.

    """

    def __init__(self, session, course_id, auth_attendee, organisation=None):
        super().__init__(session)
        self.course_id = course_id
        self.auth_attendee = auth_attendee

        # e.g. SD / STVA or nothing in case of editor
        self.organisation = organisation

    def ranked_subscription_query(self):
        """
        Ranks all subscriptions of all events of a course
        windowed over the attendee_id and ranked after completed, most recent
        Use this query for make a join with any collection of attendees.
        """
        ranked = self.session.query(
            CourseReservation.attendee_id,
            CourseReservation.event_completed,
            CourseEvent.start,
            CourseEvent.end,
            func.row_number().over(
                partition_by=CourseAttendee.id,
                order_by=[
                    desc(CourseReservation.event_completed),
                    CourseEvent.start]
            ).label('rownum'),
        )
        ranked = ranked.join(CourseEvent).join(CourseAttendee)
        ranked = ranked.filter(CourseEvent.course_id == self.course_id)
        return ranked.filter(CourseReservation.attendee_id != None)

    def last_completed_subscriptions_query(self):
        """Filter the ranked subscriptions by the rownum resulting
        in a list of just the most recent and completed subscriptions
        for every attendee_id
        """
        ranked = self.ranked_subscription_query().subquery('ranked')
        subquery = self.session.query(
            CourseReservation.attendee_id,
            ranked.c.start,
            ranked.c.end,
            ranked.c.event_completed
        ).select_entity_from(ranked)
        return subquery.filter(ranked.c.rownum == 1)

    def query(self):
        last = self.last_completed_subscriptions_query().subquery()
        query = self.session.query(
            CourseAttendee.id,
            CourseAttendee.first_name,
            CourseAttendee.last_name,
            CourseAttendee.organisation,
            last.c.start.label('start'),
            last.c.end.label('end'),
            last.c.event_completed
        )
        if self.auth_attendee.role != 'editor':
            assert self.organisation
            query = query.filter_by(organisation=self.organisation)
        else:
            query = query.filter(CourseAttendee.organisation.in_(
                self.auth_attendee.permissions,
            ))

        query = query.join(
            last, CourseAttendee.id == last.c.attendee_id, isouter=True)
        query = query.order_by(
            CourseAttendee.last_name,
            CourseAttendee.first_name,
        )
        return query

    @property
    def model_class(self):
        return CourseAttendee

    @cached_property
    def course(self):
        return self.session.query(Course).filter_by(id=self.course_id).first()
