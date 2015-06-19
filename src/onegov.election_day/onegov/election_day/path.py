from onegov.ballot import Ballot, BallotCollection, Vote, VoteCollection
from onegov.election_day import ElectionDayApp
from onegov.election_day.model import Principal


@ElectionDayApp.path(model=Principal, path='/')
def get_principal(app):
    return app.principal


@ElectionDayApp.path(model=Vote, path='/vote/{id}')
def get_vote(app, id):
    return VoteCollection(app.session()).by_id(id)


@ElectionDayApp.path(model=Ballot, path='/ballot/{id}')
def get_ballot(app, id):
    return BallotCollection(app.session()).by_id(id)
