""" Provies tools and methods for internationalization (i18n).

Applications wishing to use i18n need to define two settings:

:i18n.domain:
    The domain of the translation (e.g. onegov.town)

:i18n.localedir:
    The absolute path the gettext locale dir.

For example::

    from onegov.core import Framework
    from onegov.core import utils

    class App(Framework):
        pass

    @TownApp.setting(section='i18n', name='domain')
    def get_i18n_domain():
        return 'onegov.town'

    @TownApp.setting(section='i18n', name='localedir')
    def get_i18n_localedir():
        return utils.module_path('onegov.town', 'locale')

"""

import gettext
import glob
import os
import os.path
import polib

from io import BytesIO
from onegov.core import log
from onegov.core import Framework
from translationstring import ChameleonTranslate
from translationstring import Translator


@Framework.setting(section='i18n', name='domain')
def get_i18n_domain():
    """ Returns the gettext domain used for the translations. """
    return None


@Framework.setting(section='i18n', name='localedir')
def get_i18n_localedir():
    """ Returns the gettext locale dir. """
    return None


@Framework.setting(section='i18n', name='default_locale')
def get_i18n_default_locale():
    """ Returns the fallback language to use if the user gives no indication
    towards his preference (throught the request or anything). """
    return None


@Framework.setting(section='i18n', name='locale_negotiator')
def get_i18n_locale_negotiatior():
    """ Returns the language negotiator, which is a function that takes the
    current request as well as a list of available languages and returns the
    angauge that should be used based on that information.

    """
    return default_locale_negotiator


def default_locale_negotiator(languages, request):
    """ The default locale negotiator.

    Will select one of the given languages by:

    1. Examining the 'language' cookie which will be preferred if the
      language in the cookie actually exists

    2. Selecting the best match from the accept_language header

    If no match can be found, None is returned. It is the job of caller to
    deal with that (possibly getting :meth:`get_i18n_default_locale`).

    """
    user_language = request.cookies.get('language')

    if user_language in languages:
        return user_language

    return request.accept_language.best_match(languages)


def pofiles(localedir):
    """ Takes the given directory and yields the language and the path of
    all pofiles found under ``*/LC_MESSAGES/*.po``.

    """

    assert os.path.isdir(localedir), "Locale '{}' not found".format(localedir)

    for path in os.listdir(localedir):
        subpath = os.path.join(localedir, path, 'LC_MESSAGES')

        if not os.path.isdir(subpath):
            continue

        for pofile in glob.glob(os.path.join(subpath, '*.po')):
            yield path, os.path.join(subpath, pofile)


def get_translations(domain, localedir):
    """ Takes the given domain and locale dir and loads the po files
    found.

    The pofiles are compiled on-the-fly, using polib. This makes mofiles
    unnecessary.

    Returns a dictionary with the keys being languages and the values being
    GNUTranslations instances.

    """

    result = {}

    for language, pofile_path in pofiles(localedir):

        if not pofile_path.endswith('{}.po'.format(domain)):
            log.debug("Skipping pofile {}".format(pofile_path))
            continue
        else:
            log.debug("Compiling pofile {}".format(pofile_path))

        mofile = BytesIO()
        mofile.write(polib.pofile(pofile_path).to_binary())
        mofile.seek(0)

        result[language] = gettext.GNUTranslations(mofile)

    return result


def get_chameleon_translators(domain, localedir):
    """ Returns the translate function for the given domain and localedir as
    a dictionary keyed by language.

    """

    config = (domain, localedir)

    if not all(config):
        return None

    result = {}

    for language, translation in get_translations(*config).items():
        result[language] = ChameleonTranslate(
            Translator(translation)
        )

    return result
