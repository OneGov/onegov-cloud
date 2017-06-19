""" Provides tools and methods for internationalization (i18n).

Applications wishing to use i18n need to define two settings:

:i18n.localedirs:
    A list of gettext locale directories. The first directory is considered
    to be the main directory, all other directories are added to the
    translation object as fallbacks.

:i18n.default_locale:
    The fallback locale that is used if no locale more suitable to the user
    could be found.

For example::

    from onegov.core.framework import Framework
    from onegov.core import utils

    class App(Framework):
        pass

    @TownApp.setting(section='i18n', name='localedirs')
    def get_i18n_localedirs():
        return [
            utils.module_path('onegov.town', 'locale')
            utils.module_path('onegov.form', 'locale')
        ]

    @TownApp.setting(section='i18n', name='default_locale')
    def get_i18n_default_locale():
        return 'en'

"""

import gettext
import glob
import morepath
import os
import os.path
import polib
import re

from functools import lru_cache
from io import BytesIO
from onegov.core.framework import Framework, log
from onegov.core.utils import pairwise
from translationstring import ChameleonTranslate
from translationstring import Translator


# the language codes must be written thusly: de_CH, en_GB, en, fr and so on
# this is important because other libs like wtforms use the same scheme and
# will fail to deal with our langauges correctly if they differ in case
VALID_LANGUAGE_EXPRESSION = re.compile(r'^[a-z]{2}(_[A-Z]{2})?$')


@Framework.setting(section='i18n', name='localedirs')
def get_i18n_localedirs():
    """ Returns the gettext locale dir. """
    return tuple()


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


def default_locale_negotiator(locales, request):
    """ The default locale negotiator.

    Will select one of the given locales by:

    1. Examining the 'locale' cookie which will be preferred if the
       language in the cookie actually exists

    2. Selecting the best match from the accept_language header

    If no match can be found, None is returned. It is the job of caller to
    deal with that (possibly getting :meth:`get_i18n_default_locale`).

    """
    user_locale = request.cookies.get('locale')

    if user_locale in locales:
        return user_locale

    return request.accept_language.best_match(locales)


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
            yield path, pofile


@lru_cache(maxsize=32)
def compile_translation(pofile_path):
    log.info("Compiling pofile {}".format(pofile_path))

    mofile = BytesIO()
    mofile.write(polib.pofile(pofile_path).to_binary())
    mofile.seek(0)

    return gettext.GNUTranslations(mofile)


def get_translations(localedirs):
    """ Takes the given gettext locale directories and loads the po files
    found. The first found po file is assumed to be the main
    translations file (and should for performance reasons contain most of the
    translations). The other po files are added as fallbacks.

    The pofiles are compiled on-the-fly, using polib. This makes mofiles
    unnecessary.

    Returns a dictionary with the keys being languages and the values being
    GNUTranslations instances.

    """

    result = {}

    for localedir in localedirs:
        for language, pofile_path in pofiles(localedir):

            # try to automatically fix up the language
            if '_' in language:
                code, country = language.split('_')
                language = '_'.join((code.lower(), country.upper()))
            else:
                language = language.lower()

            assert VALID_LANGUAGE_EXPRESSION.match(language), """
                make sure to use languages in the following format:
                de_CH, en_GB, de, fr - note the case!
            """

            # we need to clone each translation because we might later modify
            # them when we merge translations - when multiple applications
            # share the same process this can lead to translations from one
            # application spilling over to the translations of another
            translation = clone(compile_translation(pofile_path))

            if language not in result:
                result[language] = translation
            else:
                result[language] = merge((result[language], translation))

    return result


def wrap_translations_for_chameleon(translations):
    """ Takes the given translations and wraps them for use with Chameleon. """

    return {
        lang: ChameleonTranslate(Translator(translation))
        for lang, translation in translations.items()
    }


def add_fallback_to_tail(translation, fallback):
    """ Adds the given fallback to the given translation, if it isn't already
    found somewhere in the fallback chain.

    """

    assert translation is not fallback

    while translation._fallback is not None:
        translation = translation._fallback

        if translation is fallback:
            return

    translation.add_fallback(fallback)


def get_translation_bound_meta(meta_class, translate):
    """ Takes a wtforms Meta class and combines our translate class with
    the one provided by WTForms itself.

    """

    class TranslationBoundMeta(meta_class):

        # instruct wtforms not to cache translations, there's very little
        # performance gain and it leads to some state not being cleared when
        # the request has been handled
        cache_translations = False

        def get_translations(self, form):

            try:
                default = super().get_translations(form)
                add_fallback_to_tail(translation=default, fallback=translate)
            except FileNotFoundError:
                # if there are no locales, the file not found error
                # can safely be ignored as there are no translations if there
                # are no locales (a wtforms bug)
                assert not getattr(self, 'locales', None)
                default = translate

            # Cache for reuse in render_field.
            self._translations = default

            return default

        def render_field(self, field, render_kw):
            """ Wtforms does not actually translate labels, it simply leaves
            the translations string be. If those translation strings hit our
            templates directly, they will then be picked up by our template
            renderer.

            However, that's not always the case. For example, when rendering
            a list of options, WTForms renders each option as a field with a
            label. By doing that it coerces the translation string into a
            plain string.

            By always translating the labels before they hit the template we
            can make sure that this is not a problem. We do this by
            intercepting each render call, which thankfully is something
            wtforms does support.

            """
            if hasattr(field, 'label'):
                field.label.text = self._translations.gettext(field.label.text)

            return super().render_field(
                field, render_kw)

    return TranslationBoundMeta


def get_translation_bound_form(form_class, translate):
    """ Returns a form setup with the given translate function. """

    MetaClass = get_translation_bound_meta(form_class.Meta, translate)

    class TranslationBoundForm(form_class):

        Meta = MetaClass

    return TranslationBoundForm


def merge(translations):
    """ Takes the given translations (a list) and merges them into
    each other. The translations at the end of the list are overwritten
    by the translations at the start of the list.

    This is preferrable to adding fallbacks, as they increases the average
    complexity of the lookup function each time.

    Note that the translations are *not* copied before merging, so that means
    all existing translations are changed during this processed. To avoid
    this, clone the translation first (see :func:`clone`).

    :returns:
        The last GNUTranslations object with all other translation
        objects merged into it. The first element overrides the second and so
        on.

    """
    assert len(translations) > 1

    for current, following in pairwise(translations):
        if following is not None:
            following._catalog.update(current._catalog)

    return translations[-1]


def clone(translation):
    """ Clones the given translation, creating an independent copy. """
    clone = gettext.GNUTranslations()
    clone._catalog = translation._catalog.copy()

    return clone


class SiteLocale(object):
    """ A model representing the locale of the site.

    Use this model to enable the user to change his locale through a path.

    """

    @classmethod
    def for_path(cls, app, locale, to):
        if locale in app.locales:
            return cls(locale, to)

    def __init__(self, locale, to):
        self.locale = locale
        self.to = to

    def redirect(self):
        response = morepath.redirect(self.to)
        response.set_cookie('locale', self.locale, overwrite=True)

        return response
