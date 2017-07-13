from onegov.gazette import GazetteApp
from onegov.gazette.collections import GazetteNoticeCollection
from onegov.gazette.collections import UserGroupCollection
from onegov.gazette.models import GazetteNotice
from onegov.gazette.models import Principal
from onegov.gazette.models import UserGroup
from onegov.user import Auth
from onegov.user import User
from onegov.user import UserCollection


@GazetteApp.path(model=Auth, path='/auth')
def get_auth(request, to='/'):
    return Auth.from_request(request, to)


@GazetteApp.path(model=Principal, path='/')
def get_principal(app):
    return app.principal


@GazetteApp.path(model=UserCollection, path='/users')
def get_users(app):
    return UserCollection(app.session())


@GazetteApp.path(model=User, path='/user/{username}')
def get_user(app, username):
    return UserCollection(app.session()).by_username(username)


@GazetteApp.path(model=UserGroupCollection, path='/groups')
def get_groups(app):
    return UserGroupCollection(app.session())


@GazetteApp.path(model=UserGroup, path='/group/{id}')
def get_group(app, id):
    return UserGroupCollection(app.session()).by_id(id)


@GazetteApp.path(model=GazetteNoticeCollection, path='/notices/{state}')
def get_notices(app, state, page=0):
    return GazetteNoticeCollection(app.session(), state=state, page=page)


@GazetteApp.path(model=GazetteNotice, path='/notice/{name}')
def get_notice(app, name):
    return GazetteNoticeCollection(app.session()).by_name(name)
