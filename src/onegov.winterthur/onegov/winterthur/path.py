from onegov.winterthur.app import WinterthurApp
from onegov.winterthur.collections import AddressCollection
from onegov.winterthur.collections import AddressSubsetCollection
from onegov.winterthur.roadwork import RoadworkCollection, Roadwork


@WinterthurApp.path(
    model=AddressCollection,
    path='/streets')
def get_streets_directory(app):
    return AddressCollection(app.session())


@WinterthurApp.path(
    model=AddressSubsetCollection,
    path='/streets/{street}')
def get_street_subset(app, street):
    subset = AddressSubsetCollection(app.session(), street=street)
    return subset.exists() and subset or None


@WinterthurApp.path(
    model=RoadworkCollection,
    path='/roadwork')
def get_roadwork_collection(app, letter=None, query=None):
    return RoadworkCollection(app.roadwork_client, letter=letter, query=query)


@WinterthurApp.path(
    model=Roadwork,
    path='/roadwork/{id}',
    converters=dict(id=int))
def get_roadwork(app, id):
    return RoadworkCollection(app.roadwork_client).by_id(id)
