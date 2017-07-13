from onegov.user import UserCollection


def get_user(request):
    session = request.app.session()
    return UserCollection(session).by_username(request.identity.userid)
