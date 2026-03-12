from __future__ import annotations

import morepath
import os
import os.path
import polib

from onegov.core import utils
from onegov.core.framework import Framework
from onegov.core.layout import ChameleonLayout
from onegov.core.templates import render_macro, PageTemplate, PageTemplateFile
from translationstring import TranslationStringFactory
from webtest import TestApp as Client


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.request import CoreRequest
    from onegov.core.types import RenderData


def test_chameleon_with_translation(
    temporary_directory: str,
    redis_url: str
) -> None:
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
    def get_template_directory() -> str:
        return templates

    @App.setting(section='i18n', name='localedirs')
    def get_localedirs() -> list[str]:
        return [locale]

    @App.setting(section='i18n', name='default_locale')
    def get_i18n_default_locale() -> str:
        return 'de'

    @App.path(path='/')
    class Root:
        pass

    @App.html(model=Root, template='index.pt')
    def view_root(self: Root, request: CoreRequest) -> RenderData:
        return {
            'foo': _("We're sinking, we're sinking!")
        }

    @App.view(model=Root, name='macro')
    def view_root_macro(self: Root, request: CoreRequest) -> str:
        registry = request.app.config.template_engine_registry
        template = registry._template_loaders['.pt']['index.pt']
        template.macros['testmacro']

        return render_macro(template.macros['testmacro'], request, {})

    utils.scan_morepath_modules(App)

    app = App()
    app.namespace = 'foo'
    app.configure_application(redis_url=redis_url)
    app.set_application_id('foo/bar')

    client = Client(app)
    assert '<b>Willkommen</b>' in client.get('/').text
    assert '<b>Wir denken, wir denken!</b>' in client.get('/').text
    assert '<i>Makro</i>' in client.get('/').text

    assert '<b>Willkommen</b>' not in client.get('/macro').text
    assert '<b>Wir denken, wir denken!</b>' not in client.get('/macro').text

    assert '<i>Makro</i>' in client.get('/macro').text


def test_inject_default_vars(temporary_directory: str, redis_url: str) -> None:

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
    def get_template_directory() -> str:
        return templates

    @Parent.path(path='/')
    class Root:
        pass

    @Parent.view(model=Root, template='index.pt')
    def view_root(self: Root, request: CoreRequest) -> RenderData:
        return {
            'injected': 'foobar'
        }

    @Parent.template_variables()
    def get_parent_template_variables(request: CoreRequest) -> RenderData:
        return {
            'injected': 'parent',
            'parent': True
        }

    class Child(Parent):
        pass

    @Child.template_variables()
    def get_child_template_variables(request: CoreRequest) -> RenderData:
        return {
            'injected': 'child',
            'child': True
        }

    utils.scan_morepath_modules(Parent)
    utils.scan_morepath_modules(Child)

    morepath.commit(Child, Parent)

    parent = Parent()
    parent.namespace = 'foo'
    parent.configure_application(redis_url=redis_url)
    parent.set_application_id('foo/parent')

    child = Child()
    child.namespace = 'foo'
    child.configure_application(redis_url=redis_url)
    child.set_application_id('foo/child')

    parent_page = Client(parent).get('/')
    assert 'parent' in parent_page
    assert 'child' not in parent_page
    assert 'padre' in parent_page
    assert 'niño' not in parent_page

    child_page = Client(child).get('/')
    assert 'parent' not in child_page
    assert 'child' in child_page
    assert 'padre' in child_page
    assert 'niño' in child_page


def test_macro_lookup(temporary_directory: str, redis_url: str) -> None:

    parent = os.path.join(temporary_directory, 'parent')
    child_dir = os.path.join(temporary_directory, 'child')

    os.mkdir(parent)
    os.mkdir(child_dir)

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
                <metal:block define-macro="foo">Foo</metal:block>
                <metal:block define-macro="id">Parent</metal:block>
            </html>
        """)

    with open(os.path.join(child_dir, 'macros.pt'), 'w') as f:
        f.write("""
            <!DOCTYPE html>
            <html xmlns="http://www.w3.org/1999/xhtml"
                  xmlns:tal="http://xml.zope.org/namespaces/tal"
                  xmlns:metal="http://xml.zope.org/namespaces/metal">
                <metal:block define-macro="bar">Bar</metal:block>
                <metal:block define-macro="id">Child</metal:block>
            </html>
        """)

    class Parent(Framework):
        pass

    @Parent.template_directory()
    def get_parent_template_directory() -> str:
        return parent

    @Parent.path(path='/')
    class Root:
        pass

    @Parent.view(model=Root, template='index.pt')
    def view_root(self: Root, request: CoreRequest) -> RenderData:
        return {
            'layout': ChameleonLayout(self, request)
        }

    class Child(Parent):
        pass

    @Child.template_directory()
    def get_child_template_directory() -> str:
        return child_dir

    utils.scan_morepath_modules(Parent)
    utils.scan_morepath_modules(Child)

    morepath.commit(Child, Parent)

    child = Child()
    child.namespace = 'foo'
    child.configure_application(redis_url=redis_url)
    child.set_application_id('foo/child')

    page = Client(child).get('/')
    assert 'Foo' in page
    assert 'Bar' in page
    assert 'Child' in page


def test_boolean_attributes(temporary_directory: str, redis_url: str) -> None:
    select = """
    <select>
        <option value="1" tal:attributes="selected True"></option>
        <option value="2" tal:attributes="selected False"></option>
        <option value="3" tal:attributes="selected None"></option>
    </select>
    """

    radio_1 = """
    <input type="radio" value="1" tal:attributes="checked True">
    <input type="radio" value="2" tal:attributes="checked False">
    <input type="radio" value="3" tal:attributes="checked None">
    """

    radio_2 = """
    <input type="radio" value="4" tal:attributes="disabled True">
    <input type="radio" value="5" tal:attributes="disabled False">
    <input type="radio" value="6" tal:attributes="disabled None">
    """

    # PageTemplate
    rendered = PageTemplate(select + radio_1 + radio_2)()
    assert '<option value="1" selected="selected"></option>' in rendered
    assert '<option value="2"></option>' in rendered
    assert '<option value="3"></option>' in rendered
    assert '<input type="radio" value="1" checked="checked">' in rendered
    assert '<input type="radio" value="2">' in rendered
    assert '<input type="radio" value="3">' in rendered
    assert '<input type="radio" value="4" disabled="disabled">' in rendered
    assert '<input type="radio" value="5">' in rendered
    assert '<input type="radio" value="6">' in rendered

    # PageTemplateFile
    template = os.path.join(temporary_directory, 'template.pt')
    with open(template, 'w') as f:
        f.write(select + radio_1 + radio_2)
    rendered = PageTemplateFile(template)()
    assert '<option value="1" selected="selected"></option>' in rendered
    assert '<option value="2"></option>' in rendered
    assert '<option value="3"></option>' in rendered
    assert '<input type="radio" value="1" checked="checked">' in rendered
    assert '<input type="radio" value="2">' in rendered
    assert '<input type="radio" value="3">' in rendered
    assert '<input type="radio" value="4" disabled="disabled">' in rendered
    assert '<input type="radio" value="5">' in rendered
    assert '<input type="radio" value="6">' in rendered

    # PageTemplateLoader
    parent_dir = os.path.join(temporary_directory, 'parent')
    child_dir = os.path.join(temporary_directory, 'child')

    os.mkdir(parent_dir)
    os.mkdir(child_dir)

    with open(os.path.join(parent_dir, 'index.pt'), 'w') as f:
        f.write(f"""
            <!DOCTYPE html>
            <html xmlns="http://www.w3.org/1999/xhtml"
                  xmlns:tal="http://xml.zope.org/namespaces/tal"
                  xmlns:metal="http://xml.zope.org/namespaces/metal">
                <metal:block use-macro="layout.macros.radio" />
                {select}
            </html>
        """)

    with open(os.path.join(parent_dir, 'macros.pt'), 'w') as f:
        f.write(f"""
            <!DOCTYPE html>
            <html xmlns="http://www.w3.org/1999/xhtml"
                  xmlns:tal="http://xml.zope.org/namespaces/tal"
                  xmlns:metal="http://xml.zope.org/namespaces/metal">
                <metal:block define-macro="radio">{radio_1}</metal:block>
            </html>
        """)

    with open(os.path.join(child_dir, 'macros.pt'), 'w') as f:
        f.write(f"""
            <!DOCTYPE html>
            <html xmlns="http://www.w3.org/1999/xhtml"
                  xmlns:tal="http://xml.zope.org/namespaces/tal"
                  xmlns:metal="http://xml.zope.org/namespaces/metal">
                <metal:block define-macro="radio">
                    <tal:block metal:define-slot="slot" />
                    {radio_2}
                </metal:block>
            </html>
        """)

    with open(os.path.join(child_dir, 'slot.pt'), 'w') as f:
        f.write(f"""
            <!DOCTYPE html>
            <html xmlns="http://www.w3.org/1999/xhtml"
                  xmlns:tal="http://xml.zope.org/namespaces/tal"
                  xmlns:metal="http://xml.zope.org/namespaces/metal">
                <metal:block use-macro="layout.macros.radio">
                    <tal:block metal:fill-slot="slot">{radio_1}</tal:block>
                </metal:block>
                {select}
            </html>
        """)

    class Parent(Framework):
        pass

    @Parent.template_directory()
    def get_parent_template_directory() -> str:
        return parent_dir

    @Parent.path(path='/')
    class Root:
        pass

    @Parent.view(model=Root, template='index.pt')
    def view_root(self: Root, request: CoreRequest) -> RenderData:
        return {
            'layout': ChameleonLayout(self, request)
        }

    class Child(Parent):
        pass

    @Child.template_directory()
    def get_child_template_directory() -> str:
        return child_dir

    @Child.view(model=Root, name='slot', template='slot.pt')
    def view_slot(self: Root, request: CoreRequest) -> RenderData:
        return {
            'layout': ChameleonLayout(self, request)
        }

    utils.scan_morepath_modules(Parent)
    utils.scan_morepath_modules(Child)

    morepath.commit(Child, Parent)

    parent = Parent()
    parent.namespace = 'parent'
    parent.configure_application(redis_url=redis_url)
    parent.set_application_id('parent/parent')

    page = Client(parent).get('/')
    assert '<option value="1" selected="selected"></option>' in page
    assert '<option value="2"></option>' in page
    assert '<option value="3"></option>' in page
    assert '<input type="radio" value="1" checked="checked">' in page
    assert '<input type="radio" value="2">' in page
    assert '<input type="radio" value="3">' in page

    child = Child()
    child.namespace = 'child'
    child.configure_application(redis_url=redis_url)
    child.set_application_id('child/child')

    page = Client(child).get('/')
    assert '<input type="radio" value="4" disabled="disabled">' in page
    assert '<input type="radio" value="5">' in page
    assert '<input type="radio" value="6">' in page
    assert '<option value="1" selected="selected"></option>' in page
    assert '<option value="2"></option>' in page
    assert '<option value="3"></option>' in page

    page = Client(child).get('/slot')
    assert '<input type="radio" value="1" checked="checked">' in page
    assert '<input type="radio" value="2">' in page
    assert '<input type="radio" value="3">' in page
    assert '<input type="radio" value="4" disabled="disabled">' in page
    assert '<input type="radio" value="5">' in page
    assert '<input type="radio" value="6">' in page
    assert '<option value="1" selected="selected"></option>' in page
    assert '<option value="2"></option>' in page
    assert '<option value="3"></option>' in page
