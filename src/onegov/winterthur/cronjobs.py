from onegov.winterthur.app import WinterthurApp
from onegov.winterthur.collections import AddressCollection


@WinterthurApp.cronjob(hour=15, minute=50, timezone='Europe/Zurich')
def update_streets_directory(request):
    AddressCollection(request.session).update()
