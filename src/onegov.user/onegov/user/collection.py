from onegov.user.model import User
from onegov.user.errors import UnknownUserError
from sqlalchemy import sql


class UserCollection(object):
    """ Manages a list of users.

    Use it like this::

        from onegov.user import UserCollection
        users = UserCollection(session)

    """

    def __init__(self, session):
        self.session = session

    def query(self):
        """ Returns a query using :class:`onegov.user.model.User`. """
        return self.session.query(User)

    def add(self, username, password, role, data=None):
        """ Add a user to the collection.

            :username:
                Must be a unique string and may not be empty.

            :password:
                Must be a non-empty string.

            :role:
                Must be a non-empty string. The meaning of roles is not defined
                in `onegov.user` instead the role is usually defined by
                :mod:`onegov.core.security.roles`.
        """
        assert username and password and role

        user = User(username=username, password=password, role=role, data=data)

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
