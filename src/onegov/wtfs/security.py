import sedate

from datetime import datetime, timedelta
from onegov.core.security import Public
from onegov.core.security.permissions import Intent
from onegov.user import User
from onegov.user import UserCollection
from onegov.wtfs import WtfsApp
from onegov.wtfs.collections import ScanJobCollection
from onegov.wtfs.models import DailyList
from onegov.wtfs.models import DailyListBoxes
from onegov.wtfs.models import Municipality
from onegov.wtfs.models import Notification
from onegov.wtfs.models import ScanJob
from onegov.wtfs.models import UserManual


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from morepath import Identity


class AddModel(Intent):
    """ The permission to add a given model. """


class AddModelUnrestricted(Intent):
    """ The permission to add given model without any restrictions. """


class EditModel(Intent):
    """ The permission to edit a given model. """


class EditModelUnrestricted(Intent):
    """ The permission to edit a given model without any restrictions. """


class DeleteModel(Intent):
    """ The permission to delete a given model. """


class ViewModel(Intent):
    """ The permission to view a given model. """


class ViewModelUnrestricted(Intent):
    """ The permission to view a given model without any restrictions. """


def same_group(model: object, identity: 'Identity') -> bool:
    """ Returns True, if the given model is in the same user group/municipality
    as the given identy.

    """
    if hasattr(model, 'group_id'):
        if model.group_id and identity.groupid:
            return model.group_id.hex == identity.groupid
    elif hasattr(model, 'municipality_id'):
        if model.municipality_id and identity.groupid:
            return model.municipality_id.hex == identity.groupid
    return False


@WtfsApp.setting_section(section='roles')
def get_roles_setting() -> dict[str, set[type[Intent]]]:
    return {
        'admin': {
            AddModel,
            AddModelUnrestricted,
            EditModel,
            EditModelUnrestricted,
            DeleteModel,
            ViewModel,
            ViewModelUnrestricted,
            Public,
        },
        'editor': {
            Public,
        },
        'member': {
            Public,
        },
        'anonymous': {
            Public,
        },
    }


@WtfsApp.permission_rule(model=Municipality, permission=object)
def has_permission_municipality(
    app: WtfsApp,
    identity: 'Identity',
    model: Municipality,
    permission: object
) -> bool:
    # Municipalities with data and/or users cannot not be deleted
    if permission in {DeleteModel}:
        if model.users.first():
            return False
        if model.has_data:
            return False

    return permission in getattr(app.settings.roles, identity.role)


@WtfsApp.permission_rule(model=UserCollection, permission=object)
def has_permission_users(
    app: WtfsApp,
    identity: 'Identity',
    model: UserCollection,
    permission: object
) -> bool:
    # Editors may view and add users
    if identity.role == 'editor':
        if permission in {ViewModel, AddModel}:
            return True

    return permission in getattr(app.settings.roles, identity.role)


@WtfsApp.permission_rule(model=User, permission=object)
def has_permission_user(
    app: WtfsApp,
    identity: 'Identity',
    model: User,
    permission: object
) -> bool:
    # One may not delete himself
    if model.username == identity.userid:
        if permission in {DeleteModel}:
            return False

    # Editors may view, edit and delete members within the same group or
    # view and edit themselves
    if identity.role == 'editor':
        if permission in {ViewModel, EditModel, DeleteModel}:
            if model.role == 'member':
                if same_group(model, identity):
                    return True
        if permission in {ViewModel, EditModel}:
            if model.username == identity.userid:
                return True

    return permission in getattr(app.settings.roles, identity.role)


@WtfsApp.permission_rule(model=ScanJobCollection, permission=object)
def has_permission_scan_jobs(
    app: WtfsApp,
    identity: 'Identity',
    model: ScanJobCollection,
    permission: object
) -> bool:
    # Editors and members of groups may view and add scan jobs
    if identity.role in ('editor', 'member'):
        if identity.groupid:
            if permission in {ViewModel, AddModel}:
                return True

    return permission in getattr(app.settings.roles, identity.role)


@WtfsApp.permission_rule(model=ScanJob, permission=object)
def has_permission_scan_job(
    app: WtfsApp,
    identity: 'Identity',
    model: ScanJob,
    permission: object
) -> bool:
    # Editors and members of groups may view and edit scan jobs within
    # the same group
    if identity.role in ('editor', 'member'):
        if identity.groupid:

            if permission in {ViewModel, EditModel}:
                if same_group(model, identity):
                    return True

            if permission is DeleteModel and identity.role == 'editor':
                if same_group(model, identity):
                    dt = model.dispatch_date

                    # editors of the same group may delete scan jobs up until
                    # 17:00 on the day before the dispatch
                    horizon = datetime(dt.year, dt.month, dt.day, 17)
                    horizon -= timedelta(days=1)
                    horizon = sedate.replace_timezone(horizon, 'Europe/Zurich')

                    now = sedate.utcnow()

                    return now <= horizon

    return permission in getattr(app.settings.roles, identity.role)


@WtfsApp.permission_rule(model=DailyList, permission=object)
def has_permission_daily_list(
    app: WtfsApp,
    identity: 'Identity',
    model: DailyList,
    permission: object
) -> bool:
    # Members without groups (transport company) may view the daily list
    # selection form
    if identity.role == 'member':
        if not identity.groupid:
            if permission in {ViewModel}:
                return True

    return permission in getattr(app.settings.roles, identity.role)


@WtfsApp.permission_rule(model=DailyListBoxes, permission=object)
def has_permission_daily_list_boxes(
    app: WtfsApp,
    identity: 'Identity',
    model: DailyListBoxes,
    permission: object
) -> bool:
    # Members without groups (transport company) may view the daily list boxes
    if identity.role == 'member':
        if not identity.groupid:
            if permission in {ViewModel}:
                return True

    return permission in getattr(app.settings.roles, identity.role)


@WtfsApp.permission_rule(model=Notification, permission=object)
def has_permission_notification(
    app: WtfsApp,
    identity: 'Identity',
    model: Notification,
    permission: object
) -> bool:
    # Everybody may view notifications
    if permission in {ViewModel}:
        return True

    return permission in getattr(app.settings.roles, identity.role)


@WtfsApp.permission_rule(model=UserManual, permission=object)
def has_permission_user_manual(
    app: WtfsApp,
    identity: 'Identity',
    model: UserManual,
    permission: object
) -> bool:
    # Everybody may view the user manual
    if permission in {ViewModel}:
        return True

    return permission in getattr(app.settings.roles, identity.role)
