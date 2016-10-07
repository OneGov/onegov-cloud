from onegov.activity import Occasion, OccasionCollection
from onegov.feriennet import FeriennetApp
from onegov.feriennet.collections import VacationActivityCollection
from onegov.feriennet.models import VacationActivity
from uuid import UUID


@FeriennetApp.path(
    model=VacationActivityCollection,
    path='/angebote',
    converters=dict(tags=[str], states=[str], durations=[int]))
def get_vacation_activities(request, app, page=0,
                            tags=[], states=[], durations=[]):

    return VacationActivityCollection(
        session=app.session(),
        page=page,
        identity=request.identity,
        tags=tags,
        states=states,
        durations=durations
    )


@FeriennetApp.path(
    model=VacationActivity,
    path='/angebot/{name}')
def get_vacation_activity(request, app, name):
    return VacationActivityCollection(
        app.session(), identity=request.identity).by_name(name)


@FeriennetApp.path(
    model=Occasion,
    path='/durchfuehrungen/{id}',
    converters=dict(id=UUID))
def get_occasion(request, app, id):
    return OccasionCollection(app.session()).by_id(id)
