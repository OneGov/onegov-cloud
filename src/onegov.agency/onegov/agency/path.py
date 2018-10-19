from onegov.agency.app import AgencyApp
from onegov.agency.collections import ExtendedPersonCollection
from onegov.agency.collections import ExtendedAgencyCollection
from onegov.people import Agency


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
    path='/agency/{id}',
    converters=dict(id=int)
)
def get_agency(app, id):
    return ExtendedAgencyCollection(app.session()).by_id(id)
