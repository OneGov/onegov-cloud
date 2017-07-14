from onegov.user import UserCollection


def get_user(request):
    session = request.app.session()
    return UserCollection(session).by_username(request.identity.userid)


def get_user_id(request):
    session = request.app.session()
    return UserCollection(session).by_username(request.identity.userid).id
