from onegov.feriennet import FeriennetApp
from onegov.feriennet.collections import VacationActivityCollection
from onegov.feriennet.models import VacationActivity


@FeriennetApp.path(
    model=VacationActivityCollection,
    path='/angebote',
    converters=dict(tags=[str]))
def get_vacation_activities(request, app, page=0, tags=[]):

    return VacationActivityCollection(
        session=app.session(),
        page=page,
        identity=request.identity,
        tags=tags
    )


@FeriennetApp.path(model=VacationActivity, path='/angebot/{name}')
def get_vacation_activity(request, app, name):
    return VacationActivityCollection(
        app.session(), identity=request.identity).by_name(name)
