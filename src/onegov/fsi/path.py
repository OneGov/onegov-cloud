from uuid import UUID

from onegov.core.security import Private
from onegov.fsi import FsiApp
from onegov.fsi.collections.attendee import CourseAttendeeCollection
from onegov.fsi.collections.course_event import CourseEventCollection
from onegov.fsi.collections.notification_template import \
    FsiNotificationTemplateCollection
from onegov.fsi.collections.reservation import ReservationCollection
from onegov.fsi.layouts.course_attendee import CourseAttendeeLayout
from onegov.fsi.models.course_attendee import CourseAttendee
from onegov.fsi.models.course_event import CourseEvent
from onegov.fsi.models.notification_template import FsiNotificationTemplate


@FsiApp.path(model=CourseEvent, path='/event/{id}')
def get_course_details(app, id):
    return CourseEventCollection(app.session()).by_id(id)


@FsiApp.path(
    model=FsiNotificationTemplate,
    path='/template/{id}')
def get_course_details(app, id):
    return FsiNotificationTemplateCollection(app.session()).by_id(id)


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


@FsiApp.path(model=CourseAttendeeCollection, path='/attendees',
             converters=dict(exclude_external=bool))
def get_attendees(app, page=0, exclude_external=False):
    return CourseAttendeeCollection(app.session(), page, exclude_external)


@FsiApp.path(model=CourseAttendee, path='/attendee/{id}')
def get_attendees(app, request, id):
    # only admins can actually specify the username
    if not request.is_admin:
        id = request.attendee_id
    return CourseAttendeeCollection(app.session()).by_id(id)


@FsiApp.path(model=FsiNotificationTemplateCollection, path='/templates')
def get_notification_templates(app, request):
    return FsiNotificationTemplateCollection(
        app.session(), owner_id=request.attendee_id
    )


@FsiApp.path(model=ReservationCollection,
             path='/reservations',
             converters=dict(attendee_id=UUID, course_event_id=UUID)
             )
def get_reservations(app, request, course_event_id=None, attendee_id=None):

    if not attendee_id and not request.is_manager:
        # check if someone has permission to see all reservations
        attendee_id = request.attendee_id
        # can be none....still, so not protected, use permissions

    return ReservationCollection(
        app.session(),
        attendee_id=attendee_id,
        course_event_id=course_event_id
    )

