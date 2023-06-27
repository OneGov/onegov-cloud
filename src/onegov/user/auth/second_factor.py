from abc import ABCMeta, abstractmethod
from onegov.core.utils import is_valid_yubikey


from typing import Any, ClassVar, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Mapping
    from onegov.core.framework import Framework
    from typing import TypedDict

    class YubikeyConfig(TypedDict):
        yubikey_client_id: str | None
        yubikey_secret_key: str | None


SECOND_FACTORS: dict[str, type['SecondFactor']] = {}

# FIXME: The API for this seems a bit insane, it would make more
#        sense if, like with `AuthenticationProvider`, there was a
#        `configure` method that could either return a SecondFactor
#        or None. That way only configured SecondFactors would be
#        available in the first place and we don't have to assert
#        a bunch of things about the config inside every `is_valid`
#        method...


class SecondFactor(metaclass=ABCMeta):
    """ Base class and registry for secondary auth factors. """

    if TYPE_CHECKING:
        # forward declare for type checking, SecondFactor is
        # abstract so this attribute will always exist
        type: ClassVar[str]

    def __init_subclass__(cls, type: str, **kwargs: Any):
        global SECOND_FACTORS
        assert type not in SECOND_FACTORS

        SECOND_FACTORS[type] = cls

        super().__init_subclass__(**kwargs)

    @abstractmethod
    def __init__(self, **kwargs: Any):
        """ Initialises the auth factor using a dictionary that may or may
        not contain the configuration values necessary for the auth factor.

        Either way, the auth factor is instantiated even if the needed
        configuration is not available.

        The :meth:`is_configured` method is responsible for signaling if
        the configuration has been successful or not.

        All used configuration values should be popped, not just read.

        """

    @classmethod
    @abstractmethod
    def args_from_app(cls, app: 'Framework') -> 'Mapping[str, Any]':
        """ Copies the required configuration values from the app, returning
        a dictionary with all keys present. The values should be either the
        ones from the application or None.

        """

    @abstractmethod
    def is_configured(self) -> bool:
        """ Returns `True` if the factor has been properly configured. """

    @abstractmethod
    def is_valid(self, user_specific_config: Any, factor: str) -> bool:
        """ Returns true if the given factor is valid for the given
        user-specific configuration. This is the value stored on the
        user in the `second_factor` column.

        """


class YubikeyFactor(SecondFactor, type='yubikey'):
    """ Implements a yubikey factor for the :class:`Auth` class. """

    def __init__(
        self,
        yubikey_client_id: str | None = None,
        yubikey_secret_key: str | None = None,
        **kwargs: Any
    ):
        self.yubikey_client_id = yubikey_client_id
        self.yubikey_secret_key = yubikey_secret_key

    @classmethod
    def args_from_app(cls, app: 'Framework') -> 'YubikeyConfig':
        return {
            'yubikey_client_id': getattr(app, 'yubikey_client_id', None),
            'yubikey_secret_key': getattr(app, 'yubikey_secret_key', None)
        }

    def is_configured(self) -> bool:
        if self.yubikey_client_id and self.yubikey_secret_key:
            return True
        return False

    def is_valid(self, user_specific_config: str, factor: str) -> bool:
        assert self.yubikey_client_id is not None
        assert self.yubikey_secret_key is not None
        return is_valid_yubikey(
            client_id=self.yubikey_client_id,
            secret_key=self.yubikey_secret_key,
            expected_yubikey_id=user_specific_config,
            yubikey=factor
        )
