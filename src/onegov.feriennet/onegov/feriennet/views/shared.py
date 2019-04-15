from onegov.user import User, UserCollection
from sqlalchemy import func


def users_for_select_element(request):
    u = UserCollection(request.session).query()
    u = u.with_entities(User.id, User.username, User.title, User.realname)
    u = u.order_by(func.lower(User.title))
    u = u.filter_by(active=True)
    return tuple(u)
