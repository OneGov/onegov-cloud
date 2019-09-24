from onegov.agency.app import AgencyApp
from onegov.agency.collections import ExtendedAgencyCollection
from onegov.agency.collections import ExtendedPersonCollection
from onegov.agency.models import AgencyMembershipMoveWithinAgency
from onegov.agency.models import AgencyMove
from onegov.agency.models import AgencyProxy
from onegov.agency.models.move import AgencyMembershipMoveWithinPerson
from onegov.people import Agency
from onegov.people import AgencyMembership
from onegov.people import AgencyMembershipCollection
from uuid import UUID


@AgencyApp.path(
    model=ExtendedPersonCollection,
    path='/people',
    converters=dict(page=int)
)
def get_people(app, page=0, letter=None, agency=None, xlsx_modified=None):
    return ExtendedPersonCollection(
        app.session(), page, letter, agency, xlsx_modified)


@AgencyApp.path(
    model=ExtendedAgencyCollection,
    path='/organizations',
)
def get_agencies(app, root_pdf_modified=None):
    return ExtendedAgencyCollection(app.session(), root_pdf_modified)


@AgencyApp.path(
    model=Agency,
    path='/organization',
    absorb=True
)
def get_agency(app, absorb):
    collection = ExtendedAgencyCollection(app.session())
    return collection.by_path(absorb)


@AgencyApp.path(
    model=AgencyProxy,
    path='/agency/{id}'
)
def get_agency_proxy(app, id):
    return ExtendedAgencyCollection(app.session()).by_id(id)


@AgencyApp.path(
    model=AgencyMove,
    path='/move/agency/{subject_id}/{direction}/{target_id}',
    converters=dict(subject_id=int, target_id=int)
)
def get_agency_move(app, subject_id, direction, target_id):
    return AgencyMove(app.session(), subject_id, target_id, direction)


@AgencyApp.path(
    model=AgencyMembership,
    path='/membership/{id}'
)
def get_membership(app, id):
    return AgencyMembershipCollection(app.session()).by_id(id)


@AgencyApp.path(
    model=AgencyMembershipMoveWithinAgency,
    path='/move-for-agency/membership/{subject_id}/{direction}/{target_id}',
    converters=dict(subject_id=UUID, target_id=UUID)
)
def get_membership_move_for_agency(app, subject_id, direction, target_id):
    return AgencyMembershipMoveWithinAgency(
        app.session(),
        subject_id,
        target_id,
        direction
    )


@AgencyApp.path(
    model=AgencyMembershipMoveWithinPerson,
    path='/move-for-person/membership/{subject_id}/{direction}/{target_id}',
    converters=dict(subject_id=UUID, target_id=UUID)
)
def get_membership_move_for_person(app, subject_id, direction, target_id):
    return AgencyMembershipMoveWithinPerson(
        app.session(),
        subject_id,
        target_id,
        direction
    )
