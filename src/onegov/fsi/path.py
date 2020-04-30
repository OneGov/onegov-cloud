from uuid import UUID

from onegov.fsi import FsiApp
from onegov.fsi.collections.attendee import CourseAttendeeCollection
from onegov.fsi.collections.audit import AuditCollection
from onegov.fsi.collections.course import CourseCollection
from onegov.fsi.collections.course_event import CourseEventCollection, \
    PastCourseEventCollection
from onegov.fsi.collections.notification_template import \
    CourseNotificationTemplateCollection
from onegov.fsi.collections.reservation import ReservationCollection
from onegov.fsi.models.course import Course
from onegov.fsi.models.course_attendee import CourseAttendee
from onegov.fsi.models.course_event import CourseEvent
from onegov.fsi.models.course_notification_template import \
    CourseNotificationTemplate
from onegov.fsi.models.course_reservation import CourseReservation


@FsiApp.path(model=Course, path='/fsi/course/{id}')
def get_course_details(request, id):
    return CourseCollection(request.session).by_id(id)


@FsiApp.path(model=CourseEvent, path='/fsi/event/{id}')
def get_course_event_details(request, id):
    return CourseEventCollection(
        request.session, show_hidden=request.is_manager).by_id(id)


@FsiApp.path(
    model=PastCourseEventCollection,
    path='/fsi/past-events',
    converters=dict(course_id=UUID, show_hidden=bool, sort_desc=bool)
)
def get_past_events_view(
        request,
        page=0,
        show_hidden=True,
        course_id=None,
):
    if not request.is_manager and show_hidden:
        show_hidden = False

    return PastCourseEventCollection(
        request.session,
        page=page,
        show_hidden=show_hidden,
        course_id=course_id,
    )


@FsiApp.path(
    model=CourseEventCollection,
    path='/fsi/events',
    converters=dict(
        upcoming_only=bool, past_only=bool, course_id=UUID, limit=int,
        show_hidden=bool, sort_desc=bool
    )
)
def get_events_view(
        request,
        page=0,
        from_date=None,
        upcoming_only=False,
        past_only=False,
        limit=None,
        show_hidden=True,
        course_id=None,
        sort_desc=False
):
    if not request.is_manager and show_hidden:
        show_hidden = False

    return CourseEventCollection(
        request.session,
        page=page,
        from_date=from_date,
        upcoming_only=upcoming_only,
        past_only=past_only,
        limit=limit,
        show_hidden=show_hidden,
        course_id=course_id,
        sort_desc=sort_desc
    )


@FsiApp.path(model=CourseCollection, path='/fsi/courses',
             converters=dict(show_hidden_from_public=bool))
def get_courses(request, show_hidden_from_public):
    if not request.is_admin:
        show_hidden_from_public = False
    return CourseCollection(
        request.session,
        auth_attendee=request.current_attendee,
        show_hidden_from_public=show_hidden_from_public
    )


@FsiApp.path(model=CourseAttendeeCollection, path='/fsi/attendees',
             converters=dict(
                 exclude_external=bool,
                 external_only=bool,
                 editors_only=bool
             ))
def get_attendees(
        request, page=0, exclude_external=False, external_only=False,
        editors_only=False):
    """This collection has permission private, so no members can see it"""

    return CourseAttendeeCollection(
        request.session, page,
        exclude_external=exclude_external,
        external_only=external_only,
        auth_attendee=request.current_attendee,
        editors_only=editors_only,
    )


@FsiApp.path(model=CourseAttendee, path='/fsi/attendee/{id}')
def get_attendee_details(request, id):
    return CourseAttendeeCollection(request.session).by_id(id)


@FsiApp.path(model=CourseNotificationTemplateCollection, path='/fsi/templates',
             converters=dict(course_event_id=UUID))
def get_notification_templates(request, course_event_id=None):
    return CourseNotificationTemplateCollection(
        request.session, course_event_id=course_event_id)


@FsiApp.path(model=CourseNotificationTemplate, path='/fsi/template/{id}')
def get_template_details(request, id):
    return CourseNotificationTemplateCollection(request.session).by_id(id)


@FsiApp.path(model=ReservationCollection, path='/fsi/reservations',
             converters=dict(
                 attendee_id=UUID, course_event_id=UUID, external_only=bool)
             )
def get_reservations(
        app, request,
        course_event_id=None, attendee_id=None, external_only=False, page=0):

    if not attendee_id:
        if not request.is_manager:
            # check if someone has permission to see all reservations
            attendee_id = request.attendee_id
        # can be none....still, so not protected, use permissions
    elif attendee_id != request.attendee_id and not request.is_manager:
        attendee_id = request.attendee_id

    return ReservationCollection(
        request.session,
        attendee_id=attendee_id,
        course_event_id=course_event_id,
        external_only=external_only,
        auth_attendee=request.current_attendee,
        page=page
    )


@FsiApp.path(model=CourseReservation, path='/fsi/reservation/{id}')
def get_reservation_details(request, id):
    return ReservationCollection(request.session).by_id(id)


@FsiApp.path(model=AuditCollection, path='/fsi/audit',
             converters=dict(course_id=UUID))
def get_audit(request, course_id, organisation):
    return AuditCollection(
        request.session,
        course_id,
        auth_attendee=request.current_attendee,
        organisation=organisation
    )
