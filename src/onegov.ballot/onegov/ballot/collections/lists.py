from onegov.ballot.models import List


class ListCollection(object):

    def __init__(self, session):
        self.session = session

    def query(self):
        return self.session.query(List)

    def by_id(self, id):
        return self.query().filter(List.id == id).first()
