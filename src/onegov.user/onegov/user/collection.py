from collections import Iterable
from onegov.core.crypto import random_token
from onegov.user import log
from onegov.user.model import User
from onegov.user.errors import (
    AlreadyActivatedError,
    ExistingUserError,
    InsecurePasswordError,
    InvalidActivationTokenError,
    UnknownUserError,
)
from sqlalchemy import sql


MIN_PASSWORD_LENGTH = 8


def as_set(value):
    if isinstance(value, set):
        return value
    if isinstance(value, str):
        return {value}
    if isinstance(value, Iterable):
        return set(value)

    return {value}


def as_dictionary_of_sets(d):
    return {
        k: (v if v is None else as_set(v))
        for k, v in d.items()
    }


def toggle(collection, item):
    if item is None:
        return collection

    if item in collection:
        return collection - {item}
    else:
        return collection | {item}


class UserCollection(object):
    """ Manages a list of users.

    Use it like this::

        from onegov.user import UserCollection
        users = UserCollection(session)

    """

    def __init__(self, session, **filters):
        self.session = session
        self.filters = as_dictionary_of_sets(filters)

    def __getattr__(self, name):
        if name not in self.filters:
            raise AttributeError(name)

        return self.filters[name]

    def for_filter(self, **filters):
        toggled = {
            key: toggle(self.filters.get(key, set()), value)
            for key, value in filters.items()
        }

        for key in self.filters:
            if key not in toggled:
                toggled[key] = self.filters[key]

        return self.__class__(self.session, **toggled)

    def query(self):
        """ Returns a query using :class:`onegov.user.model.User`. With
        the current filters applied.

        """
        query = self.session.query(User)

        for key, values in self.filters.items():
            if values:
                query = query.filter(getattr(User, key).in_(values))

        return query

    def add(self, username, password, role,
            data=None, second_factor=None, active=True, realname=None):
        """ Add a user to the collection.

            The arguments given to this function are the attributes of the
            :class:`~onegov.user.models.User` class with the same name.
        """
        assert username and password and role

        if self.exists(username):
            raise ExistingUserError(username)

        user = User(
            username=username,
            password=password,
            role=role,
            data=data,
            second_factor=second_factor,
            active=active,
            realname=realname
        )

        self.session.add(user)
        self.session.flush()

        return user

    def exists(self, username):
        """ Returns True if the given username exists.

        This function does not actually load a user, so it is the quickest
        way to find out if a user exists. It should be used if you don't
        care about finding out anything about the user.

        """
        query = self.session.query(sql.exists().where(
            User.username == username))

        return query.scalar()

    def by_id(self, id):
        """ Returns the user by the internal id.

        Use this if you need to refer to a user by path. Usernames are not
        the correct way, since they allow for user enumeration.

        """

        return self.query().filter(User.id == id).first()

    def by_username(self, username):
        """ Returns the user by username. """
        return self.query().filter(User.username == username).first()

    def by_username_and_password(self, username, password):
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

    def by_roles(self, role, *roles):
        """ Queries the users by roles. """
        roles = [role] + list(roles)
        return self.query().filter(User.role.in_(roles))

    def register(self, username, password, request, role='member'):
        """ Registers a new user.

        The so created user needs to activated with a token before it becomes
        active. Use the activation_token in the data dictionary together
        with the :meth:`activate_with_token` function.

        """

        assert username

        # we could implement a proper password policy, but a min-length of
        # of eight characters is a good start. What we don't want is someone
        # registering a user with a password of one character.
        if len(password) < MIN_PASSWORD_LENGTH:
            raise InsecurePasswordError()

        if self.by_username(username):
            raise ExistingUserError("{} already exists".format(username))

        log.info("Registration by {} ({})".format(
            request.client_addr, username))

        return self.add(
            username=username,
            password=password,
            role=role,
            data={
                'activation_token': random_token()
            },
            active=False
        )

    def activate_with_token(self, username, token):
        """ Activates the user if the given token matches the verification
        token stored in the data dictionary.

        """
        user = self.by_username(username)

        if not user:
            raise UnknownUserError("{} does not exist".format(username))

        if user.active:
            raise AlreadyActivatedError("{} already active".format(username))

        if user.data.get('activation_token', object()) != token:
            raise InvalidActivationTokenError("{} is invalid".format(token))

        del user.data['activation_token']
        user.active = True
        self.session.flush()

    def by_yubikey(self, token, active_only=True):
        """ Returns the user with the given yubikey token.

        Only considers active users by default.

        """

        token = token[:12]

        query = self.query().filter(User.active == True)

        for user in query.all():
            if not user.second_factor:
                continue

            if user.second_factor.get('type') != 'yubikey':
                continue

            if user.second_factor.get('data') == token:
                return user

    def delete(self, username):
        """ Deletes the user if it exists.

        If the user does not exist, an
        :class:`onegov.user.errors.UnknownUserError` is raised.

        """
        user = self.by_username(username)

        if not user:
            raise UnknownUserError("user {} does not exist".format(username))

        self.session.delete(user)
        self.session.flush()
