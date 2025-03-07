from __future__ import annotations

from onegov.core.security import Personal
from onegov.core.security.roles import (
    get_roles_setting as get_roles_setting_base)
from onegov.core.security.rules import has_permission_logged_in
from onegov.fsi import FsiApp
from onegov.fsi.models import CourseAttendee


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from morepath.authentication import Identity
    from onegov.core.security.roles import Intent

"""
Since FSI is mainly for internal use, a user must be logged in to see even
courses.
The standard has_permission_logged_in treats members almost like anon users

The idea for permission is the following:

Personal: beeing logged in by default, can be overwritten model wise
Private: also editor can access it
Secret: admins

"""


@FsiApp.replace_setting_section(section='roles')
def get_roles_setting() -> dict[str, set[type[Intent]]]:
    # NOTE: Without a supporter role for now
    return get_roles_setting_base()


@FsiApp.permission_rule(model=object, permission=Personal)
def local_is_logged_in(
    app: FsiApp,
    identity: Identity,
    model: object,
    permission: type[Personal]
) -> bool:
    return identity.role in ('admin', 'editor', 'member')


@FsiApp.permission_rule(model=CourseAttendee, permission=Personal)
def has_course_attendee_permission(
    app: FsiApp,
    identity: Identity,
    model: CourseAttendee,
    permission: type[Personal]
) -> bool:
    if identity.role == 'member':
        if model.user is None:
            return False
        return model.user.username == identity.userid
    return has_permission_logged_in(app, identity, model, permission)
