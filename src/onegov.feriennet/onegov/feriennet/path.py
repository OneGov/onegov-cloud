from onegov.feriennet import FeriennetApp
from onegov.feriennet.collections import VacationActivityCollection
from onegov.feriennet.models import VacationActivity


@FeriennetApp.path(model=VacationActivityCollection, path='/angebote')
def get_vacation_activities(app):
    return VacationActivityCollection(app.session())


@FeriennetApp.path(model=VacationActivity, path='/angebot/{name}')
def get_vacation_activity(app, name):
    return VacationActivityCollection(app.session()).by_name(name)
