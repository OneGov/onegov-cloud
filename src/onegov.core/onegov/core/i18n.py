""" Provies tools and methods for internationalization (i18n).

Applications wishing to use i18n need to define two settings:

:i18n.localedirs:
    A list of gettext locale directories. The first directory is considered
    to be the main directory, all other directories are added to the
    translation object as fallbacks.

:i18n.default_locale:
    The fallback locale that is used if no locale more suitable to the user
    could be found.

For example::

    from onegov.core import Framework
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
import os
import os.path
import polib

from io import BytesIO
from onegov.core import Framework, log
from onegov.core.utils import pairwise
from translationstring import ChameleonTranslate
from translationstring import Translator


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
            yield path, pofile


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
            log.info("Compiling pofile {}".format(pofile_path))

            mofile = BytesIO()
            mofile.write(polib.pofile(pofile_path).to_binary())
            mofile.seek(0)

            if language not in result:
                result[language] = gettext.GNUTranslations(mofile)
            else:
                result[language] = merge(
                    (result[language], gettext.GNUTranslations(mofile))
                )

    return result


def wrap_translations_for_chameleon(translations):
    """ Takes the given translations and wraps them for use with Chameleon. """

    return {
        lang: ChameleonTranslate(Translator(translation))
        for lang, translation in translations.items()
    }


def get_translation_bound_meta(meta_class, translate):
    """ Takes a wtforms Meta class and combines our translate class with
    the one provided by WTForms itself.

    """

    class TranslationBoundMeta(meta_class):

        def get_translations(self, form):
            default = super(TranslationBoundMeta, self).get_translations(form)

            # WTForms does this weird dance where it wraps translations for
            # Python 2, but not for Python 3. That's why we have to do this:
            if hasattr(default, '_fallback'):
                if not default._fallback:
                    default.add_fallback(translate)
            else:
                if not default.translations._fallback:
                    default.translations.add_fallback(translate)

            # Cache for reuse in render_field. I'm not sure this is perfectly
            # sane, as WTForms does use it's own caching mechanism with
            # translations bound to the current locales. For now it seems
            # fine, but we don't do different locales yet.
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

            return super(TranslationBoundMeta, self).render_field(
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

    :return: The last GNUTranslations object with all other translation
    objects merged into it. The first element overrides the second and so on.

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
