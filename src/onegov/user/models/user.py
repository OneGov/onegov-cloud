from __future__ import annotations

from onegov.core.crypto import hash_password, verify_password
from onegov.core.orm import Base
from onegov.core.orm.mixins import data_property, dict_property, TimestampMixin
from onegov.core.orm.types import JSON, UUID, LowercaseText, UTCDateTime
from onegov.core.security import forget, remembered
from onegov.core.utils import is_valid_yubikey_format
from onegov.core.utils import remove_repeated_dots
from onegov.core.utils import remove_repeated_spaces
from onegov.core.utils import yubikey_otp_to_serial
from onegov.search import ORMSearchable
from onegov.user.i18n import _
from onegov.user.models.group import UserGroup, group_association_table
from sedate import utcnow
from sqlalchemy import Boolean, Column, Index, Text, func
from sqlalchemy import UniqueConstraint
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import deferred, relationship
from uuid import uuid4, UUID as UUIDType


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Sequence
    from datetime import datetime
    from onegov.core.framework import Framework
    from onegov.core.request import CoreRequest
    from onegov.core.types import AppenderQuery
    from onegov.user import RoleMapping
    from typing_extensions import TypedDict

    class SessionDict(TypedDict):
        address: str | None
        timestamp: str
        agent: str | None


class User(Base, TimestampMixin, ORMSearchable):
    """ Defines a generic user. """

    __tablename__ = 'users'

    #: the type of the item, this can be used to create custom polymorphic
    #: subclasses of this class. See
    #: `<https://docs.sqlalchemy.org/en/improve_toc/\
    #: orm/extensions/declarative/inheritance.html>`_.
    type: Column[str] = Column(
        Text, nullable=False, default=lambda: 'generic')

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'generic',
    }

    fts_type_title = _('Users')
    fts_title_property = 'title'
    fts_properties = {
        'username': {'type': 'text', 'weight': 'A'},
        'realname': {'type': 'text', 'weight': 'A'},
        'userprofile': {'type': 'text', 'weight': 'B'}
    }
    fts_public = False

    @property
    def fts_suggestion(self) -> tuple[str, str]:
        return (self.realname or self.username, self.username)

    @property
    def userprofile(self) -> list[str]:
        if not self.data:
            return []

        return [
            value
            for value in self.data.values()
            if value and isinstance(value, str)
        ]

    #: the user id is a uuid because that's more secure (no id guessing)
    id: Column[UUIDType] = Column(
        UUID,  # type:ignore[arg-type]
        nullable=False,
        primary_key=True,
        default=uuid4
    )

    #: the username may be any string, but will usually be an email address
    username: Column[str] = Column(
        LowercaseText,
        unique=True,
        nullable=False
    )

    #: the password is stored with the hashing algorithm defined by onegov.core
    password_hash: Column[str] = Column(Text, nullable=False)

    #: the role is relevant for security in onegov.core
    role: Column[str] = Column(Text, nullable=False)

    #: the group this user belongs to
    groups: relationship[list[UserGroup]] = relationship(
        UserGroup,
        secondary=group_association_table,
        back_populates='users',
        passive_deletes=True,
    )

    #: the real name of the user for display (use the :attr:`name` property
    #: to automatically get the name or the username)
    realname: Column[str | None] = Column(Text, nullable=True)

    #: extra data that may be stored with this user, the format and content
    #: of this data is defined by the consumer of onegov.user
    #: by default, this data is only loaded by request, so if you need to
    #: load a lot of data columns, do something like this::
    #:
    #:     session.query(User).options(undefer("data"))
    #:
    data: Column[dict[str, Any]] = deferred(Column(JSON, nullable=True))

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
    second_factor: Column[dict[str, Any] | None] = Column(
        JSON,
        nullable=True
    )

    #: A string describing where the user came from, None if internal.
    #
    #: Internal users may login using a password, which they may also change.
    #
    #: External users may not login using a password, nor can they ask for one.
    #
    #: A user can technically come from changing providers - the source refers
    #: to the last provider he used.
    source: Column[str | None] = Column(Text, nullable=True, default=None)

    #: A string describing the user id on the source, which is an id that is
    #: supposed never change (unlike the username, which may change).
    #:
    #: If set, the source_id is unique per source.
    source_id: Column[str | None] = Column(Text, nullable=True, default=None)

    #: true if the user is active
    active: Column[bool] = Column(Boolean, nullable=False, default=True)

    #: timestamp of the last successful login
    last_login: Column[datetime | None] = Column(
        UTCDateTime, nullable=True, default=None
    )

    #: the signup token used by the user
    signup_token: Column[str | None] = Column(
        Text,
        nullable=True,
        default=None
    )

    __table_args__ = (
        Index('lowercase_username', func.lower(username), unique=True),
        UniqueConstraint('source', 'source_id', name='unique_source_id'),
    )

    #: the role mappings associated with this user
    role_mappings: relationship[AppenderQuery[RoleMapping]] = relationship(
        'RoleMapping',
        back_populates='user',
        lazy='dynamic'
    )

    if TYPE_CHECKING:
        # HACK: This probably won't be necessary in SQLAlchemy 2.0, but
        #       for the purposes of type checking these behave like a
        #       Column[str]
        title: Column[str]
        password: Column[str]
        api_keys: relationship[list[Any]]
    else:
        @hybrid_property
        def title(self) -> str:
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

    def is_matching_password(self, password: str) -> bool:
        """ Returns True if the given password (cleartext) matches the
        stored password hash.

        """
        return verify_password(password, self.password_hash)

    @classmethod
    def get_initials(cls, username: str, realname: str | None = None) -> str:
        """ Takes the name and returns initials which are at most two
        characters wide.

        Examples:

        admin => A
        nathan.drake@example.org => ND
        Victor Sullivan => VS
        Charles Montgomery Burns => CB

        """
        parts: Sequence[str]

        # for e-mail addresses assume the dot splits the name and use
        # the first two parts of said split (probably won't have a middle
        # name in the e-mail address)
        if realname is None or not realname.strip():
            username = username.split('@')[0]
            parts = remove_repeated_dots(username.strip('.')).split('.')[:2]

        # for real names split by space and assume that with more than one
        # part that the first and last part are the most important to get rid
        # of middlenames
        else:
            parts = remove_repeated_spaces(realname.strip()).split(' ')

            if len(parts) > 2:
                parts = (parts[0], parts[-1])

        return ''.join(p[0] for p in parts if p).upper() or '?'

    @property
    def initials(self) -> str:
        return self.get_initials(self.username, self.realname)

    @property
    def has_yubikey(self) -> bool:
        if not self.second_factor:
            return False

        return self.second_factor.get('type') == 'yubikey'

    @property
    def yubikey(self) -> str | None:
        if not self.has_yubikey:
            return None

        assert self.second_factor is not None
        return self.second_factor.get('data')

    @yubikey.setter
    def yubikey(self, yubikey: str | None) -> None:
        if not yubikey:
            self.second_factor = None
        else:
            assert is_valid_yubikey_format(yubikey)

            self.second_factor = {
                'type': 'yubikey',
                'data': yubikey[:12]
            }

    @property
    def yubikey_serial(self) -> int | None:
        """ Returns the yubikey serial of the yubikey associated with this
        user (if any).

        """

        yubikey = self.yubikey

        return yubikey and yubikey_otp_to_serial(yubikey) or None

    @property
    def mtan_phone_number(self) -> str | None:
        if not self.second_factor:
            return None

        if self.second_factor.get('type') != 'mtan':
            return None

        return self.second_factor.get('data')

    #: sessions of this user
    sessions: dict_property[dict[str, SessionDict] | None] = data_property()

    #: tags of this user
    tags: dict_property[list[str] | None] = data_property()

    #: the phone number of this user
    phone_number: dict_property[str | None] = data_property()

    def cleanup_sessions(self, app: Framework) -> None:
        """ Removes stored sessions not valid anymore. """

        self.sessions = self.sessions or {}
        for session_id in list(self.sessions.keys()):
            if not remembered(app, session_id):
                del self.sessions[session_id]

    def save_current_session(self, request: CoreRequest) -> None:
        """ Stores the current browser session. """

        self.sessions = self.sessions or {}
        self.sessions[request.browser_session._token] = {
            'address': request.client_addr,
            'timestamp': utcnow().replace(tzinfo=None).isoformat(),
            'agent': request.user_agent
        }

        self.cleanup_sessions(request.app)

    def remove_current_session(self, request: CoreRequest) -> None:
        """ Removes the current browser session. """

        token = request.browser_session._token
        if self.sessions and token and token in self.sessions:
            del self.sessions[token]

        self.cleanup_sessions(request.app)

    def logout_all_sessions(self, app: Framework) -> int:
        """ Terminates all open browser sessions. """

        self.sessions = self.sessions or {}
        count = len(self.sessions)
        for session_id in self.sessions:
            forget(app, session_id)

        self.cleanup_sessions(app)

        return count
