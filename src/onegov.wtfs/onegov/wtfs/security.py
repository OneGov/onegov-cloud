from onegov.core.security import Public
from onegov.user import User
from onegov.user import UserCollection
from onegov.user import UserGroup
from onegov.wtfs import WtfsApp
from onegov.wtfs.collections import ScanJobCollection
from onegov.wtfs.models import DailyList
from onegov.wtfs.models import DailyListBoxes
from onegov.wtfs.models import Municipality
from onegov.wtfs.models import Notification
from onegov.wtfs.models import ScanJob


class AddModel(object):
    """ The permission to add a given model. """


class AddModelUnrestricted(object):
    """ The permission to add given model without any restrictions. """


class EditModel(object):
    """ The permission to edit a given model. """


class EditModelUnrestricted(object):
    """ The permission to edit a given model without any restrictions. """


class DeleteModel(object):
    """ The permission to delete a given model. """


class ViewModel(object):
    """ The permission to view a given model. """


def same_group(model, identity):
    if model.group_id and identity.groupid:
        return model.group_id.hex == identity.groupid
    return False


@WtfsApp.setting_section(section="roles")
def get_roles_setting():
    return {
        'admin': set((
            AddModel,
            AddModelUnrestricted,
            EditModel,
            EditModelUnrestricted,
            DeleteModel,
            ViewModel,
            Public,
        )),
        'editor': set((
            Public,
        )),
        'member': set((
            Public,
        )),
        'anonymous': set((
            Public,
        )),
    }


@WtfsApp.permission_rule(model=UserGroup, permission=object)
def has_permission_user_group(app, identity, model, permission):
    # User groups linked to municipalities and users cannot be deleted
    if permission in {DeleteModel}:
        if model.municipality:
            return False
        if model.users.first():
            return False

    return permission in getattr(app.settings.roles, identity.role)


@WtfsApp.permission_rule(model=Municipality, permission=object)
def has_permission_municipality(app, identity, model, permission):
    # Municipalities with data cannot not be deleted
    if permission in {DeleteModel}:
        if model.has_data:
            return False

    return permission in getattr(app.settings.roles, identity.role)


@WtfsApp.permission_rule(model=UserCollection, permission=object)
def has_permission_users(app, identity, model, permission):
    # Editors may view and add users
    if identity.role == 'editor':
        if permission in {ViewModel, AddModel}:
            return True

    return permission in getattr(app.settings.roles, identity.role)


@WtfsApp.permission_rule(model=User, permission=object)
def has_permission_user(app, identity, model, permission):
    # Admins can not be managed through the web
    if model.role == 'admin':
        if permission not in {Public}:
            return False

    # Editors may view, edit and delete members within the same group
    if identity.role == 'editor':
        if permission in {ViewModel, EditModel, DeleteModel}:
            if model.role == 'member':
                if same_group(model, identity):
                    return True

    return permission in getattr(app.settings.roles, identity.role)


@WtfsApp.permission_rule(model=ScanJobCollection, permission=object)
def has_permission_scan_jobs(app, identity, model, permission):
    # Editors and members of groups may view and add scan jobs
    if identity.role in ('editor', 'member'):
        if identity.groupid:
            if permission in {ViewModel, AddModel}:
                return True

    return permission in getattr(app.settings.roles, identity.role)


@WtfsApp.permission_rule(model=ScanJob, permission=object)
def has_permission_scan_job(app, identity, model, permission):
    # Editors and members of groups may view and edit scan jobs within
    # the same group
    if identity.role in ('editor', 'member'):
        if identity.groupid:
            if permission in {ViewModel, EditModel}:
                if same_group(model, identity):
                    return True

    return permission in getattr(app.settings.roles, identity.role)


@WtfsApp.permission_rule(model=DailyList, permission=object)
def has_permission_daily_list(app, identity, model, permission):
    # Members without groups (transport company) may view the daily list
    # selection form
    if identity.role == 'member':
        if not identity.groupid:
            if permission in {ViewModel}:
                return True

    return permission in getattr(app.settings.roles, identity.role)


@WtfsApp.permission_rule(model=DailyListBoxes, permission=object)
def has_permission_daily_list_boxes(app, identity, model, permission):
    # Members without groups (transport company) may view the daily list boxes
    if identity.role == 'member':
        if not identity.groupid:
            if permission in {ViewModel}:
                return True

    return permission in getattr(app.settings.roles, identity.role)


@WtfsApp.permission_rule(model=Notification, permission=object)
def has_permission_notificastion(app, identity, model, permission):
    # Everybody may view notifications
    if permission in {ViewModel}:
        return True

    return permission in getattr(app.settings.roles, identity.role)
