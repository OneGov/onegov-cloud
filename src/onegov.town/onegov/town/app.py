""" Contains the application which builds on onegov.core and uses
more.chameleon.

It's possible that the chameleon integration is moved to onegov.core in the
future, but for now it is assumed that different applications may want to
use different templating languages.

"""

from onegov.core import Framework
from more.chameleon import ChameleonApp


class TownApp(Framework, ChameleonApp):
    """ The town application. Include this in your onegov.yml to serve it
    with onegov-server.

    """


@TownApp.template_directory()
def get_template_directory():
    return 'templates'
