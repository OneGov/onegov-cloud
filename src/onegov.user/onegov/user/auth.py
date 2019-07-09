import morepath

from datetime import datetime
from itsdangerous import URLSafeSerializer, BadSignature
from onegov.core.utils import is_valid_yubikey
from onegov.core.utils import relative_url
from onegov.user import log
from onegov.user.collections import UserCollection
from onegov.user.errors import ExpiredSignupLinkError


class AuthFactor(object):
    """ A registry of auth factors. """

    registry = {}

    def __init_subclass__(cls, type, **kwargs):
        assert type not in cls.registry
        cls.registry[type] = cls
        super().__init_subclass__(**kwargs)


class YubikeyFactor(AuthFactor, type='yubikey'):
    """ Implements a yubikey factor for the :class:`Auth` class. """

    def __init__(self, **kwargs):
        self.yubikey_client_id = kwargs.pop('yubikey_client_id', None)
        self.yubikey_secret_key = kwargs.pop('yubikey_secret_key', None)

    @classmethod
    def args_from_app(cls, app):
        return {
            'yubikey_client_id': getattr(app, 'yubikey_client_id', None),
            'yubikey_secret_key': getattr(app, 'yubikey_secret_key', None)
        }

    def is_configured(self):
        return self.yubikey_client_id and self.yubikey_secret_key

    def is_valid(self, user_specific_config, factor):
        return is_valid_yubikey(
            client_id=self.yubikey_client_id,
            secret_key=self.yubikey_secret_key,
            expected_yubikey_id=user_specific_config,
            yubikey=factor
        )


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

        for type, cls in AuthFactor.registry.items():
            obj = cls(**kwargs)

            if obj.is_configured():
                self.factors[type] = obj

    @classmethod
    def from_app(cls, app, to='/', skip=False, signup_token=None):
        kwargs = {}

        for factor in AuthFactor.registry.values():
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
    def signup_token_serializer(self):
        assert self.signup_token_secret
        return URLSafeSerializer(self.signup_token_secret, salt='signup')

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

    def decode_signup_token(self, token):
        try:
            return self.signup_token_serializer.loads(token)
        except BadSignature:
            return None

    @property
    def users(self):
        return UserCollection(self.session)

    def redirect(self, request):
        return morepath.redirect(request.transform(self.to))

    def skippable(self, request):

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

    def login(self, username, password, client='unknown', second_factor=None):
        """ Takes the given username and password and matches them against
        the users collection.

        :meth:`login_to` should be the preferred method in most cases, as it
        sets up automatic logging of login attempts and provides optional
        login/logout messages.

        :return: An identity bound to the ``application_id`` if the username
        and password match.

        """

        user = self.users.by_username_and_password(username, password)

        def fail():
            log.info("Failed login by {} ({})".format(client, username))
            return None

        if user is None:
            return fail()

        if not user.active:
            return fail()

        if not self.is_valid_second_factor(user, second_factor):
            return fail()

        log.info("Successful login by {} ({})".format(client, username))

        return self.identity_class(
            userid=user.username,
            groupid=user.group_id.hex if user.group_id else '',
            role=user.role,
            application_id=self.application_id
        )

    def login_to(self, username, password, request, second_factor=None):
        """ Matches the username and password against the users collection,
        just like :meth:`login`. Unlike said method it returns no identity
        however, instead a redirect response is returned which will remember
        the identity.

        :return: A redirect response to ``self.to`` with the identity
        remembered as a cookie. If not successful, None is returned.

        """

        identity = self.login(username, password, request.client_addr,
                              second_factor)

        if identity is None:
            return None

        response = self.redirect(request)
        request.app.remember_identity(response, request, identity)

        user = self.users.by_username(username)
        if user:
            user.save_current_session(request)

        return response

    def logout_to(self, request):
        """ Logs the current user out and redirects to ``self.to``.

        :return: A response redirecting to ``self.to`` with the identity
        forgotten.

        """

        user = self.users.by_username(request.identity.userid)
        if user:
            user.remove_current_session(request)

        response = self.redirect(request)
        request.app.forget_identity(response, request)

        return response

    @property
    def permitted_role_for_registration(self):
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
