from uuid import UUID
from onegov.fsi import FsiApp
from onegov.fsi.collections.attendee import CourseAttendeeCollection
from onegov.fsi.collections.course_event import CourseEventCollection
from onegov.fsi.collections.notification_template import \
    FsiNotificationTemplateCollection
from onegov.fsi.collections.reservation import ReservationCollection
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
        upcoming_only=None,
        past_only=None,
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


@FsiApp.path(model=CourseAttendeeCollection, path='/attendees')
def get_attendees(app, page=0):
    return CourseAttendeeCollection(app.session(), page)


@FsiApp.path(model=FsiNotificationTemplateCollection, path='/templates')
def get_notification_templates(app, request):
    return FsiNotificationTemplateCollection(
        app.session(), owner_id=request.attendee_id
    )


@FsiApp.path(model=ReservationCollection, path='/reservations')
def get_reservations(app, request):
    return ReservationCollection(
        app.session(), attendee_id=request.attendee_id
    )

