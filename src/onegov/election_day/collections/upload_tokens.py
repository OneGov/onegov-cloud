from onegov.election_day.models import UploadToken


class UploadTokenCollection(object):

    def __init__(self, session):
        self.session = session

    def query(self):
        return self.session.query(UploadToken).order_by(UploadToken.created)

    def create(self):
        """ Creates a new token. """

        token = UploadToken()
        self.session.add(token)
        self.session.flush()
        return token

    def delete(self, item):
        """ Deletes the given token. """

        self.session.delete(item)
        self.session.flush()

    def by_id(self, id):
        """ Returns the token by its id. """

        return self.query().filter_by(id=id).first()
