from onegov.election_day.models import UploadToken
from uuid import uuid4


class UploadTokenCollection(object):

    def __init__(self, session):
        self.session = session

    def query(self):
        return self.session.query(UploadToken)

    def list(self):
        """ Lists all available tokens. """

        return [str(token.token) for token in self.query()]

    def create(self, token=None):
        """ Creates a new token. """

        if token:
            if not self.query().filter_by(token=token).first():
                self.session.add(UploadToken(token=token))
                self.session.flush()
        else:
            token = uuid4()
            self.session.add(UploadToken(token=token))
            self.session.flush()

        return str(token)

    def delete(self, token):
        """ Deletes the given token. """

        for item in self.query().filter_by(token=token):
            self.session.delete(item)
        self.session.flush()

    def clear(self):
        """ Removes all tokens. """

        for item in self.query():
            self.session.delete(item)
        self.session.flush()
