from __future__ import annotations

from onegov.core.security import Public, Personal, Private
from onegov.core.security.roles import get_roles_setting as \
    get_roles_setting_base
from onegov.pas import PasApp
from onegov.pas.models.attendence import Attendence
from onegov.pas.models.commission import Commission
from onegov.pas.models.parliamentarian import PASParliamentarian
from onegov.user import User
from onegov.user import Auth


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Any
    from onegov.core.security.roles import Intent
    from morepath import Identity


"""
PAS is fully internal.
    - Admins can do everything.
    - Parliamentarians can report attendance, view limited data.
    - Commission presidents can same as parliamentarians + edit attendance of
      peers in their commission.
"""


@PasApp.replace_setting_section(section='roles')
def get_roles_setting() -> dict[str, set[type[Intent]]]:
    result = get_roles_setting_base()
    # All parliamentarians are basically members, plus a few domain-specific
    # permissions
    result['parliamentarian'] = {Public, Personal}
    result['commission_president'] = {Public, Personal}
    return result


@PasApp.permission_rule(model=object, permission=object)
def has_permission_logged_in(
    app: PasApp,
    identity: Identity,
    model: Any,
    permission: Intent
) -> bool:
    if getattr(model, 'access', None) == 'private':
        if identity.role not in ('admin', 'editor'):
            return False

    if getattr(model, 'access', None) == 'member':
        if identity.role not in (
            'admin', 'editor', 'member', 'parliamentarian',
            'commission_president'
        ):
            return False

    return permission in getattr(app.settings.roles, identity.role)


@PasApp.permission_rule(model=Auth, permission=object)
def restrict_auth_access(
    app: PasApp,
    identity: Identity,
    model: Auth,
    permission: object
) -> bool:
    if permission == Personal and identity.role == 'parliamentarian':
        return True

    return permission in getattr(app.settings.roles, identity.role)


@PasApp.permission_rule(model=PASParliamentarian, permission=object)
def restrict_parliamentarian_access(
    app: PasApp,
    identity: Identity,
    model: PASParliamentarian,
    permission: Intent
) -> bool:
    if (
        identity.role == 'parliamentarian'
        and identity.userid == model.email_primary
        and permission == Personal
    ):
        return True

    return permission in getattr(app.settings.roles, identity.role)


@PasApp.permission_rule(model=Commission, permission=Private)
def has_private_access_to_commission(
    app: PasApp,
    identity: Identity,
    model: Commission,
    permission: Intent
) -> bool:
    """ Grant private access to commission presidents of this commission.
    """
    if identity.role == 'commission_president':
        user = app.session().query(User).filter_by(
            username=identity.userid).first()
        if user:
            if user.parliamentarian:  # type:ignore
                membershps =  user.parliamentarian.commission_memberships  # type:ignore
                for membership in membershps: 
                    if membership.commission_id == model.id and \
                            membership.role == 'president':
                        return True
    return permission in getattr(app.settings.roles, identity.role)


@PasApp.permission_rule(model=Attendence, permission=object)
def has_attendence_permission(
    app: PasApp,
    identity: Identity,
    model: Attendence,
    permission: object
) -> bool:
    return identity.role in {
        'admin', 'parliamentarian', 'commission_president'
    }
