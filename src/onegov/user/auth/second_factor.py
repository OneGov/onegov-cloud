from __future__ import annotations

import morepath
import pyotp

from abc import ABCMeta, abstractmethod
from datetime import timedelta
from onegov.core.utils import is_valid_yubikey
from onegov.user.collections import TANCollection
from onegov.user.i18n import _
from onegov.user.models import TAN


from typing import Any, ClassVar, Literal, Self, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Mapping
    from morepath import App
    from onegov.core.request import CoreRequest
    from onegov.user import User
    from onegov.user.auth import Auth
    from typing import TypeAlias, TypedDict
    from webob import Response

    class YubikeyConfig(TypedDict):
        yubikey_client_id: str | None
        yubikey_secret_key: str | None

    class MTANConfig(TypedDict):
        mtan_second_factor_enabled: bool
        mtan_automatic_setup: bool

    class TOTPConfig(TypedDict):
        totp_enabled: bool

    AnySecondFactor: TypeAlias = 'SingleStepSecondFactor | TwoStepSecondFactor'


SECOND_FACTORS: dict[str, type[AnySecondFactor]] = {}


class SecondFactor(metaclass=ABCMeta):
    """ Base class and registry for secondary auth factors. """

    __slots__ = ()

    if TYPE_CHECKING:
        # forward declare for type checking, SecondFactor is
        # abstract so this attribute will always exist
        type: ClassVar[str]
        kind: ClassVar[Literal['single_step', 'two_step']]

    self_activation: bool = False

    def __init_subclass__(cls, type: str | None = None, **kwargs: Any):
        global SECOND_FACTORS
        if type is not None:
            assert issubclass(cls, (
                SingleStepSecondFactor,
                TwoStepSecondFactor
            ))
            assert type not in SECOND_FACTORS

            SECOND_FACTORS[type] = cls
            cls.type = type
        else:
            assert cls.kind in ('single_step', 'two_step')

        super().__init_subclass__(**kwargs)

    @classmethod
    @abstractmethod
    def configure(cls, **cfg: Any) -> Self | None:
        """ Initialises the auth factor using a dictionary that may or may
        not contain the configuration values necessary for the auth factor.

        If the configuration is invalid None will be returned, otherwise
        a new instance is created.

        All used configuration values should be popped, not just read.

        """

    @classmethod
    @abstractmethod
    def args_from_app(cls, app: App) -> Mapping[str, Any]:
        """ Copies the required configuration values from the app, returning
        a dictionary with all keys present. The values should be either the
        ones from the application or None.

        """

    def start_activation(
        self,
        request: CoreRequest,
        auth: Auth
    ) -> Response | None:
        """ Initiates the activation of the second factor. """
        return None

    def complete_activation(self, user: User, factor: Any) -> None:
        """ Completes the activation of the second factor. """
        assert factor
        user.second_factor = {'type': self.type, 'data': factor}


class SingleStepSecondFactor(SecondFactor):
    """ Base class for single step secondary auth factors.

    Second factors may be eagerly available like a TOTP, so we can
    ask for it in the initial login form, rather than in a second step.
    """

    kind: ClassVar[Literal['single_step']] = 'single_step'

    @abstractmethod
    def is_valid(
        self,
        request: CoreRequest,
        user: User,
        factor: str
    ) -> bool:
        """ Returns true if the given factor is valid for the given
        user-specific configuration. This is the value stored on the
        user in the `second_factor` column.

        """


class TwoStepSecondFactor(SecondFactor):
    """ Base class for two step secondary auth factors.

    Second factors may involve a challenge response step like sending
    a token to a mobile device.
    """

    kind: ClassVar[Literal['two_step']] = 'two_step'

    @abstractmethod
    def send_challenge(
        self,
        request: CoreRequest,
        user: User,
        auth: Auth
    ) -> Response:
        """ Sends the authentication challenge.

        The response will be checked in a second step using :meth:`is_valid`
        """


class YubikeyFactor(SingleStepSecondFactor, type='yubikey'):
    """ Implements a yubikey factor for the :class:`Auth` class. """

    __slots__ = ('yubikey_client_id', 'yubikey_secret_key')

    def __init__(
        self,
        yubikey_client_id: str,
        yubikey_secret_key: str
    ):
        self.yubikey_client_id = yubikey_client_id
        self.yubikey_secret_key = yubikey_secret_key

    @classmethod
    def configure(cls, **cfg: Any) -> Self | None:
        yubikey_client_id = cfg.pop('yubikey_client_id', None)
        yubikey_secret_key = cfg.pop('yubikey_secret_key', None)
        if not yubikey_client_id or not yubikey_secret_key:
            return None

        return cls(yubikey_client_id, yubikey_secret_key)

    @classmethod
    def args_from_app(cls, app: App) -> YubikeyConfig:
        return {
            'yubikey_client_id': getattr(app, 'yubikey_client_id', None),
            'yubikey_secret_key': getattr(app, 'yubikey_secret_key', None)
        }

    def is_valid(
        self,
        request: CoreRequest,
        user: User,
        factor: str
    ) -> bool:

        if not user.second_factor:
            return False

        return is_valid_yubikey(
            client_id=self.yubikey_client_id,
            secret_key=self.yubikey_secret_key,
            expected_yubikey_id=user.second_factor['data'],
            yubikey=factor
        )


class MTANFactor(TwoStepSecondFactor, type='mtan'):
    """ Implements a mTAN factor for the :class:`Auth` class. """

    __slots__ = ('self_activation', 'expires_after')

    def __init__(self, mtan_automatic_setup: bool) -> None:
        self.self_activation = mtan_automatic_setup
        # TODO: Do we want to make this configurable? For now we want
        #       this to be slightly shorter than the default validity
        #       period of one hour, since the second factor is a little
        #       bit more sensitive.
        self.mtan_expires_after = timedelta(minutes=15)

    @classmethod
    def configure(cls, **cfg: Any) -> Self | None:
        if not cfg.pop('mtan_second_factor_enabled', False):
            return None

        return cls(cfg.pop('mtan_automatic_setup', False))

    @classmethod
    def args_from_app(cls, app: App) -> MTANConfig:
        # if we can't deliver SMS we can't do mTAN authentication
        if not getattr(app, 'can_deliver_sms', False):
            enabled = False
        else:
            enabled = getattr(app, 'mtan_second_factor_enabled', False)

        return {
            'mtan_second_factor_enabled': enabled,
            'mtan_automatic_setup': getattr(app, 'mtan_automatic_setup', False)
        }

    def tans(self, request: CoreRequest) -> TANCollection:
        return TANCollection(
            request.session,
            scope='mtan_second_factor',
            expires_after=self.mtan_expires_after
        )

    def start_activation(
        self,
        request: CoreRequest,
        auth: Auth
    ) -> Response | None:
        if not self.self_activation:
            return None

        activation_url = request.link(auth, name='mtan-setup')
        return morepath.redirect(activation_url)

    def send_challenge(
        self,
        request: CoreRequest,
        user: User,
        auth: Auth,
        mobile_number: str | None = None
    ) -> Response:

        if mobile_number is None:
            assert user.second_factor
            mobile_number = user.second_factor['data']
            assert mobile_number is not None

        tans = self.tans(request)
        obj = tans.add(
            client=request.client_addr or 'unknown',
            username=user.username,
            mobile_number=mobile_number
        )
        authenticate_url = request.link(auth, name='mtan')

        app = request.app
        # FIXME: we should define the title on app, so each app can
        #        define how it's defined
        assert hasattr(app, 'org')
        app.send_sms(mobile_number, request.translate(_(
            '${mtan} - mTAN for ${organisation}.',
            mapping={
                'organisation': app.org.title,
                'mtan': obj.tan,
            }
        )))
        request.info(_(
            'We sent an mTAN to the number linked with this account. '
            'Please enter it below.'
        ))
        return morepath.redirect(authenticate_url)

    def is_valid(
        self,
        request: CoreRequest,
        username: str,
        mobile_number: str,
        factor: str
    ) -> bool:

        tans = self.tans(request)
        tan = tans.by_tan(factor)
        if (
            tan is not None
            and tan.meta.get('mobile_number') == mobile_number
            and tan.meta.get('username') == username
        ):
            # expire the TAN we just used
            tan.expire()
            # expire any other TANs issued to the same user
            for tan in tans.query().filter(TAN.meta['username'] == username):
                tan.expire()
            return True
        return False


class TOTPFactor(TwoStepSecondFactor, type='totp'):
    """ Implements a TOTP factor for the :class:`Auth` class. """

    @classmethod
    def configure(cls, **cfg: Any) -> Self | None:
        if not cfg.pop('totp_enabled', False):
            return None

        return cls()

    @classmethod
    def args_from_app(cls, app: App) -> TOTPConfig:
        return {
            'totp_enabled': getattr(app, 'totp_enabled', False)
        }

    def send_challenge(
        self,
        request: CoreRequest,
        user: User,
        auth: Auth,
        mobile_number: str | None = None
    ) -> Response:

        return morepath.redirect(request.link(auth, name='totp'))

    def is_valid(
        self,
        request: CoreRequest,
        user: User,
        factor: str
    ) -> bool:

        if not user.second_factor:
            return False

        assert user.second_factor['type'] == 'totp'
        totp = pyotp.TOTP(user.second_factor['data'])
        return totp.verify(factor)
