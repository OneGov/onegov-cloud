from onegov.winterthur.app import WinterthurApp
from onegov.winterthur.collections import AddressCollection


@WinterthurApp.path(
    model=AddressCollection,
    path='/streets-directory')
def get_streets_directory(app):
    return AddressCollection(app.session())
