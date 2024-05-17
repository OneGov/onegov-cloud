from onegov.core.utils import normalize_for_url, is_uuid
from onegov.newsletter import Newsletter, Recipient
from onegov.newsletter.errors import AlreadyExistsError


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from datetime import datetime
    from sqlalchemy.orm import Query, Session
    from uuid import UUID


class NewsletterCollection:

    def __init__(self, session: 'Session'):
        self.session = session

    def query(self) -> 'Query[Newsletter]':
        return self.session.query(Newsletter)

    def by_name(self, name: str) -> Newsletter | None:
        return self.query().filter(Newsletter.name == name).first()

    def add(
        self,
        title: str,
        # FIXME: We should be more strict and only allow Markup
        html: str,
        lead: str | None = None,
        meta: dict[str, Any] | None = None,
        content: dict[str, Any] | None = None,
        scheduled: 'datetime | None' = None
    ) -> Newsletter:

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

    def delete(self, newsletter: Newsletter) -> None:
        self.session.delete(newsletter)
        self.session.flush()


class RecipientCollection:

    def __init__(self, session: 'Session'):
        self.session = session

    def query(self) -> 'Query[Recipient]':
        return self.session.query(Recipient)

    def by_id(self, id: 'str | UUID') -> Recipient | None:
        if is_uuid(id):
            return self.query().filter(Recipient.id == id).first()
        return None

    def by_address(
        self,
        address: str,
        group: str | None = None
    ) -> Recipient | None:

        query = self.query()
        query = query.filter(Recipient.address == address)
        query = query.filter(Recipient.group == group)

        return query.first()

    def ordered_by_status_address(self) -> 'Query[Recipient]':
        """ Orders the recipients by status and address. """
        return self.query().order_by(Recipient.confirmed, Recipient.address)

    def add(
        self,
        address: str,
        group: str | None = None,
        confirmed: bool = False
    ) -> Recipient:

        recipient = Recipient(
            address=address,
            group=group,
            confirmed=confirmed
        )
        self.session.add(recipient)
        self.session.flush()

        return recipient

    def delete(self, recipient: Recipient) -> None:
        self.session.delete(recipient)
        self.session.flush()
