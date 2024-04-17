import morepath

from datetime import datetime
from itsdangerous import URLSafeSerializer, BadSignature

from onegov.core.utils import relative_url
from onegov.user import log
from onegov.user.collections import UserCollection
from onegov.user.errors import ExpiredSignupLinkError
from onegov.user.auth.second_factor import SECOND_FACTORS


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from morepath.authentication import Identity, NoIdentity
    from onegov.core.request import CoreRequest
    from onegov.user import User, UserApp
    from onegov.user.forms import RegistrationForm
    from typing_extensions import Self, TypedDict
    from webob import Response

    class SignupToken(TypedDict):
        role: str
        max_uses: int
        expires: int


class Auth:
    """ Defines a model for authentication methods like login/logout.
    Applications should use this model to implement authentication views.

    """

    identity_class = morepath.Identity

    def __init__(
        self,
        app: 'UserApp',
        # FIXME: For now we allow None, because purl.URL will default
        #        to '/' for None, which is used by relative_url, but
        #        we should probably be more vigilant about this...
        to: str | None = '/',
        skip: bool = False,
        signup_token: str | None = None,
        signup_token_secret: str | None = None
    ):

        self.app = app
        self.session = app.session()
        self.application_id = app.application_id

        self.signup_token = signup_token
        self.signup_token_secret = signup_token_secret or getattr(
            app, 'identity_secret', None)

        # never redirect to an external page, this might potentially be used
        # to trick the user into thinking he's on our page after entering his
        # password and being redirected to a phishing site.
        self.to = relative_url(to)
        self.skip = skip

        # initialize nth factors
        self.factors = {}

        for type, cls in SECOND_FACTORS.items():
            obj = cls.configure(**cls.args_from_app(app))

            if obj is not None:
                self.factors[type] = obj

    @classmethod
    def from_request(
        cls,
        request: 'CoreRequest',
        to: str | None = '/',
        skip: bool = False,
        signup_token: str | None = None
    ) -> 'Self':
        return cls(
            request.app,  # type:ignore[arg-type]
            to,
            skip,
            signup_token
        )

    @classmethod
    def from_request_path(
        cls,
        request: 'CoreRequest',
        skip: bool = False,
        signup_token: str | None = None
    ) -> 'Self':
        return cls.from_request(
            request, request.transform(request.path), skip, signup_token)

    @property
    def users(self) -> UserCollection:
        return UserCollection(self.session)

    def redirect(self, request: 'CoreRequest', path: str) -> 'Response':
        return morepath.redirect(request.transform(path))

    def skippable(self, request: 'CoreRequest') -> bool:
        """ Returns true if the login for the current `to` target is optional
        (i.e. it is not required to access the page).

        This should only be used on protected pages as public pages would
        always be skipppable. Therefore it has to be enabled manually by
        specifying `skip=True` on the :class:`Auth` class.

        """

        if not self.skip:
            return False

        # this is the default parameter, we won't skip to it in any case
        if self.to == '/':
            return False

        try:
            return request.has_access_to_url(self.to)
        except KeyError:
            return False

    def is_valid_second_factor(
        self,
        user: 'User',
        second_factor_value: str | None
    ) -> bool:
        """ Returns true if the second factor of the given user is valid. """

        if not user.second_factor:
            return True

        if not second_factor_value:
            return False

        if user.second_factor['type'] in self.factors:
            return self.factors[user.second_factor['type']].is_valid(
                user_specific_config=user.second_factor['data'],
                factor=second_factor_value
            )
        else:
            raise NotImplementedError

    def authenticate(
        self,
        request: 'CoreRequest',
        username: str,
        password: str,
        client: str = 'unknown',
        second_factor: str | None = None,
        skip_providers: bool = False
    ) -> 'User | None':
        """ Takes the given username and password and matches them against the
        users collection. This does not login the user, use :meth:`login_to` to
        accomplish that.

        :param username:
            The username to authenticate.

        :param password:
            The password of the user (clear-text).

        :param client:
            The client address of the user (i.e. his IP address).

        :param second_factor:
            The value of the second factor or None.

        :param skip_providers:
            In special cases where e.g. an LDAP-Provider is a source of users
            but can't offer the password for authentication, you can login
            using the application database.

        :return: The matched user, if successful, or None.

        """

        from onegov.user.integration import UserApp  # circular import

        user = None
        source = None

        if isinstance(self.app, UserApp) and not skip_providers:
            for provider in self.app.providers:
                if not provider.available(self.app):
                    continue
                if provider.kind == 'integrated':
                    user = provider.authenticate_user(
                        request=request,
                        username=username,
                        password=password)

                if user:
                    source = user.source
                    break

        # fall back to default, only if it didn't work otherwise
        user = user or self.users.by_username_and_password(username, password)

        def fail() -> None:
            log.info(f"Failed login by {client} ({username})")
            return None

        if user is None:
            return fail()  # type:ignore[func-returns-value]

        if not user.active:
            return fail()  # type:ignore[func-returns-value]

        # only built-in users currently support second factors
        if source is None:
            try:
                if not self.is_valid_second_factor(user, second_factor):
                    return fail()  # type:ignore[func-returns-value]
            except Exception as e:
                log.info(f'Second factor exception for user {user.username}: '
                         f'{e.args[0]}')
                return None

        # users from external authentication providers may not login using
        # a regular login - if for some reason the source is false (if the
        # authentication system is switched) - the source column has to be
        # set to NULL
        if user.source != source:
            return fail()  # type:ignore[func-returns-value]

        log.info(f"Successful login by {client} ({username})")
        return user

    def as_identity(self, user: 'User') -> 'Identity':
        """ Returns the morepath identity of the given user. """

        return self.identity_class(
            userid=user.username,
            groupid=user.group_id.hex if user.group_id else '',
            role=user.role,
            application_id=self.application_id
        )

    def by_identity(self, identity: 'Identity | NoIdentity') -> 'User | None':
        """ Returns the user record of the given identity. """
        if identity.userid is None:
            return None
        return self.users.by_username(identity.userid)

    def login_to(
        self,
        username: str,
        password: str,
        request: 'CoreRequest',
        second_factor: str | None = None,
        skip_providers: bool = False
    ) -> 'Response | None':
        """ Takes a user login request and remembers the user if the
        authentication completes successfully.

        :param username:
            The username to log in.

        :param password:
            The password to log in (cleartext).

        :param request:
            The request of the user.

        :param second_factor:
            The second factor, if any.

        :skip_providers:
            Pass option skip_providers to skip any configured auth providers.

        :return: A redirect response to ``self.to`` with the identity
        remembered as a cookie. If not successful, None is returned.

        """

        user = self.authenticate(
            request=request,
            username=username,
            password=password,
            client=request.client_addr or 'unknown',
            second_factor=second_factor,
            skip_providers=skip_providers
        )

        if user is None:
            return None

        return self.complete_login(user, request)

    def complete_login(
        self,
        user: 'User',
        request: 'CoreRequest'
    ) -> 'Response':
        """ Takes a user record, remembers its session and returns a proper
        redirect response to complete the login.

        This method is mostly useful inside onegov.user. You probably want
        to use :meth:`complete_login` outside of that.

        """
        assert user is not None

        identity = self.as_identity(user)

        to: str | None
        assert hasattr(request.app, 'redirect_after_login')
        to = request.app.redirect_after_login(identity, request, self.to)
        to = to or self.to

        response = self.redirect(request, to)

        # Rotate the session ID
        if 'session_id' in request.cookies:
            del request.cookies['session_id']
        if 'browser_session' in request.__dict__:
            del request.__dict__['browser_session']

        request.app.remember_identity(response, request, identity)

        if hasattr(request.app, 'on_login'):
            request.app.on_login(request, user)

        user.save_current_session(request)

        return response

    def logout_to(
        self,
        request: 'CoreRequest',
        to: str | None = None
    ) -> 'Response':
        """ Logs the current user out and redirects to ``to`` or ``self.to``.

        :return: A response redirecting to ``self.to`` with the identity
        forgotten.

        """

        user = self.by_identity(request.identity)
        if user is not None:
            user.remove_current_session(request)

        response = self.redirect(request, to or self.to)
        request.app.forget_identity(response, request)

        return response

    def new_signup_token(
        self,
        role: str,
        max_age: int = 24 * 60 * 60,
        max_uses: int = 1
    ) -> str:
        """ Returns a signup token which can be used for users to register
        themselves, directly gaining the given role.

        Signup tokens are recorded on the user to make sure that only the
        requested amount of uses is allowed.

        """
        return self.signup_token_serializer.dumps({
            'role': role,
            'max_uses': max_uses,
            'expires': int(datetime.utcnow().timestamp()) + max_age
        })

    @property
    def signup_token_serializer(self) -> URLSafeSerializer:
        assert self.signup_token_secret
        return URLSafeSerializer(self.signup_token_secret, salt='signup')

    def decode_signup_token(self, token: str) -> 'SignupToken | None':
        try:
            return self.signup_token_serializer.loads(token)
        except BadSignature:
            return None

    @property
    def permitted_role_for_registration(self) -> str | None:
        """ Returns the permitted role for the current signup token. """

        if not self.signup_token:
            return 'member'

        assert self.signup_token_secret
        params = self.decode_signup_token(self.signup_token)

        if not params:
            return None

        if params['expires'] < int(datetime.utcnow().timestamp()):
            return None

        signups = UserCollection(self.session)\
            .by_signup_token(self.signup_token).count()

        if signups >= params['max_uses']:
            return None

        return params['role']

    def register(
        self,
        form: 'RegistrationForm',
        request: 'CoreRequest'
    ) -> 'User':
        """ Registers the user using the information on the registration form.

        Takes the signup token into account to provide the user with the
        proper role.

        See :meth:`onegov.user.collections.UserCollection.register_user` for
        more information.

        """

        role = self.permitted_role_for_registration

        if role is None:
            raise ExpiredSignupLinkError()

        assert form.username.data is not None
        assert form.password.data is not None
        return UserCollection(self.session).register(
            username=form.username.data,
            password=form.password.data,
            request=request,
            role=role,
            signup_token=self.signup_token
        )
