from onegov.ballot.models import Ballot


class BallotCollection(object):

    def __init__(self, session):
        self.session = session

    def query(self):
        return self.session.query(Ballot)

    def by_id(self, id):
        return self.query().filter(Ballot.id == id).first()
