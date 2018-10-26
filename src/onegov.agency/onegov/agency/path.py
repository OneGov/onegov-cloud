from onegov.agency.app import AgencyApp
from onegov.agency.collections import ExtendedAgencyCollection
from onegov.agency.collections import ExtendedPersonCollection
from onegov.agency.models import AgencyProxy
from onegov.people import Agency
from onegov.people import AgencyMembership
from onegov.people import AgencyMembershipCollection


@AgencyApp.path(
    model=ExtendedPersonCollection,
    path='/personen',
    converters=dict(page=int)
)
def get_people(app, page=0, letter=None, agency=None):
    return ExtendedPersonCollection(app.session(), page, letter, agency)


@AgencyApp.path(
    model=ExtendedAgencyCollection,
    path='/organisationen'
)
def get_agencies(app):
    return ExtendedAgencyCollection(app.session())


@AgencyApp.path(
    model=Agency,
    path='/organisation',
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
    model=AgencyMembership,
    path='/mitgliedschaft/{id}'
)
def get_membership(app, id):
    return AgencyMembershipCollection(app.session()).by_id(id)
