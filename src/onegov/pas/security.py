from __future__ import annotations

from onegov.core.security import Public, Personal, Private
from onegov.core.security.roles import get_roles_setting as \
    get_roles_setting_base
from onegov.pas import PasApp
from onegov.pas.collections import (
    AttendenceCollection
)
from onegov.pas.models.attendence import Attendence
from onegov.pas.models.commission import Commission
from onegov.org.models import Organisation
from onegov.org.models.file import GeneralFileCollection
from onegov.user import User


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Any
    from onegov.core.security.roles import Intent
    from morepath import Identity
    from onegov.pas.models.parliamentarian import PASParliamentarian


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
    # All parliamentarians are basically members, plus a few
    # specific permissions
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


@PasApp.permission_rule(model=AttendenceCollection, permission=object)
def restrict_attendence_collection_access(
    app: PasApp,
    identity: Identity,
    model: AttendenceCollection,
    permission: Intent
) -> bool:
    # Parliamentarians and commission presidents can access attendance
    # collection
    if identity.role in ('parliamentarian', 'commission_president'):
        # Allow Private permission for attendance collection access
        if isinstance(permission, type) and issubclass(permission, Private):
            return True
        return permission in getattr(app.settings.roles, identity.role)

    return permission in getattr(app.settings.roles, identity.role)


@PasApp.permission_rule(model=Attendence, permission=object)
def restrict_attendence_access(
    app: PasApp,
    identity: Identity,
    model: Attendence,
    permission: Intent
) -> bool:
    # Check basic role permissions first
    if identity.role not in ('parliamentarian', 'commission_president'):
        return permission in getattr(app.settings.roles, identity.role)

    # For parliamentarians and commission presidents, check ownership
    if identity.role in ('parliamentarian', 'commission_president'):
        # Allow Private permission only if they have access to this record
        if isinstance(permission, type) and issubclass(permission, Private):
            user = app.session().query(User).filter_by(
                username=identity.userid).first()
            if not user or not user.parliamentarian:  # type: ignore
                return False

            parliamentarian: PASParliamentarian = user.parliamentarian  # type: ignore

            # Regular parliamentarians can only access their own records
            if identity.role == 'parliamentarian':
                return model.parliamentarian_id == str(parliamentarian.id)

            # Commission presidents can access their own + commission members'
            elif identity.role == 'commission_president':
                # Always allow own records
                if model.parliamentarian_id == str(parliamentarian.id):
                    return True

                # Check if they are president of the commission for this record
                if model.commission_id:
                    from datetime import date
                    for membership in parliamentarian.commission_memberships:
                        if (membership.commission_id == model.commission_id
                            and membership.role == 'president'
                            and (membership.end is None
                                 or membership.end >= date.today())):
                            return True

                return False

        return permission in getattr(app.settings.roles, identity.role)

    return permission in getattr(app.settings.roles, identity.role)


@PasApp.permission_rule(model=Organisation, permission=object)
def restrict_organisation_access(
    app: PasApp,
    identity: Identity,
    model: Organisation,
    permission: Intent
) -> bool:
    # Allow parliamentarians to access pas-settings via Organisation model
    if identity.role in ('parliamentarian', 'commission_president'):
        return permission in getattr(app.settings.roles, identity.role)

    return permission in getattr(app.settings.roles, identity.role)


@PasApp.permission_rule(model=GeneralFileCollection, permission=object)
def restrict_files_collection_access(
    app: PasApp,
    identity: Identity,
    model: GeneralFileCollection,
    permission: Intent
) -> bool:
    # Allow parliamentarians and commission presidents to access files
    if identity.role in ('parliamentarian', 'commission_president'):
        # Allow Private permission for files collection access
        if isinstance(permission, type) and issubclass(permission, Private):
            return True
        return permission in getattr(app.settings.roles, identity.role)

    return permission in getattr(app.settings.roles, identity.role)


# todo: test this
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
                membershps = user.parliamentarian.commission_memberships  # type:ignore
                for membership in membershps:
                    if membership.commission_id == model.id and \
                            membership.role == 'president':
                        return True
    return permission in getattr(app.settings.roles, identity.role)
