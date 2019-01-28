from onegov.wtfs.app import WtfsApp
from onegov.wtfs.models import Principal
from onegov.user import Auth


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
