from onegov.fsi import FsiApp
from onegov.fsi.collections.course import CourseCollection
from onegov.fsi.collections.course_event import CourseEventCollection


@FsiApp.path(model=CourseCollection, path='/courses')
def get_courses_list(app, page=0, creator_id=None):
    return CourseCollection(app.session(), page=page, creator_id=creator_id)


@FsiApp.path(model=CourseCollection, path='/course/<id>/events')
def get_events_from_course(
        app,
        page=0,
        course_id=None,
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
