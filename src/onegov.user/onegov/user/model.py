from onegov.core.crypto import hash_password, verify_password
from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import JSON, UUID
from onegov.core.utils import remove_repeated_spaces
from onegov.user.utils import is_valid_yubikey_format
from onegov.user.utils import yubikey_otp_to_serial
from sqlalchemy import Boolean, Column, Text, func
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

    #: the real name of the user for display (use the :attr:`name` property
    #: to automatically get the name or the username)
    realname = Column(Text, nullable=True)

    #: extra data that may be stored with this user, the format and content
    #: of this data is defined by the consumer of onegov.user
    #: by default, this data is only loaded by request, so if you need to
    #: load a lot of data columns, do something like this::
    #:
    #:     session.query(User).options(undefer("data"))
    #:
    data = deferred(Column(JSON, nullable=True))

    #: two-factor authentication schemes are enabled with this property
    #: if no two-factor auth is used, the value is NULL, if one *is* used,
    #: there should be a dictionary with the type of the two-factor
    #: authentication as well as custom values required by the two-factor
    #: implementation.
    #:
    #: e.g.::
    #:
    #:      {
    #:          'type': 'yubikey',
    #:          'data': 'ccccccbcgujh'
    #:      }
    #:
    #: Note that 'data' could also be a nested dictionary!
    #:
    second_factor = Column(JSON, nullable=True)

    #: true if the user is active
    active = Column(Boolean, nullable=False, default=True)

    @hybrid_property
    def title(self):
        """ Returns the realname or the username of the user, depending on
        what's available first. """
        return self.realname or self.username

    @title.expression
    def title(cls):
        return func.coalesce(cls.realname, cls.username)

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

    @property
    def initials(self):
        """ Takes the name and returns initials which are at most two
        characters wide.

        Examples:

        admin => A
        nathan.drake@example.org => ND
        Victor Sullivan => VS
        Charles Montgomery Burns => CB

        """

        # for e-mail addresses assume the dot splits the name and use
        # the first two parts of said split (probably won't have a middle
        # name in the e-mail address)
        if not self.realname:
            username = self.username.split('@')[0]
            parts = username.split('.')[:2]

        # for real names split by space and assume that with more than one
        # part that the first and last part are the most important to get rid
        # of middlenames
        else:
            parts = remove_repeated_spaces(self.realname).split(' ')

            if len(parts) > 2:
                parts = (parts[0], parts[-1])

        return ''.join(p[0] for p in parts).upper()

    @property
    def has_yubikey(self):
        if not self.second_factor:
            return False

        return self.second_factor.get('type') == 'yubikey'

    @property
    def yubikey(self):
        if not self.has_yubikey:
            return None

        return self.second_factor.get('data')

    @yubikey.setter
    def yubikey(self, yubikey):
        if not yubikey:
            self.second_factor = None
        else:
            assert is_valid_yubikey_format(yubikey)

            self.second_factor = {
                'type': 'yubikey',
                'data': yubikey[:12]
            }

    @property
    def yubikey_serial(self):
        """ Returns the yubikey serial of the yubikey associated with this
        user (if any).

        """

        yubikey = self.yubikey

        return yubikey and yubikey_otp_to_serial(yubikey) or None
