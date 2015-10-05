import morepath
from onegov.core.utils import relative_url
from onegov.user import log
from onegov.user.collection import UserCollection


class Auth(object):
    """ Defines a model for authentication methods like login/logout.
    Applications should use this model to implement authentication views.

    """

    identity_class = morepath.Identity

    def __init__(self, session, application_id, to='/'):
        assert application_id  # may not be empty!

        self.session = session
        self.application_id = application_id

        # never redirect to an external page, this might potentially be used
        # to trick the user into thinking he's on our page after entering his
        # password and being redirected to a phising site.
        self.to = relative_url(to)

    @classmethod
    def from_app(cls, app, to='/'):
        return cls(app.session(), app.application_id, to)

    @classmethod
    def from_request(cls, request, to='/'):
        return cls.from_app(request.app)

    @property
    def users(self):
        return UserCollection(self.session)

    def login(self, username, password, client='unknown'):
        """ Takes the given username and password and matches them against
        the users collection.

        :meth:`login_to` should be the preferred method in most cases, as it
        sets up automatic logging of login attempts and provides optional
        login/logout messages.

        :return: An identity bound to the ``application_id`` if the username
        and password match.

        """

        user = self.users.by_username_and_password(username, password)

        if user is None:
            log.info("Failed login by {} ({})".format(client, username))
            return None

        log.info("Successful login by {} ({})".format(client, username))

        return self.identity_class(
            userid=user.username,
            role=user.role,
            application_id=self.application_id
        )

    def login_to(self, username, password, request):
        """ Matches the username and password against the users collection,
        just like :meth:`login`. Unlike said method it returns no identity
        however, instead a redirect response is returned which will remember
        the identity.

        :return: A redirect response to ``self.to`` with the identity
        remembered as a cookie. If not successful, None is returned.

        """

        identity = self.login(username, password, request.client_addr)

        if identity is None:
            return None

        response = morepath.redirect(self.to)
        morepath.remember_identity(response, request, identity)

        return response

    def logout_to(self, request):
        """ Logs the current user out and redirects to ``self.to``.

        :return: A response redirecting to ``self.to`` with the identity
        forgotten.

        """

        response = morepath.redirect(self.to)
        morepath.forget_identity(response, request)

        return response
