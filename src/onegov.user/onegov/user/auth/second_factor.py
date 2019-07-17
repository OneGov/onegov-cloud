from abc import ABCMeta, abstractmethod
from onegov.core.utils import is_valid_yubikey


SECOND_FACTORS = {}


class SecondFactor(metaclass=ABCMeta):
    """ Base class and registry for secondary auth factors. """

    def __init_subclass__(cls, type, **kwargs):
        global SECOND_FACTORS
        assert type not in SECOND_FACTORS

        SECOND_FACTORS[type] = cls

        super().__init_subclass__(**kwargs)

    @abstractmethod
    def __init__(self, **kwargs):
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
    def args_from_app(cls, app):
        """ Copies the required configuration values from the app, returning
        a dictionary with all keys present. The values should be either the
        ones from the application or None.

        """

    @abstractmethod
    def is_configured(self):
        """ Returns `True` if the factor has been properly configured. """

    @abstractmethod
    def is_valid(self, user_specific_config, factor):
        """ Returns true if the given factor is valid for the given
        user-specific configuration. This is the value stored on the
        user in the `second_factor` column.

        """


class YubikeyFactor(SecondFactor, type='yubikey'):
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
