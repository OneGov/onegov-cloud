from onegov.core.cronjobs import Job
from onegov.core.framework import Framework
from onegov.core.security import Public
from webob.exc import HTTPException


@Framework.permission_rule(model=object, permission=object, identity=None)
def has_permission_not_logged_in(app, identity, model, permission):
    """ This catch-all rule returns the default permission rule. It says
    that the permission must be part of the anonymous rule.

    Models with an 'access' property set to 'secret' are prohibited from being
    viewed by anonymous users.

    """

    if getattr(model, 'access', None) == 'private':
        return False

    return permission in app.settings.roles.anonymous


@Framework.permission_rule(model=object, permission=object)
def has_permission_logged_in(app, identity, model, permission):
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
    identity=None)
def may_view_http_errors_not_logged_in(app, identity, model, permission):
    """ HTTP errors may be viewed by anyone, regardeless of settings.

    This is important, otherwise the HTTPForbidden/HTTPNotFound views
    will lead to an exception if the user does not have the ``Public``
    permission.

    """
    return True


@Framework.permission_rule(
    model=Job,
    permission=Public,
    identity=None)
def may_view_cronjobs_not_logged_in(app, identity, model, permission):
    """ Cronjobs are run anonymously from a thread and need to be excluded
    from the permission rules as a result.

    """
    return True
