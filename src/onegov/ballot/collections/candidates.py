from onegov.ballot.models import Candidate


class CandidateCollection(object):

    def __init__(self, session):
        self.session = session

    def query(self):
        return self.session.query(Candidate)

    def by_id(self, id):
        return self.query().filter(Candidate.id == id).first()
