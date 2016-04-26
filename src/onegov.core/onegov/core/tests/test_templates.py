import os
import os.path
import polib

from onegov.core import Framework
from onegov.core import utils
from onegov.core.templates import render_macro
from translationstring import TranslationStringFactory
from webtest import TestApp as Client


def test_chameleon_with_translation(temporary_directory):
    # Test chameleon in a real scenario with templating and translations

    templates = os.path.join(temporary_directory, 'templates')
    os.mkdir(templates)

    locale = os.path.join(temporary_directory, 'locale')
    os.makedirs(os.path.join(locale, 'de/LC_MESSAGES'))

    po = polib.POFile()
    po.append(polib.POEntry(
        msgid='Welcome',
        msgstr='Willkommen'
    ))
    po.append(polib.POEntry(
        msgid="We're sinking, we're sinking!",
        msgstr='Wir denken, wir denken!'
    ))
    po.append(polib.POEntry(
        msgid="Macro",
        msgstr="Makro"
    ))
    po.save(os.path.join(locale, 'de/LC_MESSAGES/onegov.test.po'))

    with open(os.path.join(templates, 'index.pt'), 'w') as f:
        f.write("""
            <!DOCTYPE html>
            <html xmlns="http://www.w3.org/1999/xhtml"
                  xmlns:i18n="http://xml.zope.org/namespaces/i18n"
                  xmlns:tal="http://xml.zope.org/namespaces/tal"
                  i18n:domain="onegov.test">
                <b><tal:block i18n:translate="">Welcome</tal:block></b>
                <b>${foo}</b>
                <metal:macro
                    define-macro="testmacro" i18n:domain="onegov.test">
                    <i i18n:translate>Macro</i>
                </metal:macro>
            </html>
        """)

    _ = TranslationStringFactory('onegov.test')

    class App(Framework):
        pass

    @App.template_directory()
    def get_template_directory():
        return templates

    @App.setting(section='i18n', name='localedirs')
    def get_localedirs():
        return [locale]

    @App.setting(section='i18n', name='default_locale')
    def get_i18n_default_locale():
        return 'de'

    @App.path(path='/')
    class Root(object):
        pass

    @App.html(model=Root, template='index.pt')
    def view_root(self, request):
        return {
            'foo': _("We're sinking, we're sinking!")
        }

    @App.view(model=Root, name='macro')
    def view_root_macro(self, request):
        registry = request.app.config.template_engine_registry
        template = registry._template_loaders['.pt']['index.pt']
        template.macros['testmacro']

        return render_macro(template.macros['testmacro'], request, {})

    utils.scan_morepath_modules(App)

    client = Client(App())
    assert '<b>Willkommen</b>' in client.get('/').text
    assert '<b>Wir denken, wir denken!</b>' in client.get('/').text
    assert '<i>Makro</i>' in client.get('/').text

    assert '<b>Willkommen</b>' not in client.get('/macro').text
    assert '<b>Wir denken, wir denken!</b>' not in client.get('/macro').text

    assert '<i>Makro</i>' in client.get('/macro').text
