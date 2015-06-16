from onegov.core import Framework
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
