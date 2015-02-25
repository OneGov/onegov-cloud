from morepath import settings
from onegov.core import Framework


@Framework.permission_rule(model=object, permission=object, identity=None)
def has_permission_not_logged_in(identity, model, permission):
    """ This catch-all rule returns the default permission rule. It says
    that the permission must be part of the anonymous rule.

    """
    return permission in settings().roles.anonymous


@Framework.permission_rule(model=object, permission=object)
def has_permission_logged_in(identity, model, permission):
    """ This permission rule matches all logged in identities. It requires
    the identity to have a 'role' attribute. Said role attribute is used
    to determine if the given permission is part of the given role.

    """

    assert hasattr(identity, 'role'), """
        the identity needs to implement a role property
    """
    return permission in getattr(settings().roles, identity.role)
