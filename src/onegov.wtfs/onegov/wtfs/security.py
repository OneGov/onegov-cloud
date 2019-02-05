from onegov.core.security.roles import get_roles_setting as _get_roles_setting
from onegov.user import User
from onegov.user import UserCollection
from onegov.user import UserGroup
from onegov.user import UserGroupCollection
from onegov.wtfs import WtfsApp


# todo: change to AddUnrestricted, EditUnrestricted (ViewUnrestricted?)
# todo: remove Private, Protected, Secret, Public


class AddModel(object):
    """ The permission to add a given model. """


class EditModel(object):
    """ The permission to edit a given model. """


class DeleteModel(object):
    """ The permission to delete a given model. """


class ViewModel(object):
    """ The permission to view a given model. """


class AddModelSameGroup(object):
    """ The permission to add a given group owned model. """


class EditModelSameGroup(object):
    """ The permission to edit a given group owned model. """


class DeleteModelSameGroup(object):
    """ The permission to delete a given group owned model. """


class ViewModelSameGroup(object):
    """ The permission to view a given group owned model. """


def same_group(model, identity):
    if model.group_id and identity.groupid:
        return model.group_id.hex == identity.groupid
    return False


@WtfsApp.setting_section(section="roles")
def get_roles_setting():
    roles = _get_roles_setting()
    roles['admin'] |= {AddModel, EditModel, DeleteModel, ViewModel}
    return roles


@WtfsApp.permission_rule(model=UserGroupCollection, permission=object)
def has_permission_user_groups(app, identity, model, permission):
    # Only admins may manage user groups
    if identity.role != 'admin':
        return False

    return permission in getattr(app.settings.roles, identity.role)


@WtfsApp.permission_rule(model=UserGroup, permission=object)
def has_permission_user_group(app, identity, model, permission):
    # Only admins may manage user groups
    if identity.role != 'admin':
        return False

    # User groups linked to municipalities and users cannot be deleted
    if permission in {DeleteModel}:
        if model.municipality:
            return False
        if model.users.first():
            return False

    return permission in getattr(app.settings.roles, identity.role)


@WtfsApp.permission_rule(model=UserCollection, permission=object)
def has_permission_users(app, identity, model, permission):
    # There is only one view for users, give admin this permission, too
    if identity.role == 'admin':
        if permission in {ViewModelSameGroup}:
            return True

    # Editors may view and add users, too (the same group distiniction is done
    # in the views itself)
    if identity.role == 'editor':
        if permission in {ViewModelSameGroup, AddModelSameGroup}:
            return True
        return False

    # Members are not allowed to do anything
    if identity.role == 'member':
        return False

    return permission in getattr(app.settings.roles, identity.role)


@WtfsApp.permission_rule(model=User, permission=object)
def has_permission_user(app, identity, model, permission):
    # Admins can not be managed through the web
    if model.role == 'admin':
        return False

    # There is only one view/delete user, give admin this permission, too
    if identity.role == 'admin':
        if permission in {ViewModelSameGroup, DeleteModelSameGroup}:
            return True

    # Editors may view, edit and delete a user within the same group
    if identity.role == 'editor':
        if permission in {ViewModelSameGroup, EditModelSameGroup,
                          DeleteModelSameGroup}:
            if model.role == 'member':
                if same_group(model, identity):
                    return True
        return False

    # Members are not allowed to do anything
    if identity.role == 'member':
        return False

    return permission in getattr(app.settings.roles, identity.role)
