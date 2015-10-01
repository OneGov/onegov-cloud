import os
import os.path
import polib

from onegov.core import i18n
from onegov.core import utils
from webob import Request
from webob.acceptparse import Accept
from wtforms import Label


def test_pofiles(temporary_directory):
    os.makedirs(os.path.join(temporary_directory, 'de/LC_MESSAGES'))
    utils.touch(
        os.path.join(temporary_directory, 'de/LC_MESSAGES/onegov.test.po'))

    result = list(i18n.pofiles(temporary_directory))
    assert result[0][0] == 'de'
    assert result[0][1].endswith('onegov.test.po')


def test_get_translations(temporary_directory):
    os.makedirs(os.path.join(temporary_directory, '1/de/LC_MESSAGES'))
    po = polib.POFile()
    po.append(polib.POEntry(
        msgid=u'Welcome',
        msgstr=u'Willkommen'
    ))
    po.save(os.path.join(
        temporary_directory, '1/de/LC_MESSAGES/onegov.test.po'))

    os.makedirs(os.path.join(temporary_directory, '2/de/LC_MESSAGES'))
    po = polib.POFile()
    po.append(polib.POEntry(
        msgid=u'Morning',
        msgstr=u'Moin'
    ))
    po.save(os.path.join(
        temporary_directory, '2/de/LC_MESSAGES/onegov.test.po'))

    os.makedirs(os.path.join(temporary_directory, '2/fr/LC_MESSAGES'))
    po = polib.POFile()
    po.append(polib.POEntry(
        msgid=u'Welcome',
        msgstr=u'Bienvenue'
    ))
    po.save(os.path.join(
        temporary_directory, '2/fr/LC_MESSAGES/onegov.test.po'))

    translations = i18n.get_translations([
        temporary_directory + '/1',
        temporary_directory + '/2'
    ])
    assert list(sorted(translations.keys())) == list(sorted(['de', 'fr']))

    translations['de'].gettext(u'Welcome') == u'Willkommen'
    translations['de'].gettext(u'Morning') == u'Moin'
    translations['fr'].gettext(u'Welcome') == u'Bienvenue'

    translations = i18n.get_translations([
        temporary_directory + '/1',
    ])
    assert list(sorted(translations.keys())) == list(sorted(['de']))
    translations['de'].gettext(u'Welcome') == u'Willkommen'
    translations['de'].gettext(u'Morning') == u'Morning'

    translations = i18n.get_translations([
        temporary_directory + '/2',
    ])
    assert list(sorted(translations.keys())) == list(sorted(['de', 'fr']))
    translations['de'].gettext(u'Welcome') == u'Welcome'
    translations['de'].gettext(u'Morning') == u'Moin'
    translations['fr'].gettext(u'Welcome') == u'Bienvenue'


def test_default_locale_negotiator():
    negotiate = i18n.default_locale_negotiator
    request = Request.blank('/')

    request.accept_language = Accept('fr')
    assert negotiate(['en', 'de'], request) is None

    request.accept_language = Accept('en')
    assert negotiate(['en', 'de'], request) == 'en'

    request.accept_language = Accept('de')
    assert negotiate(['en', 'de'], request) == 'de'

    request.accept_language = Accept('de')
    request.cookies['language'] = 'en'
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

    assert form_class.Meta().get_translations(None) is default
    assert form_class.Meta().get_translations(None)._fallback is translate

    meta = form_class.Meta()
    meta.get_translations(None)
    assert meta.render_field(MockField('Yes'), {}) == 'seY'
