from onegov.user import User, UserCollection
from sqlalchemy import func


def all_users(request):
    u = UserCollection(request.session).query()
    u = u.order_by(func.lower(User.title))
    return u.all()
