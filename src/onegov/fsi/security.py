from onegov.core.security import Private, Secret, Personal
from onegov.core.security.rules import has_permission_logged_in
from onegov.fsi import FsiApp
from onegov.fsi.models import CourseAttendee

"""
Since FSI is mainly for internal use, a user must logged in to see even
courses.
The standard has_permission_logged_in treats members almost like anon users

The idea for permission is the following:

Personal: beeing logged in by default, can be overwritten model wise
Private: also editor can access it
Secret: admins

"""


@FsiApp.permission_rule(model=object, permission=Personal)
def local_is_logged_in(app, identity, model, permission):
    return identity.role in ('admin', 'editor', 'member')


@FsiApp.permission_rule(model=CourseAttendee, permission=object)
def has_course_attendee_permission(app, identity, model, permission):
    if identity.role == 'member':
        return model.user.username == identity.userid
    return True

# @FsiApp.permission_rule(model=object, permission=Secret)
# def has_secret_permission_logged_in(app, identity, model, permission):
#     """ Things just admins can do
#     """
#     return has_permission_logged_in(app, identity, model, permission)

