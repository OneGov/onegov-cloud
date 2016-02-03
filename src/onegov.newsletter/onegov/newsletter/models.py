from onegov.core.crypto import random_token
from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin, TimestampMixin
from onegov.core.orm.types import UTCDateTime, UUID
from onegov.core.utils import normalize_for_url
from onegov.search import ORMSearchable
from sqlalchemy import (
    column,
    Boolean,
    Column,
    ForeignKey,
    Index,
    Table,
    Text,
)
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import object_session, validates, relationship
from uuid import uuid4
from validate_email import validate_email

# Newsletters and recipients are joined in a many to many relationship
newsletter_recipients = Table(
    'newsletter_recipients', Base.metadata,
    Column('newsletter_id', Text, ForeignKey('newsletters.name')),
    Column('recipient_id', UUID, ForeignKey('recipients.id'))
)


class Newsletter(Base, ContentMixin, TimestampMixin, ORMSearchable):
    """ Represents a newsletter before and after it is sent.

    A newsletter basically consists of a title/subject, a content and a
    number of recipients. We assume that all newsletters are sent in HTML
    using onegov.core, which automatically creates a text representation.

    """

    __tablename__ = 'newsletters'

    es_id = 'name'
    es_language = 'de'  # XXX add to database in the future
    es_properties = {
        'title': {'type': 'localized'},
        'lead': {'type': 'localized'},
        'html': {'type': 'localized_html'}
    }

    @property
    def es_public(self):
        return self.sent is not None

    #: the name of the newsletter, derived from the title
    name = Column(Text, nullable=False, primary_key=True)

    @validates('name')
    def validate_name(self, key, name):
        assert normalize_for_url(name) == name, (
            "The given name was not normalized"
        )

        return name

    #: the title of the newsletter
    title = Column(Text, nullable=False)

    #: the optional lead or editorial of the newsletter
    lead = Column(Text, nullable=True)

    #: the content of the newsletter in html, this is not just the partial
    #: content, but the actual, fully rendered html content.
    html = Column(Text, nullable=False)

    #: null if not sent yet, otherwise the date this newsletter was first sent
    sent = Column(UTCDateTime, nullable=True)

    #: the recipients of this newsletter, meant in part as a tracking feature
    #: to answer the question "who got which newsletters?" - for this to work
    #: the user of onegov.newsletter has to make sure that sent out
    #: newsletters can't have actual recipients removed from them.
    #: onegov.newsletter does not make any guarantees here
    recipients = relationship(
        'Recipient',
        secondary=newsletter_recipients,
        back_populates='newsletters')


class Recipient(Base, TimestampMixin):
    """ Represents a single recipient.

    Recipients may be grouped by any kind of string. Only inside their groups
    are recipient addresses unique. However, groups are an optional feature
    and they are not deeply integrated. If you don't care for group, never
    use them and the list becomes like a simple list of addresses with no
    duplicate addresses present.

    """

    __tablename__ = 'recipients'

    #: the id of the recipient, used in the url
    id = Column(UUID, primary_key=True, default=uuid4)

    #: the email address of the recipient, unique per group
    address = Column(Text, nullable=False)

    @validates('address')
    def validate_address(self, key, address):
        assert validate_email(address)
        return address

    #: the recipient group, a freely choosable string - may be null
    group = Column(Text, nullable=True)

    #: the newsletters that this recipient received
    newsletters = relationship(
        'Newsletter',
        secondary=newsletter_recipients,
        back_populates='recipients')

    #: this token is used for confirm and unsubscribe
    token = Column(Text, nullable=False, default=random_token)

    #: when recipients are added, they are unconfirmed. At this point they get
    #: one e-mail with a confirmation link. If they ignore said e-mail they
    #: should not get another one.
    confirmed = Column(Boolean, nullable=False, default=False)

    @declared_attr
    def __table_args__(cls):
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

    def confirm(self, token):
        if self.token != token:
            return False

        self.confirmed = True
        return True

    def unsubscribe(self, token):
        if self.token != token:
            return False

        session = object_session(self)
        session.delete(self)
        session.flush()

        return True
