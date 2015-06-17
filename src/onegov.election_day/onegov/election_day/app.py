from onegov.core import Framework, utils
from onegov.election_day.theme import ElectionDayTheme
from onegov.election_day.model import Principal


class ElectionDayApp(Framework):
    """ The election day application. Include this in your onegov.yml to serve
    it with onegov-server.

    """

    @property
    def principal(self):
        """ Returns the principal of the election day app. See
        :class:`onegov.election_day.model.Principal`.

        """
        return Principal()


@ElectionDayApp.template_directory()
def get_template_directory():
    return 'templates'


@ElectionDayApp.setting(section='core', name='theme')
def get_theme():
    return ElectionDayTheme()


@ElectionDayApp.setting(section='i18n', name='domain')
def get_i18n_domain():
    return 'onegov.election_day'


@ElectionDayApp.setting(section='i18n', name='localedir')
def get_i18n_localedir():
    return utils.module_path('onegov.election_day', 'locale')


@ElectionDayApp.setting(section='i18n', name='default_locale')
def get_i18n_default_locale():
    return 'de'
