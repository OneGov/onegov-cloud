from onegov.user import Auth
from onegov.wtfs.app import WtfsApp
from onegov.wtfs.collections import MunicipalityCollection
from onegov.wtfs.models import Municipality
from onegov.wtfs.models import Principal


@WtfsApp.path(
    model=Principal,
    path='/'
)
def get_principal(app):
    return app.principal


@WtfsApp.path(
    model=Auth,
    path='/auth'
)
def get_auth(request, to='/'):
    return Auth.from_request(request, to)


@WtfsApp.path(
    model=MunicipalityCollection,
    path='/municipalities'
)
def get_municipalities(request):
    return MunicipalityCollection(request.session)


@WtfsApp.path(
    model=Municipality,
    path='/municipality/{id}'
)
def get_municipality(request, id):
    return MunicipalityCollection(request.session).by_id(id)
