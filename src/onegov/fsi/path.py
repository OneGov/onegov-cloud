from uuid import UUID

from onegov.fsi import FsiApp
from onegov.fsi.collections.attendee import CourseAttendeeCollection
from onegov.fsi.collections.course_event import CourseEventCollection
from onegov.fsi.collections.notification_template import \
    FsiNotificationTemplateCollection
from onegov.fsi.collections.reservation import ReservationCollection
from onegov.fsi.models.course_attendee import CourseAttendee
from onegov.fsi.models.course_event import CourseEvent
from onegov.fsi.models.notification_template import FsiNotificationTemplate
from onegov.fsi.models.reservation import Reservation


@FsiApp.path(model=CourseEvent, path='/fsi/event/{id}')
def get_course_event_details(app, id):
    return CourseEventCollection(app.session()).by_id(id)


@FsiApp.path(model=CourseEventCollection,
             path='/events',
             converters=dict(
                 upcoming_only=bool, past_only=bool, course_id=UUID, limit=int)
             )
def get_events_view(
        app,
        page=0,
        from_date=None,
        upcoming_only=False,
        past_only=False,
        limit=None
):
    return CourseEventCollection(
        app.session(),
        page=page,
        from_date=from_date,
        upcoming_only=upcoming_only,
        past_only=past_only,
        limit=limit
    )


@FsiApp.path(model=CourseAttendeeCollection, path='/fsi/attendees',
             converters=dict(exclude_external=bool, external_only=bool))
def get_attendees(
        request, page=0, exclude_external=False, external_only=False):
    return CourseAttendeeCollection(
        request.session, page,
        exclude_external=exclude_external,
        external_only=external_only
    )


@FsiApp.path(model=CourseAttendee, path='/fsi/attendee/{id}')
def get_attendee_details(request, id):
    # only admins can actually choose a username
    if not request.is_admin:
        id = request.attendee_id
    return CourseAttendeeCollection(request.session).by_id(id)


@FsiApp.path(model=FsiNotificationTemplateCollection, path='/fsi/templates',
             converters=dict(course_event_id=UUID))
def get_notification_templates(request, course_event_id=None):
    return FsiNotificationTemplateCollection(
        request.session, owner_id=request.attendee_id,
        course_event_id=course_event_id
    )


@FsiApp.path(model=FsiNotificationTemplate, path='/fsi/template/{id}')
def get_template_details(request, id):
    return FsiNotificationTemplateCollection(request.session).by_id(id)


@FsiApp.path(model=ReservationCollection, path='/fsi/reservations',
             converters=dict(
                 attendee_id=UUID, course_event_id=UUID, external_only=bool)
             )
def get_reservations(
        app, request,
        course_event_id=None, attendee_id=None, external_only=False):

    if not attendee_id:
        if not request.is_manager:
            # check if someone has permission to see all reservations
            attendee_id = request.attendee_id
        # can be none....still, so not protected, use permissions
    elif attendee_id != request.attendee_id and not request.is_manager:
        attendee_id = request.attendee_id

    return ReservationCollection(
        app.session(),
        attendee_id=attendee_id,
        course_event_id=course_event_id,
        external_only=external_only
    )


@FsiApp.path(model=Reservation, path='/fsi/reservation/{id}')
def get_reservation_details(request, id):
    return ReservationCollection(request.session).by_id(id)
