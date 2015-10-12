from onegov.ballot import Ballot, BallotCollection, Vote, VoteCollection
from onegov.election_day import ElectionDayApp
from onegov.election_day.models import Manage, Principal
from onegov.user import Auth


@ElectionDayApp.path(model=Auth, path='/auth')
def get_auth(request, to='/'):
    return Auth.from_request(request, to)


@ElectionDayApp.path(model=Principal, path='/')
def get_principal(app):
    return app.principal


@ElectionDayApp.path(model=Manage, path='/manage')
def get_manage(app):
    return Manage(app.session())


@ElectionDayApp.path(model=Vote, path='/vote/{id}')
def get_vote(app, id):
    return VoteCollection(app.session()).by_id(id)


@ElectionDayApp.path(model=Ballot, path='/ballot/{id}')
def get_ballot(app, id):
    return BallotCollection(app.session()).by_id(id)


@ElectionDayApp.path(model=VoteCollection, path='/votes/{year}')
def get_votes(app, year):
    return VoteCollection(app.session(), year)
