import morepath

from datetime import datetime
from itsdangerous import URLSafeSerializer, BadSignature

from onegov.core.utils import relative_url
from onegov.user import log
from onegov.user.collections import UserCollection
from onegov.user.errors import ExpiredSignupLinkError
from onegov.user.auth.second_factor import SECOND_FACTORS


class Auth(object):
    """ Defines a model for authentication methods like login/logout.
    Applications should use this model to implement authentication views.

    """

    identity_class = morepath.Identity

    def __init__(self, session, application_id, to='/', skip=False,
                 signup_token=None, signup_token_secret=None, **kwargs):
        assert application_id  # may not be empty!

        self.session = session
        self.application_id = application_id

        self.signup_token = signup_token
        self.signup_token_secret = signup_token_secret

        # never redirect to an external page, this might potentially be used
        # to trick the user into thinking he's on our page after entering his
        # password and being redirected to a phishing site.
        self.to = relative_url(to)
        self.skip = skip

        # initialize nth factors
        self.factors = {}

        for type, cls in SECOND_FACTORS.items():
            obj = cls(**kwargs)

            if obj.is_configured():
                self.factors[type] = obj

    @classmethod
    def from_app(cls, app, to='/', skip=False, signup_token=None):
        kwargs = {}

        for factor in SECOND_FACTORS.values():
            kwargs.update(factor.args_from_app(app))

        return cls(
            session=app.session(),
            application_id=app.application_id,
            to=to,
            skip=skip,
            signup_token=signup_token,
            signup_token_secret=getattr(app, 'identity_secret', None),
            **kwargs,
        )

    @classmethod
    def from_request(cls, request, to='/', skip=False, signup_token=None):
        return cls.from_app(request.app, to, skip, signup_token)

    @classmethod
    def from_request_path(cls, request, skip=False, signup_token=None):
        return cls.from_request(
            request, request.transform(request.path), skip, signup_token)

    @property
    def users(self):
        return UserCollection(self.session)

    def redirect(self, request):
        return morepath.redirect(request.transform(self.to))

    def skippable(self, request):
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

    def is_valid_second_factor(self, user, second_factor_value):
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

    def authenticate(self, username, password,
                     client='unknown', second_factor=None):
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

        :return: The matched user, if successful, or None.

        """

        user = self.users.by_username_and_password(username, password)

        def fail():
            log.info(f"Failed login by {client} ({username})")
            return None

        if user is None:
            return fail()

        if not user.active:
            return fail()

        if user.authentication_provider:
            if user.authentication_provider.get('required', False):
                return fail()

        if not self.is_valid_second_factor(user, second_factor):
            return fail()

        log.info(f"Successful login by {client} ({username})")
        return user

    def as_identity(self, user):
        """ Returns the morepath identity of the given user. """

        return self.identity_class(
            userid=user.username,
            groupid=user.group_id.hex if user.group_id else '',
            role=user.role,
            application_id=self.application_id
        )

    def by_identity(self, identity):
        """ Returns the user record of the given identity. """

        return self.users.by_username(identity.userid)

    def login_to(self, username, password, request, second_factor=None):
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

        :return: A redirect response to ``self.to`` with the identity
        remembered as a cookie. If not successful, None is returned.

        """

        user = self.authenticate(
            username=username,
            password=password,
            client=request.client_addr,
            second_factor=second_factor)

        if user is None:
            return None

        return self.complete_login(user, request)

    def complete_login(self, user, request):
        """ Takes a user record, remembers its session and returns a proper
        redirect response to complete the login.

        This method is mostly useful inside onegov.user. You probably want
        to use :meth:`complete_login` outside of that.

        """
        assert user is not None

        identity = self.as_identity(user)
        response = self.redirect(request)

        request.app.remember_identity(response, request, identity)
        user.save_current_session(request)

        return response

    def logout_to(self, request):
        """ Logs the current user out and redirects to ``self.to``.

        :return: A response redirecting to ``self.to`` with the identity
        forgotten.

        """

        user = self.by_identity(request.identity)
        user and user.remove_current_session(request)

        response = self.redirect(request)
        request.app.forget_identity(response, request)

        return response

    def new_signup_token(self, role, max_age=24 * 60 * 60, max_uses=1):
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
    def signup_token_serializer(self):
        assert self.signup_token_secret
        return URLSafeSerializer(self.signup_token_secret, salt='signup')

    def decode_signup_token(self, token):
        try:
            return self.signup_token_serializer.loads(token)
        except BadSignature:
            return None

    @property
    def permitted_role_for_registration(self):
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

    def register(self, form, request):
        """ Registers the user using the information on the registration form.

        Takes the signup token into account to provide the user with the
        proper role.

        See :meth:`onegov.user.collections.UserCollection.register_user` for
        more information.

        """

        role = self.permitted_role_for_registration

        if role is None:
            raise ExpiredSignupLinkError()

        return UserCollection(self.session).register(
            username=form.username.data,
            password=form.password.data,
            request=request,
            role=role,
            signup_token=self.signup_token
        )
