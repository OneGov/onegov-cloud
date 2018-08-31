import os
import os.path
import polib
import pytest

from gettext import GNUTranslations
from onegov.core import i18n, utils
from webob import Request
from wtforms import Label

# compatibility shim for webob 1.8 before its release
try:
    from webob.acceptparse import create_accept_language_header
except ImportError:
    from webob.acceptparse import Accept as create_accept_language_header


def test_pofiles(temporary_directory):
    os.makedirs(os.path.join(temporary_directory, 'de/LC_MESSAGES'))
    utils.touch(
        os.path.join(temporary_directory, 'de/LC_MESSAGES/onegov.test.po'))

    result = list(i18n.pofiles(temporary_directory))
    assert result[0][0] == 'de'
    assert result[0][1].endswith('onegov.test.po')


def test_merge_translations():
    t1 = GNUTranslations()
    t1._catalog = {
        'We are here': 'Hier sind wir',
        'Welcome': 'Willkommen'
    }

    t2 = GNUTranslations()
    t2._catalog = {
        'We are here': 'Wir sind hier',
        'Hi': 'Hallo'
    }

    t3 = GNUTranslations()
    t3._catalog = {
        'We are here': 'Sind wir hier',
        'Morning': 'Moin'
    }

    with pytest.raises(AssertionError):
        i18n.merge([])

    with pytest.raises(AssertionError):
        i18n.merge([i18n.clone(t1)])

    assert i18n.merge([i18n.clone(t1), i18n.clone(t2)])._catalog == {
        'We are here': 'Hier sind wir',
        'Welcome': 'Willkommen',
        'Hi': 'Hallo'
    }

    assert i18n.merge([i18n.clone(t2), i18n.clone(t3)])._catalog == {
        'We are here': 'Wir sind hier',
        'Morning': 'Moin',
        'Hi': 'Hallo'
    }

    assert i18n.merge(
        [i18n.clone(t1), i18n.clone(t2), i18n.clone(t3)])._catalog == {
        'We are here': 'Hier sind wir',
        'Welcome': 'Willkommen',
        'Morning': 'Moin',
        'Hi': 'Hallo'
    }


def test_get_translations(temporary_directory):
    os.makedirs(os.path.join(temporary_directory, '1/de/LC_MESSAGES'))
    po = polib.POFile()
    po.append(polib.POEntry(
        msgid='Welcome',
        msgstr='Willkommen'
    ))
    po.save(os.path.join(
        temporary_directory, '1/de/LC_MESSAGES/onegov.test.po'))

    os.makedirs(os.path.join(temporary_directory, '2/de/LC_MESSAGES'))
    po = polib.POFile()
    po.append(polib.POEntry(
        msgid='Morning',
        msgstr='Moin'
    ))
    po.save(os.path.join(
        temporary_directory, '2/de/LC_MESSAGES/onegov.test.po'))

    os.makedirs(os.path.join(temporary_directory, '2/fr/LC_MESSAGES'))
    po = polib.POFile()
    po.append(polib.POEntry(
        msgid='Welcome',
        msgstr='Bienvenue'
    ))
    po.save(os.path.join(
        temporary_directory, '2/fr/LC_MESSAGES/onegov.test.po'))

    translations = i18n.get_translations([
        temporary_directory + '/1',
        temporary_directory + '/2'
    ])
    assert list(sorted(translations.keys())) == list(sorted(['de', 'fr']))

    translations['de'].gettext('Welcome') == 'Willkommen'
    translations['de'].gettext('Morning') == 'Moin'
    translations['fr'].gettext('Welcome') == 'Bienvenue'

    translations = i18n.get_translations([
        temporary_directory + '/1',
    ])
    assert list(sorted(translations.keys())) == list(sorted(['de']))
    translations['de'].gettext('Welcome') == 'Willkommen'
    translations['de'].gettext('Morning') == 'Morning'

    translations = i18n.get_translations([
        temporary_directory + '/2',
    ])
    assert list(sorted(translations.keys())) == list(sorted(['de', 'fr']))
    translations['de'].gettext('Welcome') == 'Welcome'
    translations['de'].gettext('Morning') == 'Moin'
    translations['fr'].gettext('Welcome') == 'Bienvenue'


def test_default_locale_negotiator():

    negotiate = i18n.default_locale_negotiator
    request = Request.blank('/')

    request.accept_language = create_accept_language_header('fr')
    assert negotiate(['en', 'de'], request) is None

    request.accept_language = create_accept_language_header('en')
    assert negotiate(['en', 'de'], request) == 'en'

    request.accept_language = create_accept_language_header('de')
    assert negotiate(['en', 'de'], request) == 'de'

    request.accept_language = create_accept_language_header('de')
    request.cookies['locale'] = 'en'
    assert negotiate(['en', 'de'], request) == 'en'


def test_get_translation_bound_form():

    class MockTranslation(object):

        _fallback = None

        def add_fallback(self, translation):
            self._fallback = translation

        def gettext(self, text):
            return text[::-1]  # inverse the string

    default = MockTranslation()
    translate = MockTranslation()

    class MetaMeta(object):

        def render_field(self, field, render_kw):
            return field.label.text

    class MockMeta(MetaMeta):

        def get_translations(self, form):
            return default

    class MockForm(object):

        Meta = MockMeta

    class MockField(object):

        def __init__(self, label):
            self.label = Label('x', label)

    form_class = i18n.get_translation_bound_form(MockForm, translate)

    assert form_class.Meta().get_translations(None) is translate
    assert form_class.Meta().get_translations(None)._fallback is default

    meta = form_class.Meta()
    meta.get_translations(None)
    assert meta.render_field(MockField('Yes'), {}) == 'seY'
