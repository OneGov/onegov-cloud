from __future__ import annotations

from onegov.org.app import OrgApp
from onegov.org.models import Export
from onegov.ticket import Ticket


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from morepath.authentication import Identity


@OrgApp.permission_rule(model=Export, permission=object, identity=None)
def has_export_permission_not_logged_in(
    app: OrgApp,
    identity: None,
    model: Export,
    permission: object
) -> bool:
    return model.permission in app.settings.roles.anonymous


@OrgApp.permission_rule(model=Export, permission=object)
def has_export_permissions_logged_in(
    app: OrgApp,
    identity: Identity,
    model: Export,
    permission: object
) -> bool:
    return model.permission in getattr(app.settings.roles, identity.role)


@OrgApp.permission_rule(model=Ticket, permission=object)
def has_permission_ticket(
    app: OrgApp,
    identity: Identity,
    model: Ticket,
    permission: object
) -> bool:

    role = identity.role

    # Downgrade the role
    if role not in ('admin', 'anonymous'):
        groups = app.ticket_permissions.get(model.handler_code, {})
        if model.group in groups:
            if identity.groupid not in groups[model.group]:
                role = 'member'
        elif None in groups:
            if identity.groupid not in groups[None]:
                role = 'member'

    if role == 'member':
        if getattr(model, 'access', None) == 'private':
            return False

    return permission in getattr(app.settings.roles, role)
