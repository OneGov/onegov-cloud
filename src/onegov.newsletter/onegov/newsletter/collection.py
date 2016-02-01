from onegov.core.utils import normalize_for_url
from onegov.newsletter import Newsletter, Recipient


class NewsletterCollection(object):

    def __init__(self, session):
        self.session = session

    def query(self):
        return self.session.query(Newsletter)

    def by_name(self, name):
        return self.query().filter(Newsletter.name == name).first()

    def add(self, title, content):
        newsletter = Newsletter(
            name=normalize_for_url(title),
            title=title,
            content=content
        )

        self.session.add(newsletter)
        self.session.flush()

        return newsletter

    def delete(self, newsletter):
        self.session.delete(newsletter)
        self.session.flush()


class RecipientCollection(object):

    def __init__(self, session):
        self.session = session

    def query(self):
        return self.session.query(Recipient)

    def by_id(self, id):
        return self.query().filter(Recipient.id == id).first()

    def by_address(self, address, group=None):
        query = self.query()
        query = query.filter(Recipient.address == address)
        query = query.filter(Recipient.group == group)

        return query.first()

    def add(self, address, group=None):
        recipient = Recipient(address=address, group=group)
        self.session.add(recipient)
        self.session.flush()

        return recipient

    def delete(self, recipient):
        self.session.delete(recipient)
        self.session.flush()
