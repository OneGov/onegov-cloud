from abc import ABCMeta, abstractmethod
from onegov.core.utils import is_valid_yubikey


from typing import Any, ClassVar, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Mapping
    from morepath import App
    from typing_extensions import Self, TypedDict

    class YubikeyConfig(TypedDict):
        yubikey_client_id: str | None
        yubikey_secret_key: str | None


SECOND_FACTORS: dict[str, type['SecondFactor']] = {}


class SecondFactor(metaclass=ABCMeta):
    """ Base class and registry for secondary auth factors. """

    __slots__ = ()

    if TYPE_CHECKING:
        # forward declare for type checking, SecondFactor is
        # abstract so this attribute will always exist
        type: ClassVar[str]

    def __init_subclass__(cls, type: str, **kwargs: Any):
        global SECOND_FACTORS
        assert type not in SECOND_FACTORS

        SECOND_FACTORS[type] = cls

        super().__init_subclass__(**kwargs)

    @classmethod
    @abstractmethod
    def configure(self, **cfg: Any) -> 'Self | None':
        """ Initialises the auth factor using a dictionary that may or may
        not contain the configuration values necessary for the auth factor.

        If the configuration is invalid None will be returned, otherwise
        a new instance is created.

        All used configuration values should be popped, not just read.

        """

    @classmethod
    @abstractmethod
    def args_from_app(cls, app: 'App') -> 'Mapping[str, Any]':
        """ Copies the required configuration values from the app, returning
        a dictionary with all keys present. The values should be either the
        ones from the application or None.

        """

    @abstractmethod
    def is_valid(self, user_specific_config: Any, factor: str) -> bool:
        """ Returns true if the given factor is valid for the given
        user-specific configuration. This is the value stored on the
        user in the `second_factor` column.

        """


class YubikeyFactor(SecondFactor, type='yubikey'):
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
    def configure(cls, **cfg: Any) -> 'Self | None':
        yubikey_client_id = cfg.pop('yubikey_client_id', None)
        yubikey_secret_key = cfg.pop('yubikey_secret_key', None)
        if not yubikey_client_id or not yubikey_secret_key:
            return None

        return cls(yubikey_client_id, yubikey_secret_key)

    @classmethod
    def args_from_app(cls, app: 'App') -> 'YubikeyConfig':
        return {
            'yubikey_client_id': getattr(app, 'yubikey_client_id', None),
            'yubikey_secret_key': getattr(app, 'yubikey_secret_key', None)
        }

    def is_valid(self, user_specific_config: str, factor: str) -> bool:
        return is_valid_yubikey(
            client_id=self.yubikey_client_id,
            secret_key=self.yubikey_secret_key,
            expected_yubikey_id=user_specific_config,
            yubikey=factor
        )
