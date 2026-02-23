from __future__ import annotations

from collections.abc import Iterable
from onegov.core.crypto import random_token
from onegov.core.utils import toggle
from onegov.user import log
from onegov.user.models import User
from onegov.user.errors import (
    AlreadyActivatedError,
    ExistingUserError,
    InsecurePasswordError,
    InvalidActivationTokenError,
    UnknownUserError,
)
from sqlalchemy import or_, exists, text


from typing import overload, Any, TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Collection, Mapping
    from onegov.core.request import CoreRequest
    from onegov.user import UserGroup
    from sqlalchemy.orm import Query, Session
    from typing import Self
    from uuid import UUID


_T = TypeVar('_T')


MIN_PASSWORD_LENGTH = 10


@overload
def as_set(value: Iterable[_T]) -> set[_T]: ...
@overload
def as_set(value: _T) -> set[_T]: ...


def as_set(value: Any) -> set[Any]:
    if isinstance(value, set):
        return value
    if isinstance(value, str):
        return {value}
    if isinstance(value, Iterable):
        return set(value)

    return {value}


@overload
def as_dictionary_of_sets(
    d: Mapping[str, _T | Iterable[_T] | None]
) -> dict[str, set[_T]]: ...


@overload
def as_dictionary_of_sets(d: Mapping[str, Any]) -> dict[str, set[Any]]: ...


def as_dictionary_of_sets(d: Mapping[str, Any]) -> dict[str, set[Any]]:
    return {
        k: (set() if v is None else as_set(v))
        for k, v in d.items()
    }


class UserCollection:
    """ Manages a list of users.

    Use it like this::

        from onegov.user import UserCollection
        users = UserCollection(session)

    """

    def __init__(self, session: Session, **filters: Any):
        self.session = session
        self.filters = as_dictionary_of_sets(filters)

    def __getattr__(self, name: str) -> set[Any] | None:
        if name not in self.filters:
            raise AttributeError(name)

        return self.filters[name]

    def for_filter(self, **filters: Any) -> Self:
        toggled = {
            key: toggle(self.filters.get(key, set()), value)
            for key, value in filters.items()
        }

        for key in self.filters:
            if key not in toggled:
                toggled[key] = self.filters[key]

        return self.__class__(self.session, **toggled)

    def query(self) -> Query[User]:
        """ Returns a query using :class:`onegov.user.models.User`. With
        the current filters applied.

        """
        query = self.session.query(User)

        for key, values in self.filters.items():
            if values:
                apply = getattr(self, f'apply_{key}_filter', self.apply_filter)
                query = apply(query, key, values)

        return query

    def apply_filter(
        self,
        query: Query[User],
        key: str,
        values: Collection[Any]
    ) -> Query[User]:

        if '' in values:
            return query.filter(
                or_(
                    getattr(User, key).in_(values),
                    getattr(User, key).is_(None)
                )
            )

        return query.filter(getattr(User, key).in_(values))

    def apply_tag_filter(
        self,
        query: Query[User],
        key: str,
        values: Iterable[str]
    ) -> Query[User]:
        return query.filter(or_(
            *(User.data['tags'].contains((v, )) for v in values)
        ))

    def add(
        self,
        username: str,
        password: str,
        role: str,
        data: dict[str, Any] | None = None,
        second_factor: dict[str, Any] | None = None,
        active: bool = True,
        realname: str | None = None,
        phone_number: str | None = None,
        signup_token: str | None = None,
        groups: list[UserGroup] | None = None
    ) -> User:
        """ Add a user to the collection.

        The arguments given to this function are the attributes of the
        :class:`~onegov.user.models.User` class with the same name.
        """
        assert username
        assert password
        assert role

        if self.exists(username):
            raise ExistingUserError(username)

        # FIXME: __init__ should probably be explicit with data_properties
        #        like phone_number, for SQLAlchemy 2.0 we will probably do
        #        that transformation anyways unless we want to switch all
        #        the models to being dataclasses
        user = User(
            username=username,
            password=password,
            role=role,
            data=data,
            second_factor=second_factor,
            active=active,
            realname=realname,
            signup_token=signup_token,
            groups=groups or [],
            phone_number=phone_number
        )

        self.session.add(user)
        self.session.flush()

        return user

    @property
    def tags(self) -> tuple[str, ...]:
        """ All available tags. """
        records = self.session.execute(text("""
            SELECT DISTINCT tags FROM (
                SELECT jsonb_array_elements(data->'tags') AS tags
                FROM users
            ) AS elements ORDER BY tags
        """))

        return tuple(tag for tag, in records)

    @property
    def sources(self) -> tuple[str, ...]:
        """ All available sources. """

        records = self.session.query(User.source)
        records = records.filter(User.source.isnot(None))
        records = records.order_by(User.source).distinct()

        return tuple(source for source, in records)

    @property
    def usernames(self) -> tuple[tuple[str, str], ...]:
        """ All available usernames. """
        records = self.session.execute(text("""
            SELECT username, initcap(realname)
            FROM users ORDER BY COALESCE(initcap(realname), username)
        """))

        return tuple((username, realname) for username, realname in records)

    def usernames_by_tags(self, tags: list[str]) -> tuple[str, ...]:
        """ All usernames where the user's tags match at least one tag
        from the given list.

        """

        records = self.session.execute(text("""
            SELECT username FROM users
            WHERE data->'tags' ?| :tags
        """), {'tags': tags})

        return tuple(username for username, in records)

    def exists(self, username: str) -> bool:
        """ Returns True if the given username exists.

        This function does not actually load a user, so it is the quickest
        way to find out if a user exists. It should be used if you don't
        care about finding out anything about the user.

        """
        query = self.session.query(exists().where(
            User.username == username))

        return query.scalar()

    def by_id(self, id: UUID) -> User | None:
        """ Returns the user by the internal id.

        Use this if you need to refer to a user by path. Usernames are not
        the correct way, since they allow for user enumeration.

        """

        return self.query().filter(User.id == id).first()

    def by_username(self, username: str) -> User | None:
        """ Returns the user by username. """
        return self.query().filter(User.username == username).first()

    def by_source_id(self, source: str, source_id: str) -> User | None:
        """ Returns the user by source and source_id. """
        return self.query().filter_by(
            source=source, source_id=source_id).first()

    def by_username_and_password(
        self,
        username: str,
        password: str
    ) -> User | None:
        """ Returns the user by username and password.

        Note that although the password can be empty on the user, this function
        will not query for empty passwords as an added security measure.

        Apart from that everything is fair game though, as it is not the job
        of onegov.user to enforce a password policy.

        """
        user = self.by_username(username)

        if user and password and user.is_matching_password(password):
            return user
        else:
            return None

    def by_roles(self, role: str, *roles: str) -> Query[User]:
        """ Queries the users by roles. """
        return self.query().filter(User.role.in_([role, *roles]))

    def by_signup_token(self, signup_token: str) -> Query[User]:
        return self.query().filter_by(signup_token=signup_token)

    def register(
        self,
        username: str,
        password: str,
        request: CoreRequest,
        role: str = 'member',
        signup_token: str | None = None
    ) -> User:
        """ Registers a new user.

        The so created user needs to activated with a token before it becomes
        active. Use the activation_token in the data dictionary together
        with the :meth:`activate_with_token` function.

        You probably want to use the provided
        :class:`~onegov.user.forms.registration_form.RegistrationForm` in
        conjunction with :class:`~onegov.user.auth.Auth` as it includes a lot
        of extras like signup links and robots protection.

        """

        assert username

        # we could implement a proper password policy, but a min-length of
        # of eight characters is a good start. What we don't want is someone
        # registering a user with a password of one character.
        if len(password) < MIN_PASSWORD_LENGTH:
            raise InsecurePasswordError()

        if self.by_username(username):
            raise ExistingUserError('{} already exists'.format(username))

        log.info('Registration by {} ({})'.format(
            request.client_addr, username))

        return self.add(
            username=username,
            password=password,
            role=role,
            data={
                'activation_token': random_token()
            },
            active=False,
            signup_token=signup_token
        )

    def activate_with_token(self, username: str, token: object) -> None:
        """ Activates the user if the given token matches the verification
        token stored in the data dictionary.

        """
        user = self.by_username(username)

        if not user:
            raise UnknownUserError(f'{username} does not exist')

        if user.active:
            raise AlreadyActivatedError(f'{username} already active')

        if user.data.get('activation_token', object()) != token:
            raise InvalidActivationTokenError(f'{token} is invalid')

        del user.data['activation_token']
        user.active = True
        self.session.flush()

    def by_yubikey(self, token: str, active_only: bool = True) -> User | None:
        """ Returns the user with the given yubikey token.

        Only considers active users by default.

        """

        token = token[:12]

        query = self.query().filter(User.active == True)

        # TODO: We could implement this in postgres using the JSON
        #       operators, which should be a lot faster
        for user in query.all():
            if not user.second_factor:
                continue

            if user.second_factor.get('type') != 'yubikey':
                continue

            if user.second_factor.get('data') == token:
                return user
        return None

    def delete(self, username: str) -> None:
        """ Deletes the user if it exists.

        If the user does not exist, an
        :class:`onegov.user.errors.UnknownUserError` is raised.

        """
        user = self.by_username(username)

        if not user:
            raise UnknownUserError('user {} does not exist'.format(username))

        self.session.delete(user)
        self.session.flush()
