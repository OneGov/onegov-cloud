from onegov.core.security import Public, Personal
from onegov.core.security.roles import get_roles_setting as _get_roles_setting
from onegov.user import UserGroup
from onegov.wtfs import WtfsApp


class AddModel(object):
    """ The permission to add a given model. """


class EditModel(object):
    """ The permission to edit a given model. """


class DeleteModel(object):
    """ The permission to delete a given model. """


class ViewModel(object):
    """ The permission to view a given model. """


@WtfsApp.setting_section(section="roles")
def get_roles_setting():
    roles = _get_roles_setting()
    roles['admin'] |= {AddModel, EditModel, DeleteModel, ViewModel}
    roles['carrier'] = {Public, Personal}
    return roles


@WtfsApp.permission_rule(model=UserGroup, permission=object)
def has_permission_user_group(app, identity, model, permission):
    """ User groups linked to municipalities can not be deleted. """
    if permission in {DeleteModel} and model.municipality:
        return False

    return permission in getattr(app.settings.roles, identity.role)
