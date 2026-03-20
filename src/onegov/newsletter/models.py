from __future__ import annotations

from datetime import datetime
from email_validator import validate_email
from onegov.core.crypto import random_token
from onegov.core.orm import Base
from onegov.core.orm.mixins import (
    content_property, dict_markup_property, dict_property,
    ContentMixin, TimestampMixin)
from onegov.core.utils import normalize_for_url
from onegov.search import SearchableContent
from sqlalchemy import and_
from sqlalchemy import column
from sqlalchemy import not_
from sqlalchemy import select
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Index
from sqlalchemy import Table
from sqlalchemy import Text
from sqlalchemy import UUID as UUIDType
from sqlalchemy.orm import mapped_column, relationship, Mapped
from sqlalchemy.orm import object_session, validates
from translationstring import TranslationString
from uuid import uuid4
from uuid import UUID


# Newsletters and recipients are joined in a many to many relationship
newsletter_recipients = Table(
    'newsletter_recipients',
    Base.metadata,
    Column('newsletter_id', Text, ForeignKey('newsletters.name')),
    Column('recipient_id', UUIDType(as_uuid=True), ForeignKey('recipients.id'))
)


class Newsletter(Base, ContentMixin, TimestampMixin, SearchableContent):
    """ Represents a newsletter before and after it is sent.

    A newsletter basically consists of a title/subject, a content and a
    number of recipients. We assume that all newsletters are sent in HTML
    using onegov.core, which automatically creates a text representation.

    """

    __tablename__ = 'newsletters'

    # HACK: We don't want to set up translations in this module for this single
    #       string, we know we already have a translation in a different domain
    #       so we just manually specify it for now.
    fts_type_title = TranslationString('Newsletter', domain='onegov.org')
    fts_id = 'name'
    fts_title_property = 'title'
    fts_properties = {
        'title': {'type': 'localized', 'weight': 'A'},
        'lead': {'type': 'localized', 'weight': 'B'},
        'html': {'type': 'localized', 'weight': 'C'}
    }

    @property
    def fts_public(self) -> bool:
        return self.sent is not None

    #: the name of the newsletter, derived from the title
    name: Mapped[str] = mapped_column(primary_key=True)

    @validates('name')
    def validate_name(self, key: str, name: str) -> str:
        assert normalize_for_url(name) == name, (
            'The given name was not normalized'
        )

        return name

    #: the title of the newsletter
    title: Mapped[str]

    #: the optional lead or editorial of the newsletter
    lead: Mapped[str | None]

    #: the content of the newsletter in html, this is not just the partial
    #: content, but the actual, fully rendered html content.
    html: Mapped[str]

    #: the closing remark of the newsletter
    closing_remark = dict_markup_property('content')

    #: null if not sent yet, otherwise the date this newsletter was first sent
    sent: Mapped[datetime | None]

    #: time the newsletter is scheduled to be sent (in UTC)
    scheduled: Mapped[datetime | None]

    #: the recipients of this newsletter, meant in part as a tracking feature
    #: to answer the question "who got which newsletters?" - for this to work
    #: the user of onegov.newsletter has to make sure that sent out
    #: newsletters can't have actual recipients removed from them.
    #: onegov.newsletter does not make any guarantees here
    recipients: Mapped[list[Recipient]] = relationship(
        secondary=newsletter_recipients,
        back_populates='newsletters'
    )

    #: whether the newsletter should only show previews instead of full text
    show_only_previews: Mapped[bool] = mapped_column(default=True)

    @property
    def open_recipients(self) -> tuple[Recipient, ...]:
        session = object_session(self)
        assert session is not None

        received = select(newsletter_recipients.c.recipient_id).where(
            newsletter_recipients.c.newsletter_id == self.name)

        return tuple(session.query(Recipient).filter(
            and_(
                not_(
                    Recipient.id.in_(received)
                ),
                Recipient.confirmed == True
            )
        ))

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
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4
    )

    #: the email address of the recipient, unique per group
    address: Mapped[str]

    @validates('address')
    def validate_address(self, key: str, address: str) -> str:
        assert validate_email(address)
        return address

    #: the recipient group, a freely choosable string - may be null
    group: Mapped[str | None]

    #: the newsletters that this recipient received
    newsletters: Mapped[list[Newsletter]] = relationship(
        secondary=newsletter_recipients,
        back_populates='recipients'
    )

    #: this token is used for confirm and unsubscribe
    token: Mapped[str] = mapped_column(default=random_token)

    #: when recipients are added, they are unconfirmed. At this point they get
    #: one e-mail with a confirmation link. If they ignore said e-mail they
    #: should not get another one.
    confirmed: Mapped[bool] = mapped_column(default=False)

    #: subscribed newsletter categories. For legacy reasons, no selection
    # means all topics are subscribed to.
    subscribed_categories: dict_property[list[str] | None] = content_property()

    daily_newsletter: Mapped[bool] = mapped_column(default=False)

    __table_args__ = (
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
    def recipient_id(self) -> UUID:
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
        assert session is not None
        session.delete(self.recipient)
        session.flush()

        return True
