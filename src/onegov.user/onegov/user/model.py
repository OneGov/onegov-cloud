from onegov.core.crypto import hash_password, verify_password
from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import JSON, UUID
from sqlalchemy import Column, Text
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import deferred
from uuid import uuid4


class User(Base, TimestampMixin):
    """ Defines a generic user. """

    __tablename__ = 'users'

    #: the user id is a uuid because that's more secure (no id guessing)
    id = Column(UUID, nullable=False, primary_key=True, default=uuid4)

    #: the username may be any string, but will usually be an email address
    username = Column(Text, unique=True, nullable=False)

    #: the password is stored with the hashing algorithm defined by onegov.core
    password_hash = Column(Text, nullable=False)

    #: the role is relevant for security in onegov.core
    role = Column(Text, nullable=False)

    #: extra data that may be stored with this user, the format and content
    #: of this data is defined by the consumer of onegov.user
    #: by default, this data is only loaded by request, so if you need to
    #: load a lot of data columns, do something like this::
    #:
    #:     session.query(User).options(undefer("data"))
    #:
    data = deferred(Column(JSON, nullable=True))

    @hybrid_property
    def password(self):
        """ An alias for :attr:`password_hash`. """
        return self.password_hash

    @password.setter
    def password(self, value):
        """ When set, the given password in cleartext is hashed using
        onegov.core's default hashing algorithm.

        """
        self.password_hash = hash_password(value)

    def is_matching_password(self, password):
        """ Returns True if the given password (cleartext) matches the
        stored password hash.

        """
        return verify_password(password, self.password_hash)
