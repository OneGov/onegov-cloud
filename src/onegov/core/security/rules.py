from __future__ import annotations

from onegov.core.cronjobs import Job
from onegov.core.framework import Framework
from onegov.core.security import Public
from webob.exc import HTTPException


from typing import Any, Literal, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import HasRole


@Framework.permission_rule(model=object, permission=object, identity=None)
def has_permission_not_logged_in(
    app: Framework,
    identity: None,
    model: object,
    permission: object
) -> bool:
    """ This catch-all rule returns the default permission rule. It says
    that the permission must be part of the anonymous rule.

    Models with an 'access' property set to 'secret' are prohibited from being
    viewed by anonymous users.

    """

    if getattr(model, 'access', None) == 'private':
        return False

    if getattr(model, 'access', None) == 'member':
        return False

    if getattr(model, 'published', None) == False:
        return False

    return permission in app.settings.roles.anonymous


@Framework.permission_rule(model=object, permission=object)
def has_permission_logged_in(
    app: Framework,
    identity: HasRole,
    model: object,
    permission: object
) -> bool:
    """ This permission rule matches all logged in identities. It requires
    the identity to have a 'role' attribute. Said role attribute is used
    to determine if the given permission is part of the given role.

    """

    assert hasattr(identity, 'role'), """
        the identity needs to implement a role property
    """

    # basic members are mostly treated like anonymous users
    if identity.role == 'member':
        if getattr(model, 'access', None) == 'private':
            return False

    return permission in getattr(app.settings.roles, identity.role)


@Framework.permission_rule(
    model=HTTPException,
    permission=Public,
    identity=None
)
def may_view_http_errors_not_logged_in(
    app: Framework,
    identity: None,
    model: HTTPException,
    permission: type[Public]
) -> Literal[True]:
    """ HTTP errors may be viewed by anyone, regardeless of settings.

    This is important, otherwise the HTTPForbidden/HTTPNotFound views
    will lead to an exception if the user does not have the ``Public``
    permission.

    """
    return True


@Framework.permission_rule(model=Job, permission=Public, identity=None)
def may_view_cronjobs_not_logged_in(
    app: Framework,
    identity: None,
    model: Job[Any],
    permission: type[Public]
) -> Literal[True]:
    """ Cronjobs are run anonymously from a thread and need to be excluded
    from the permission rules as a result.

    """
    return True
