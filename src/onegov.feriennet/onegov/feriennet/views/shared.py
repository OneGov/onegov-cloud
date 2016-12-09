from onegov.activity import Period, PeriodCollection
from onegov.user import User, UserCollection


def all_periods(request):
    p = PeriodCollection(request.app.session()).query()
    p = p.order_by(Period.execution_start)
    return p.all()


def all_users(request):
    u = UserCollection(request.app.session()).query()
    u = u.order_by(User.title)
    return u.all()
