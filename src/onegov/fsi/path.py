from onegov.fsi import FsiApp
from onegov.fsi.collections.course import CourseCollection
from onegov.fsi.collections.course_event import CourseEventCollection


@FsiApp.path(model=CourseCollection, path='/courses')
def get_courses_list(app, request, page=0, creator_id=None, term=None):
    return CourseCollection(
        app.session(),
        page=page,
        creator_id=creator_id,
        term=term,
        locale=request.locale
    )


@FsiApp.path(model=CourseEventCollection, path='/events')
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
