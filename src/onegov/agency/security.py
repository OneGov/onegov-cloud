from morepath.authentication import NO_IDENTITY
from onegov.agency import AgencyApp
from onegov.agency.models import AgencyMembershipMoveWithinAgency
from onegov.agency.models import AgencyMembershipMoveWithinPerson
from onegov.agency.models import AgencyMove
from onegov.agency.models.ticket import AgencyMutationTicket
from onegov.agency.models.ticket import PersonMutationTicket
from onegov.core.security.rules import has_permission_logged_in
from onegov.people import Agency
from onegov.people import AgencyCollection
from onegov.people import AgencyMembership
from onegov.people import Person
from onegov.user import RoleMapping


def get_current_role(session, identity):
    """ Returns the current role of the identity. Elevates the role from member
    to editor if any group role mapping with editor role is present.

    """

    if identity is not NO_IDENTITY:
        if identity.role == 'member' and identity.groupid:
            role = session.query(RoleMapping).filter(
                RoleMapping.role == 'editor',
                RoleMapping.group_id == identity.groupid
            ).first()
            if role:
                return 'editor'

        return identity.role

    return None


def has_permission(app, identity, model, permission):
    """ Global permission with eleveated roles. """

    role = get_current_role(app.session(), identity)
    if permission in getattr(app.settings.roles, role):
        return True

    return False


def has_model_permission(app, identity, model, permission):
    """ Specific model permission with elevated roles for this model. """

    # Check if the identity itself has the role
    if permission in getattr(app.settings.roles, identity.role):
        return True

    # Check the role mappings of the model
    if identity.role == 'member' and identity.groupid:
        if hasattr(model, 'role_mappings'):
            role = model.role_mappings.filter(
                RoleMapping.role == 'editor',
                RoleMapping.group_id == identity.groupid
            ).first()
            if role and permission in getattr(app.settings.roles, 'editor'):
                return True

    # Check if the role mappings of the parent
    if getattr(model, 'parent', None):
        return has_model_permission(app, identity, model.parent, permission)

    return False


@AgencyApp.permission_rule(model=object, permission=object)
def has_permission_all(app, identity, model, permission):
    if has_permission_logged_in(app, identity, model, permission):
        return True
    return has_permission(app, identity, model, permission)


@AgencyApp.permission_rule(model=Agency, permission=object)
def has_permission_agency(app, identity, model, permission):
    return has_model_permission(app, identity, model, permission)


@AgencyApp.permission_rule(model=AgencyMembership, permission=object)
def has_permission_agency_membership(app, identity, model, permission):
    if has_model_permission(app, identity, model, permission):
        return True
    if model.agency:
        agency = model.agency
        return has_model_permission(app, identity, agency, permission)
    return False


@AgencyApp.permission_rule(model=Person, permission=object)
def has_permission_person(app, identity, model, permission):
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


@AgencyApp.permission_rule(model=AgencyCollection, permission=object)
def has_permission_agency_collection(app, identity, model, permission):
    return has_permission_logged_in(app, identity, model, permission)


@AgencyApp.permission_rule(model=AgencyMove, permission=object)
def has_permission_agency_move(app, identity, model, permission):
    return all((
        has_permission_agency(app, identity, model.subject, permission),
        has_permission_agency(app, identity, model.target, permission)
    ))


@AgencyApp.permission_rule(
    model=AgencyMembershipMoveWithinAgency, permission=object
)
def has_permission_agency_membership_move_within_agency(
    app, identity, model, permission
):
    return all((
        has_permission_agency(app, identity, model.subject.agency, permission),
        has_permission_agency(app, identity, model.target.agency, permission)
    ))


@AgencyApp.permission_rule(
    model=AgencyMembershipMoveWithinPerson, permission=object
)
def has_permission_agency_membership_move_within_person(
    app, identity, model, permission
):
    return all((
        has_permission_agency(app, identity, model.subject.agency, permission),
        has_permission_agency(app, identity, model.target.agency, permission)
    ))


@AgencyApp.permission_rule(model=AgencyMutationTicket, permission=object)
def has_permission_agency_mutation_ticket(app, identity, model, permission):
    return has_permission_agency(
        app, identity, model.handler.agency, permission
    )


@AgencyApp.permission_rule(model=PersonMutationTicket, permission=object)
def has_permission_person_mutation_ticket(app, identity, model, permission):
    return has_permission_person(
        app, identity, model.handler.person, permission
    )
