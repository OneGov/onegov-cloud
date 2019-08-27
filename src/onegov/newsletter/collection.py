from onegov.core.utils import normalize_for_url, is_uuid
from onegov.newsletter import Newsletter, Recipient
from onegov.newsletter.errors import AlreadyExistsError


class NewsletterCollection(object):

    def __init__(self, session):
        self.session = session

    def query(self):
        return self.session.query(Newsletter)

    def by_name(self, name):
        return self.query().filter(Newsletter.name == name).first()

    def add(self, title, html, lead=None, meta=None, content=None,
            scheduled=None):

        name = normalize_for_url(title)

        if self.by_name(name):
            raise AlreadyExistsError(name)

        newsletter = Newsletter(
            name=normalize_for_url(title),
            title=title,
            html=html,
            lead=lead,
            meta=meta or {},
            content=content or {},
            scheduled=scheduled
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
        if is_uuid(id):
            return self.query().filter(Recipient.id == id).first()

    def by_address(self, address, group=None):
        query = self.query()
        query = query.filter(Recipient.address == address)
        query = query.filter(Recipient.group == group)

        return query.first()

    def add(self, address, group=None, confirmed=False):
        recipient = Recipient(
            address=address,
            group=group,
            confirmed=confirmed
        )
        self.session.add(recipient)
        self.session.flush()

        return recipient

    def delete(self, recipient):
        self.session.delete(recipient)
        self.session.flush()
