from onegov.user import Auth
from onegov.user import User
from onegov.user import UserCollection
from onegov.user import UserGroup
from onegov.user import UserGroupCollection
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
    model=UserGroupCollection,
    path='/user-groups'
)
def get_user_groups(request):
    return UserGroupCollection(request.session)


@WtfsApp.path(
    model=UserGroup,
    path='/user-group/{id}'
)
def get_user_group(request, id):
    return UserGroupCollection(request.session).by_id(id)


@WtfsApp.path(
    model=UserCollection,
    path='/users'
)
def get_users(request):
    return UserCollection(request.session)


@WtfsApp.path(
    model=User,
    path='/user/{username}'
)
def get_user(request, username):
    return UserCollection(request.session).by_username(username)


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
