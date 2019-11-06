from uuid import UUID
from onegov.fsi import FsiApp
from onegov.fsi.collections.attendee import CourseAttendeeCollection
from onegov.fsi.collections.course import CourseCollection
from onegov.fsi.collections.course_event import CourseEventCollection
from onegov.fsi.collections.notification_template import \
    FsiNotificationTemplateCollection
from onegov.fsi.collections.reservation import ReservationCollection
from onegov.fsi.models.course import Course
from onegov.fsi.models.course_event import CourseEvent
from onegov.fsi.models.notification_template import FsiNotificationTemplate


@FsiApp.path(model=Course, path='/course/{id}')
def get_course_details(app, id):
    return CourseCollection(app.session()).by_id(id)


@FsiApp.path(model=CourseEvent, path='/event/{id}')
def get_course_details(app, id):
    return CourseEventCollection(app.session()).by_id(id)


@FsiApp.path(
    model=FsiNotificationTemplate,
    path='/template/{id}')
def get_course_details(app, id):
    return FsiNotificationTemplateCollection(app.session()).by_id(id)


@FsiApp.path(model=CourseCollection, path='/courses')
def get_courses_list(app, request, page=0, creator_id=None, term=None):
    return CourseCollection(
        app.session(),
        page=page,
        creator_id=creator_id,
        term=term,
        locale=request.locale
    )


@FsiApp.path(model=CourseEventCollection,
             path='/events/{course_id}',
             converters=dict(upcoming_only=bool, past_only=bool))
def get_events_from_course(
        app,
        course_id,
        page=0,
        from_date=None,
        upcoming_only=None,
        past_only=None
):
    return CourseEventCollection(
        app.session(),
        page=page,
        course_id=course_id,
        from_date=from_date,
        upcoming_only=upcoming_only,
        past_only=past_only)


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

