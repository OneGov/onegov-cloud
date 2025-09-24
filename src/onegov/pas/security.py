from __future__ import annotations

from onegov.core.security import Public, Personal, Private
from onegov.core.security.roles import get_roles_setting as \
    get_roles_setting_base
from onegov.pas import PasApp
from onegov.pas.collections import (
    AttendenceCollection
)
from onegov.org.models import GeneralFileCollection

from datetime import date
from onegov.pas.models.attendence import Attendence
from onegov.pas.models.commission import Commission
from onegov.pas.models.parliamentarian import PASParliamentarian
from onegov.org.models import Organisation
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
    - Editors and Members in the usual sense don't exist.
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
    return permission in getattr(app.settings.roles, identity.role)


@PasApp.permission_rule(model=AttendenceCollection, permission=object)
def restrict_attendence_collection_access(
    app: PasApp,
    identity: Identity,
    model: AttendenceCollection,
    permission: Intent
) -> bool:
    if identity.role in ('parliamentarian', 'commission_president'):
        # Allow Private permission for attendance collection access
        if isinstance(permission, type) and issubclass(permission, Private):
            return True

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
            if not user or not user.parliamentarian:  # type: ignore[attr-defined]
                return False

            parliamentarian: PASParliamentarian = user.parliamentarian  # type: ignore[attr-defined]

            # Regular parliamentarians can only access their own records
            if identity.role == 'parliamentarian':
                return model.parliamentarian_id == parliamentarian.id

            # Commission presidents can access their own + commission members'
            elif identity.role == 'commission_president':
                # Always allow own records
                if model.parliamentarian_id == parliamentarian.id:
                    return True

                # Check if the parliamentarian owning this attendance record
                # is a member of any commission this president leads
                # Get attendance record owner
                attendance_owner = app.session().query(User).join(
                    User.parliamentarian  # type: ignore[attr-defined]
                ).filter(
                    User.parliamentarian.has(id=model.parliamentarian_id)  # type: ignore[attr-defined]
                ).first()

                if attendance_owner and attendance_owner.parliamentarian:
                    # Check if president leads any commission where attendance
                    # owner is a member
                    for pres_membership in (
                        parliamentarian.commission_memberships
                    ):
                        if (pres_membership.role == 'president'
                            and (pres_membership.end is None
                                 or pres_membership.end >= date.today())):

                            # Check if attendance owner is member of this
                            # commission
                            for member_membership in (
                                attendance_owner.parliamentarian
                                .commission_memberships
                            ):
                                if (
                                    member_membership.commission_id
                                    == pres_membership.commission_id
                                    and (member_membership.end is None
                                         or member_membership.end
                                         >= date.today())
                                ):
                                    return True

                return False

    return permission in getattr(app.settings.roles, identity.role)


@PasApp.permission_rule(model=PASParliamentarian, permission=object)
def restrict_parliamentarian_access(
    app: PasApp,
    identity: Identity,
    model: PASParliamentarian,
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
            if not user or not user.parliamentarian:  # type: ignore[attr-defined]
                return False

            parliamentarian: PASParliamentarian = user.parliamentarian  # type: ignore[attr-defined]

            # Regular parliamentarians can only access their own profile
            if identity.role == 'parliamentarian':
                return model.id == parliamentarian.id

            # Commission presidents can access their own + commission members'
            elif identity.role == 'commission_president':
                # Always allow own profile
                if model.id == parliamentarian.id:
                    return True

                # Check if the target parliamentarian is a member of any
                # commission this president leads
                for pres_membership in parliamentarian.commission_memberships:
                    if (pres_membership.role == 'president'
                        and (pres_membership.end is None
                             or pres_membership.end >= date.today())):

                        # Check if target parliamentarian is member of this
                        # commission
                        for member_membership in model.commission_memberships:
                            if (member_membership.commission_id
                                == pres_membership.commission_id
                                and (member_membership.end is None
                                     or member_membership.end
                                     >= date.today())):
                                return True

                return False

    return permission in getattr(app.settings.roles, identity.role)


@PasApp.permission_rule(model=Organisation, permission=object)
def restrict_organisation_access(
    app: PasApp,
    identity: Identity,
    model: Organisation,
    permission: Intent
) -> bool:
    # Allow parliamentarians to access pas-settings via Organisation model
    return permission in getattr(app.settings.roles, identity.role)


@PasApp.permission_rule(model=GeneralFileCollection, permission=object)
def restrict_files_collection_access(
    app: PasApp,
    identity: Identity,
    model: GeneralFileCollection,
    permission: Intent
) -> bool:
    """ Grant parliamentarians and commission presidents access to files """
    # Special case: auto-grant Private access to these roles
    if (identity.role in ('parliamentarian', 'commission_president') and
        isinstance(permission, type) and issubclass(permission, Private)):
        return True
    # Default: check role permissions
    return permission in getattr(app.settings.roles, identity.role)


@PasApp.permission_rule(model=Commission, permission=Private)
def has_private_access_to_commission(
    app: PasApp,
    identity: Identity,
    model: Commission,
    permission: Intent
) -> bool:
    """
    -Looks up the User from database by username
    - Verifies they're actually a parliamentarian
    - Checks their commission memberships to see if they're the
    - president of THIS specific commission
    If yes → grants access
    """
    if identity.role == 'commission_president':
        user = app.session().query(User).filter_by(
            username=identity.userid).first()
        if user:
            if user.parliamentarian:  # type: ignore[attr-defined]
                membershps = user.parliamentarian.commission_memberships  # type: ignore[attr-defined]
                for membership in membershps:
                    if membership.commission_id == model.id and \
                            membership.role == 'president':
                        return True
    return permission in getattr(app.settings.roles, identity.role)
