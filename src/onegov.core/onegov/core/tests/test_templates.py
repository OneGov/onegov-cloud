import morepath
import os
import os.path
import polib

from onegov.core.framework import Framework
from onegov.core import utils
from onegov.core.layout import ChameleonLayout
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


def test_inject_default_vars(temporary_directory):

    templates = os.path.join(temporary_directory, 'templates')
    os.mkdir(templates)

    with open(os.path.join(templates, 'index.pt'), 'w') as f:
        f.write("""
            <!DOCTYPE html>
            <html xmlns="http://www.w3.org/1999/xhtml"
                  xmlns:tal="http://xml.zope.org/namespaces/tal">
                <span>${injected}</span>
                <span tal:condition="parent|nothing">padre</span>
                <span tal:condition="child|nothing">niño</span>
            </html>
        """)

    class Parent(Framework):
        pass

    @Parent.template_directory()
    def get_template_directory():
        return templates

    @Parent.path(path='/')
    class Root(object):
        pass

    @Parent.view(model=Root, template='index.pt')
    def view_root(self, request):
        return {
            'injected': 'foobar'
        }

    @Parent.template_variables()
    def get_parent_template_variables(request):
        return {
            'injected': 'parent',
            'parent': True
        }

    class Child(Parent):
        pass

    @Child.template_variables()
    def get_child_template_variables(request):
        return {
            'injected': 'child',
            'child': True
        }

    utils.scan_morepath_modules(Parent)
    utils.scan_morepath_modules(Child)

    morepath.commit(Child, Parent)

    parent_page = Client(Parent()).get('/')
    assert 'parent' in parent_page
    assert 'child' not in parent_page
    assert 'padre' in parent_page
    assert 'niño' not in parent_page

    child_page = Client(Child()).get('/')
    assert 'parent' not in child_page
    assert 'child' in child_page
    assert 'padre' in child_page
    assert 'niño' in child_page


def test_macro_lookup(temporary_directory):

    parent = os.path.join(temporary_directory, 'parent')
    child = os.path.join(temporary_directory, 'child')

    os.mkdir(parent)
    os.mkdir(child)

    with open(os.path.join(parent, 'index.pt'), 'w') as f:
        f.write("""
            <!DOCTYPE html>
            <html xmlns="http://www.w3.org/1999/xhtml"
                  xmlns:tal="http://xml.zope.org/namespaces/tal"
                  xmlns:metal="http://xml.zope.org/namespaces/metal">
                <metal:block use-macro="layout.macros.foo" />
                <metal:block use-macro="layout.macros.bar" />
                <metal:block use-macro="layout.macros.id" />
            </html>
        """)

    with open(os.path.join(parent, 'macros.pt'), 'w') as f:
        f.write("""
            <!DOCTYPE html>
            <html xmlns="http://www.w3.org/1999/xhtml"
                  xmlns:tal="http://xml.zope.org/namespaces/tal"
                  xmlns:metal="http://xml.zope.org/namespaces/metal">

                <metal:block define-macro="foo">
                    Foo
                </metal:block>

                <metal:block define-macro="id">
                    Parent
                </metal:block>
            </html>
        """)

    with open(os.path.join(child, 'macros.pt'), 'w') as f:
        f.write("""
            <!DOCTYPE html>
            <html xmlns="http://www.w3.org/1999/xhtml"
                  xmlns:tal="http://xml.zope.org/namespaces/tal"
                  xmlns:metal="http://xml.zope.org/namespaces/metal">

                <metal:block define-macro="bar">
                    Bar
                </metal:block>

                <metal:block define-macro="id">
                    Child
                </metal:block>
            </html>
        """)

    class Parent(Framework):
        pass

    @Parent.template_directory()
    def get_parent_template_directory():
        return parent

    @Parent.path(path='/')
    class Root(object):
        pass

    @Parent.view(model=Root, template='index.pt')
    def view_root(self, request):
        return {
            'layout': ChameleonLayout(self, request)
        }

    class Child(Parent):
        pass

    @Child.template_directory()
    def get_child_template_directory():
        return child

    utils.scan_morepath_modules(Parent)
    utils.scan_morepath_modules(Child)

    morepath.commit(Child, Parent)

    page = Client(Child()).get('/')
    assert 'Foo' in page
    assert 'Bar' in page
    assert 'Child' in page
