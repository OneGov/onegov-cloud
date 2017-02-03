from onegov.user import User, UserCollection


def all_users(request):
    u = UserCollection(request.app.session()).query()
    u = u.order_by(User.title)
    return u.all()
