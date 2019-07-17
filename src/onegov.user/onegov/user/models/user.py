from datetime import datetime
from onegov.core.crypto import hash_password, verify_password
from onegov.core.orm import Base
from onegov.core.orm.mixins import data_property, TimestampMixin
from onegov.core.orm.types import JSON, UUID, LowercaseText
from onegov.core.security import forget, remembered
from onegov.core.utils import is_valid_yubikey_format
from onegov.core.utils import remove_repeated_spaces
from onegov.core.utils import yubikey_otp_to_serial
from onegov.search import ORMSearchable
from onegov.user.models.group import UserGroup
from sqlalchemy import Boolean, Column, Index, Text, func, ForeignKey
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import backref, deferred, relationship
from uuid import uuid4


class User(Base, TimestampMixin, ORMSearchable):
    """ Defines a generic user. """

    __tablename__ = 'users'

    #: the type of the item, this can be used to create custom polymorphic
    #: subclasses of this class. See
    #: `<http://docs.sqlalchemy.org/en/improve_toc/\
    #: orm/extensions/declarative/inheritance.html>`_.
    type = Column(Text, nullable=True)

    __mapper_args__ = {
        'polymorphic_on': type
    }

    es_properties = {
        'username': {'type': 'text'},
        'realname': {'type': 'text'},
        'userprofile': {'type': 'text'}
    }
    es_public = False

    @property
    def es_suggestion(self):
        return (self.realname or self.username, self.username)

    @property
    def userprofile(self):
        data = []

        if self.data:
            for value in self.data.values():
                if value and isinstance(value, str):
                    data.append(value)

        return data

    #: the user id is a uuid because that's more secure (no id guessing)
    id = Column(UUID, nullable=False, primary_key=True, default=uuid4)

    #: the username may be any string, but will usually be an email address
    username = Column(LowercaseText, unique=True, nullable=False)

    #: the password is stored with the hashing algorithm defined by onegov.core
    password_hash = Column(Text, nullable=False)

    #: the role is relevant for security in onegov.core
    role = Column(Text, nullable=False)

    #: the group this user belongs to
    group_id = Column(UUID, ForeignKey(UserGroup.id), nullable=True)
    group = relationship(
        UserGroup, backref=backref('users', lazy='dynamic')
    )

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

    #: Third-party authentication provider data if enabled. Users are only
    #: ever associated with one authentication provider at once.
    #:
    #: Additionally, authentication may be either required or optional, if it
    #: is configured at all. If the configured authentication is optional, the
    #: user may login using it, but may also fall back to username/password.
    #:
    #: If the configured authentication is required, then the user may only
    #: authenticate trough the required authentication. The username/password
    #: combination won't work in this case.
    #:
    #: This allows for regular users registered with a third-party provider to
    #: be forced to use it, while some admin may have an optional login with
    #: an escape hatch, should the third-party provider be down or faulty.
    #:
    #: Example content::
    #:
    #:      {
    #:          'name': 'kerberos',
    #:          'fields': {'username': 'user@EXAMPLE.ORG'},
    #:          'required': True
    #:      }
    #:
    #: Note that the authentication provider is configured once per application
    #: instance, there cannot be multiple auth providers of the same type one
    #: a single application.
    authentication_provider = Column(JSON, nullable=True)

    #: true if the user is active
    active = Column(Boolean, nullable=False, default=True)

    #: the signup token used by the user
    signup_token = Column(Text, nullable=True, default=None)

    __table_args__ = (
        Index('lowercase_username', func.lower(username), unique=True),
    )

    @hybrid_property
    def title(self):
        """ Returns the realname or the username of the user, depending on
        what's available first. """
        if self.realname is None:
            return self.username

        if self.realname.strip():
            return self.realname

        return self.username

    @title.expression
    def title(cls):
        return func.coalesce(
            func.nullif(func.trim(cls.realname), ''), cls.username
        )

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

    @classmethod
    def get_initials(cls, username, realname=None):
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
        if realname is None or not realname.strip():
            username = username.split('@')[0]
            parts = username.split('.')[:2]

        # for real names split by space and assume that with more than one
        # part that the first and last part are the most important to get rid
        # of middlenames
        else:
            parts = remove_repeated_spaces(realname).split(' ')

            if len(parts) > 2:
                parts = (parts[0], parts[-1])

        return ''.join(p[0] for p in parts).upper()

    @property
    def initials(self):
        return self.get_initials(self.username, self.realname)

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

    #: sessions of this user
    sessions = data_property()

    #: tags of this user
    tags = data_property()

    #: the phone number of this user
    phone_number = data_property()

    def cleanup_sessions(self, request):
        """ Removes stored sessions not valid anymore. """

        self.sessions = self.sessions or {}
        for session_id in list(self.sessions.keys()):
            if not remembered(request.app, session_id):
                del self.sessions[session_id]

    def save_current_session(self, request):
        """ Stores the current browser session. """

        self.sessions = self.sessions or {}
        self.sessions[request.browser_session._token] = {
            'address': request.client_addr,
            'timestamp': datetime.utcnow().isoformat(),
            'agent': request.user_agent
        }

        self.cleanup_sessions(request)

    def remove_current_session(self, request):
        """ Removes the current browser session. """

        token = request.browser_session._token
        if self.sessions and token and token in self.sessions:
            del self.sessions[token]

        self.cleanup_sessions(request)

    def logout_all_sessions(self, request):
        """ Terminates all open browser sessions. """

        self.sessions = self.sessions or {}
        for session_id in self.sessions:
            forget(request.app, session_id)

        self.cleanup_sessions(request)
