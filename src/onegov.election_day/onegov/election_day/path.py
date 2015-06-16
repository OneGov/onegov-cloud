from onegov.election_day import ElectionDayApp
from onegov.election_day.model import Principal


@ElectionDayApp.path(model=Principal, path='/')
def get_principal(app):
    return app.principal
