from cached_property import cached_property
from sedate import utcnow
from sqlalchemy import func, desc

from onegov.core.collection import GenericCollection, Pagination
from onegov.fsi.models import CourseAttendee, CourseSubscription, \
    CourseEvent, Course


class AuditCollection(GenericCollection, Pagination):
    """
    Displays the list of attendees filtered by a course and organisation
    for evauluation if they subscribed and completed a course event.

    The organisation filter should also be exact and not fuzzy.

    """

    batch_size = 20

    def __init__(self, session, course_id, auth_attendee, organisations=None,
                 letter=None, page=0):
        super().__init__(session)
        self.page = page

        # When using the class link, the option with a course is still
        self.course_id = course_id if course_id \
            else self.relevant_courses and self.relevant_courses[0].id

        self.auth_attendee = auth_attendee

        # e.g. SD / STVA or nothing in case of editor
        self.organisations = organisations or []
        self.letter = letter.upper() if letter else None

    def subset(self):
        return self.query()

    @property
    def page_index(self):
        return self.page

    def page_by_index(self, index):
        return self.__class__(
            self.session,
            page=index,
            course_id=self.course_id,
            auth_attendee=self.auth_attendee,
            organisations=self.organisations,
            letter=self.letter
        )

    def by_letter_and_orgs(self, letter=None, orgs=None):
        return self.__class__(
            self.session,
            page=0,
            course_id=self.course_id,
            auth_attendee=self.auth_attendee,
            organisations=orgs if orgs is not None else self.organisations,
            letter=letter or self.letter
        )

    def by_letter(self, letter):
        return self.__class__(
            self.session,
            page=0,
            course_id=self.course_id,
            auth_attendee=self.auth_attendee,
            organisations=self.organisations,
            letter=letter
        )

    def __eq__(self, other):
        return all((
            self.page == other.page,
            self.course_id == other.course_id,
            self.auth_attendee == other.auth_attendee,
            self.organisations == other.organisations,
            self.letter == other.letter
        ))

    def ranked_subscription_query(self, past_only=True):
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
            CourseSubscription.attendee_id != None
        )
        if past_only:
            ranked = ranked.filter(CourseEvent.start < utcnow())
        return ranked

    def last_subscriptions(self):
        """Retrieve the last completed subscription by attemdee for
        a given the course_id.
        """
        ranked = self.ranked_subscription_query().subquery('ranked')
        subquery = self.session.query(
            CourseSubscription.attendee_id,
            ranked.c.start,
            ranked.c.end,
            ranked.c.name,
            ranked.c.event_completed,
            ranked.c.refresh_interval,
        ).select_entity_from(ranked)
        return subquery.filter(ranked.c.rownum == 1)

    def filter_attendees_by_role(self, query):
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

    def query(self):
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
        return self.course_id and self.session.query(Course).filter_by(
            id=self.course_id).first() or None

    @cached_property
    def used_letters(self):
        """ Returns a list of all the distinct first letters of the peoples
        last names.

        """
        letter = func.left(CourseAttendee.last_name, 1)
        letter = func.upper(func.unaccent(letter))
        query = self.session.query(letter.distinct().label('letter'))
        query = query.order_by(letter)
        return [r.letter for r in query if r.letter]

    @cached_property
    def relevant_courses(self):
        return tuple(self.session.query(Course.id, Course.name).filter(
            Course.hidden_from_public == False,
            Course.mandatory_refresh != None
        ))
