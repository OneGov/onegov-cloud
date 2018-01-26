from onegov.winterthur.app import WinterthurApp
from onegov.winterthur.collections import AddressCollection
from onegov.winterthur.collections import AddressSubsetCollection


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
