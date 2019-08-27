from onegov.org.app import OrgApp
from onegov.org.models import Export


@OrgApp.permission_rule(model=Export, permission=object, identity=None)
def has_export_permission_not_logged_in(app, identity, model, permission):
    return model.permission in app.settings.roles.anonymous


@OrgApp.permission_rule(model=Export, permission=object)
def has_export_permissions_logged_in(app, identity, model, permission):
    return model.permission in getattr(app.settings.roles, identity.role)
