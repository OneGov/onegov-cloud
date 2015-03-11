import os
import os.path
import polib

from onegov.core import i18n
from onegov.core import utils
from webob import Request
from webob.acceptparse import Accept


def test_pofiles(tempdir):
    os.makedirs(os.path.join(tempdir, 'de/LC_MESSAGES'))
    utils.touch(os.path.join(tempdir, 'de/LC_MESSAGES/onegov.test.po'))

    result = list(i18n.pofiles(tempdir))
    assert result[0][0] == 'de'
    assert result[0][1].endswith('onegov.test.po')


def test_get_translations(tempdir):
    os.makedirs(os.path.join(tempdir, 'de/LC_MESSAGES'))
    po = polib.POFile()
    po.append(polib.POEntry(
        msgid=u'Welcome',
        msgstr=u'Willkommen'
    ))
    po.save(os.path.join(tempdir, 'de/LC_MESSAGES/onegov.test.po'))

    os.makedirs(os.path.join(tempdir, 'fr/LC_MESSAGES'))
    po = polib.POFile()
    po.append(polib.POEntry(
        msgid=u'Welcome',
        msgstr=u'Bienvenue'
    ))
    po.save(os.path.join(tempdir, 'fr/LC_MESSAGES/onegov.test.po'))

    os.makedirs(os.path.join(tempdir, 'es/LC_MESSAGES'))
    po = polib.POFile()
    po.append(polib.POEntry(
        msgid=u'Welcome',
        msgstr=u'Bienvenido'
    ))
    po.save(os.path.join(tempdir, 'es/LC_MESSAGES/onegov.somethingelse.po'))

    translations = i18n.get_translations('onegov.somethingelse', tempdir)
    assert list(translations.keys()) == list(['es'])
    translations['es'].gettext(u'Welcome') == u'Bienvenido'

    translations = i18n.get_translations('onegov.test', tempdir)
    assert list(sorted(translations.keys())) == list(sorted(['de', 'fr']))

    translations['de'].gettext(u'Welcome') == u'Willkommen'
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
