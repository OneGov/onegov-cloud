from onegov.user import UserCollection


def get_user(request):
    session = request.app.session()
    return UserCollection(session).by_username(request.identity.userid)


def get_user_and_group(request):
    user = get_user(request)
    return (
        [user.id] if (user and not user.group) else [],
        [user.group.id] if (user and user.group) else []
    )
