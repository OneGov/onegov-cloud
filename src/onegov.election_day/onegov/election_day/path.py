from onegov.ballot import Vote, VoteCollection
from onegov.election_day import ElectionDayApp
from onegov.election_day.model import Principal


@ElectionDayApp.path(model=Principal, path='/')
def get_principal(app):
    return app.principal


@ElectionDayApp.path(model=Vote, path='/abstimmung/{id}')
def get_vote(app, id):
    return VoteCollection(app.session()).by_id(id)
