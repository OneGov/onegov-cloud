from __future__ import annotations

from onegov.agency import AgencyApp
from onegov.agency.collections import ExtendedAgencyCollection
from onegov.agency.models import AgencyMembershipMoveWithinAgency
from onegov.agency.models import AgencyMembershipMoveWithinPerson
from onegov.agency.models import AgencyMove
from onegov.agency.models.ticket import AgencyMutationTicket
from onegov.agency.models.ticket import PersonMutationTicket
from onegov.core.security.roles import (
    get_roles_setting as get_roles_setting_base)
from onegov.core.security.rules import has_permission_logged_in
from onegov.people import Agency
from onegov.people import AgencyCollection
from onegov.people import AgencyMembership
from onegov.people import Person
from onegov.ticket.collection import ArchivedTicketCollection
from onegov.ticket.collection import TicketCollection
from onegov.user import RoleMapping
from sqlalchemy.orm import object_session


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from morepath.authentication import Identity
    from morepath.authentication import NoIdentity
    from onegov.core.security.roles import Intent
    from sqlalchemy.orm import Session


@AgencyApp.replace_setting_section(section='roles')
def get_roles_setting() -> dict[str, set[type[Intent]]]:
    # NOTE: Without a supporter role for now
    return get_roles_setting_base()


def get_current_role(
    session: Session,
    identity: Identity | NoIdentity
) -> str | None:
    """ Returns the current role of the identity. Elevates the role from member
    to editor if any group role mapping with editor role is present.

    """

    if identity.userid:
        if identity.role == 'member' and identity.groupids:
            roles = session.query(RoleMapping).filter(
                RoleMapping.role == 'editor',
                RoleMapping.group_id.in_(identity.groupids)
            )
            if session.query(roles.exists()).scalar():
                return 'editor'

        return identity.role

    return None


def has_permission(
    app: AgencyApp,
    identity: Identity,
    model: object,
    permission: object
) -> bool:
    """ Global permission with elevated roles. """

    role = get_current_role(app.session(), identity)
    assert role is not None

    if permission in getattr(app.settings.roles, role):
        return True

    return False


def has_model_permission(
    app: AgencyApp,
    identity: Identity,
    model: object,
    permission: object
) -> bool:
    """ Specific model permission with elevated roles for this model. """

    # Check if the identity itself has the role
    if permission in getattr(app.settings.roles, identity.role):
        return True

    # Check the role mappings of the model
    if (
        identity.role == 'member'
        and identity.groupids
        and hasattr(model, 'role_mappings')
        and permission in getattr(app.settings.roles, 'editor', [])
    ):
        roles = model.role_mappings.filter(
            RoleMapping.role == 'editor',
            RoleMapping.group_id.in_(identity.groupids)
        )
        if object_session(model).query(roles.exists()).scalar():
            return True

    # Check the role mappings of the parent
    if parent := getattr(model, 'parent', None):
        return has_model_permission(app, identity, parent, permission)

    return False


@AgencyApp.permission_rule(model=object, permission=object)
def has_permission_all(
    app: AgencyApp,
    identity: Identity,
    model: object,
    permission: object
) -> bool:
    if has_permission_logged_in(app, identity, model, permission):
        return True
    return has_permission(app, identity, model, permission)


@AgencyApp.permission_rule(model=Agency, permission=object)
def has_permission_agency(
    app: AgencyApp,
    identity: Identity,
    model: Agency,
    permission: object
) -> bool:
    return has_model_permission(app, identity, model, permission)


@AgencyApp.permission_rule(model=AgencyMembership, permission=object)
def has_permission_agency_membership(
    app: AgencyApp,
    identity: Identity,
    model: AgencyMembership,
    permission: object
) -> bool:

    if has_model_permission(app, identity, model, permission):
        return True
    if model.agency:
        agency = model.agency
        return has_model_permission(app, identity, agency, permission)
    return False


@AgencyApp.permission_rule(model=Person, permission=object)
def has_permission_person(
    app: AgencyApp,
    identity: Identity,
    model: Person,
    permission: object
) -> bool:

    if has_model_permission(app, identity, model, permission):
        return True
    memberships = model.memberships.all()
    if not memberships:
        if has_permission(app, identity, model, permission):
            return True
    for membership in memberships:
        if membership.agency:
            agency = membership.agency
            if has_model_permission(app, identity, agency, permission):
                return True
    return False


@AgencyApp.permission_rule(model=ExtendedAgencyCollection, permission=object)
@AgencyApp.permission_rule(model=AgencyCollection, permission=object)
def has_permission_agency_collection(
    app: AgencyApp,
    identity: Identity,
    model: AgencyCollection,
    permission: object
) -> bool:
    return has_permission_logged_in(app, identity, model, permission)


@AgencyApp.permission_rule(model=AgencyMove, permission=object)
def has_permission_agency_move(
    app: AgencyApp,
    identity: Identity,
    model: AgencyMove,
    permission: object
) -> bool:

    if model.subject:
        agency = model.subject
        if not has_permission_agency(app, identity, agency, permission):
            return False
    if model.target:
        agency = model.target
        if not has_permission_agency(app, identity, agency, permission):
            return False
    return True


@AgencyApp.permission_rule(
    model=AgencyMembershipMoveWithinAgency, permission=object
)
def has_permission_agency_membership_move_within_agency(
    app: AgencyApp,
    identity: Identity,
    model: AgencyMembershipMoveWithinAgency,
    permission: object
) -> bool:

    if model.subject and model.subject.agency:
        agency = model.subject.agency
        if not has_permission_agency(app, identity, agency, permission):
            return False
    if model.target and model.target.agency:
        agency = model.target.agency
        if not has_permission_agency(app, identity, agency, permission):
            return False
    return True


@AgencyApp.permission_rule(
    model=AgencyMembershipMoveWithinPerson, permission=object
)
def has_permission_agency_membership_move_within_person(
    app: AgencyApp,
    identity: Identity,
    model: AgencyMembershipMoveWithinPerson,
    permission: object
) -> bool:

    if model.subject and model.subject.agency:
        agency = model.subject.agency
        if not has_permission_agency(app, identity, agency, permission):
            return False
    if model.target and model.target.agency:
        agency = model.target.agency
        if not has_permission_agency(app, identity, agency, permission):
            return False
    return True


@AgencyApp.permission_rule(model=AgencyMutationTicket, permission=object)
def has_permission_agency_mutation_ticket(
    app: AgencyApp,
    identity: Identity,
    model: AgencyMutationTicket,
    permission: object
) -> bool:
    if model.handler and model.handler.agency:
        agency = model.handler.agency
        if not has_permission_agency(app, identity, agency, permission):
            return False
    return True


@AgencyApp.permission_rule(model=PersonMutationTicket, permission=object)
def has_permission_person_mutation_ticket(
    app: AgencyApp,
    identity: Identity,
    model: PersonMutationTicket,
    permission: object
) -> bool:
    if model.handler and model.handler.person:
        person = model.handler.person
        if not has_permission_person(app, identity, person, permission):
            return False
    return True


@AgencyApp.permission_rule(model=TicketCollection, permission=object)
@AgencyApp.permission_rule(model=ArchivedTicketCollection, permission=object)
def has_permission_ticket_collection(
    app: AgencyApp,
    identity: Identity,
    model: TicketCollection | ArchivedTicketCollection,
    permission: object
) -> bool:
    return has_permission_all(app, identity, model, permission)
