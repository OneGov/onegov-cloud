from onegov.org.app import OrgApp
from onegov.org.models import Export
from onegov.ticket import Ticket


@OrgApp.permission_rule(model=Export, permission=object, identity=None)
def has_export_permission_not_logged_in(app, identity, model, permission):
    return model.permission in app.settings.roles.anonymous


@OrgApp.permission_rule(model=Export, permission=object)
def has_export_permissions_logged_in(app, identity, model, permission):
    return model.permission in getattr(app.settings.roles, identity.role)


@OrgApp.permission_rule(model=Ticket, permission=object)
def has_permission_ticket(app, identity, model, permission):
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
