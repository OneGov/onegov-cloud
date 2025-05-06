from __future__ import annotations

from email_validator import validate_email
from onegov.core.crypto import random_token
from onegov.core.orm import Base
from onegov.core.orm.mixins import (ContentMixin, TimestampMixin,
                                    content_property, dict_markup_property,
                                    dict_property)
from onegov.core.orm.types import UTCDateTime, UUID
from onegov.core.utils import normalize_for_url
from onegov.search import SearchableContent
from sqlalchemy import and_
from sqlalchemy import Boolean
from sqlalchemy import column
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Index
from sqlalchemy import not_
from sqlalchemy import select
from sqlalchemy import Table
from sqlalchemy import Text
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import object_session, validates, relationship
from uuid import uuid4


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from datetime import datetime


# Newsletters and recipients are joined in a many to many relationship
newsletter_recipients = Table(
    'newsletter_recipients',
    Base.metadata,
    Column('newsletter_id', Text, ForeignKey('newsletters.name')),
    Column('recipient_id', UUID, ForeignKey('recipients.id'))
)


class Newsletter(Base, ContentMixin, TimestampMixin, SearchableContent):
    """ Represents a newsletter before and after it is sent.

    A newsletter basically consists of a title/subject, a content and a
    number of recipients. We assume that all newsletters are sent in HTML
    using onegov.core, which automatically creates a text representation.

    """

    __tablename__ = 'newsletters'

    es_id = 'name'
    es_properties = {
        'title': {'type': 'localized'},
        'lead': {'type': 'localized'},
        'html': {'type': 'localized_html'}
    }

    @property
    def es_public(self) -> bool:
        return self.sent is not None

    #: the name of the newsletter, derived from the title
    name: Column[str] = Column(Text, nullable=False, primary_key=True)

    @validates('name')
    def validate_name(self, key: str, name: str) -> str:
        assert normalize_for_url(name) == name, (
            'The given name was not normalized'
        )

        return name

    #: the title of the newsletter
    title: Column[str] = Column(Text, nullable=False)

    #: the optional lead or editorial of the newsletter
    lead: Column[str | None] = Column(Text, nullable=True)

    #: the content of the newsletter in html, this is not just the partial
    #: content, but the actual, fully rendered html content.
    html: Column[str] = Column(Text, nullable=False)

    #: the closing remark of the newsletter
    closing_remark = dict_markup_property('content')

    #: null if not sent yet, otherwise the date this newsletter was first sent
    sent: Column[datetime | None] = Column(UTCDateTime, nullable=True)

    #: time the newsletter is scheduled to be sent (in UTC)
    scheduled: Column[datetime | None] = Column(UTCDateTime, nullable=True)

    #: the recipients of this newsletter, meant in part as a tracking feature
    #: to answer the question "who got which newsletters?" - for this to work
    #: the user of onegov.newsletter has to make sure that sent out
    #: newsletters can't have actual recipients removed from them.
    #: onegov.newsletter does not make any guarantees here
    recipients: relationship[list[Recipient]] = relationship(
        'Recipient',
        secondary=newsletter_recipients,
        back_populates='newsletters')

    @property
    def open_recipients(self) -> tuple[Recipient, ...]:
        received = select([newsletter_recipients.c.recipient_id]).where(
            newsletter_recipients.c.newsletter_id == self.name)

        return tuple(object_session(self).query(Recipient).filter(
            and_(
                not_(
                    Recipient.id.in_(received)
                ),
                Recipient.confirmed == True
            )
        ))

    show_news_as_tiles: dict_property[bool] = content_property(default=True)

    #: categories the newsletter reports on
    newsletter_categories: dict_property[list[str] | None] = content_property()


class Recipient(Base, TimestampMixin, ContentMixin):
    """ Represents a single recipient.

    Recipients may be grouped by any kind of string. Only inside their groups
    are recipient addresses unique. However, groups are an optional feature
    and they are not deeply integrated. If you don't care for group, never
    use them and the list becomes like a simple list of addresses with no
    duplicate addresses present.

    """

    __tablename__ = 'recipients'

    #: the id of the recipient, used in the url
    id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: the email address of the recipient, unique per group
    address: Column[str] = Column(Text, nullable=False)

    @validates('address')
    def validate_address(self, key: str, address: str) -> str:
        assert validate_email(address)
        return address

    #: the recipient group, a freely choosable string - may be null
    group: Column[str | None] = Column(Text, nullable=True)

    #: the newsletters that this recipient received
    newsletters: relationship[list[Newsletter]] = relationship(
        'Newsletter',
        secondary=newsletter_recipients,
        back_populates='recipients')

    #: this token is used for confirm and unsubscribe
    token: Column[str] = Column(Text, nullable=False, default=random_token)

    #: when recipients are added, they are unconfirmed. At this point they get
    #: one e-mail with a confirmation link. If they ignore said e-mail they
    #: should not get another one.
    confirmed: Column[bool] = Column(Boolean, nullable=False, default=False)

    #: subscribed newsletter categories. For legacy reasons, no selection
    # means all topics are subscribed to.
    subscribed_categories: dict_property[list[str] | None] = content_property()

    daily_newsletter: Column[bool] = Column(
        Boolean, nullable=False, default=False)

    @declared_attr
    def __table_args__(cls) -> tuple[Index, ...]:
        return (
            Index(
                'recipient_address_in_group', 'address', 'group',
                unique=True, postgresql_where=column('group') != None
            ),
            Index(
                'recipient_address_without_group', 'address',
                unique=True, postgresql_where=column('group') == None
            ),
        )

    @property
    def subscription(self) -> Subscription:
        return Subscription(self, self.token)

    @property
    def is_inactive(self) -> bool:
        """
        Checks if the recipient's email address is marked as inactive.

        Returns:
            bool: True if the email address is marked as inactive, False
            otherwise.
        """
        return self.meta.get('inactive', False)

    def mark_inactive(self) -> None:
        """
        Marks the recipient's email address as inactive.

        This method sets the 'inactive' flag in the recipient's metadata to
        True. It is typically used when a bounce event causes the email
        address to be deactivated by Postmark.
        """
        self.meta['inactive'] = True

    def reactivate(self) -> None:
        """
        Marks a previously `inactive` recipient as active again.
        """
        self.meta['inactive'] = False


class Subscription:
    """ Adds subscription management to a recipient. """

    def __init__(self, recipient: Recipient, token: str):
        self.recipient = recipient
        self.token = token

    @property
    def recipient_id(self) -> uuid.UUID:
        # even though this seems redundant, we need this property
        # for morepath, so it can match it to the path variable
        return self.recipient.id

    def confirm(self) -> bool:
        if self.recipient.token != self.token:
            return False

        self.recipient.confirmed = True
        return True

    def unsubscribe(self) -> bool:
        if self.recipient.token != self.token:
            return False

        # don't delete if they unsubscribe before they confirm
        if not self.recipient.confirmed:
            return True

        session = object_session(self.recipient)
        session.delete(self.recipient)
        session.flush()

        return True
