# -*- coding: utf-8 -*-
import json
import os
import transaction
import pytest

from datetime import datetime, timedelta
from email.header import decode_header
from email.utils import parseaddr
from freezegun import freeze_time
from morepath import setup
from onegov.core import Framework
from onegov.core.upgrade import UpgradeState
from onegov.server import Config, Server
from webtest import TestApp as Client
from wtforms import Form, StringField


def test_set_application_id():
    app = Framework()
    app.namespace = 'namespace'
    app.configure_application()
    app.set_application_id('namespace/id')

    assert app.schema == 'namespace-id'


def test_configure():
    class App(Framework):
        configured = []

        def configure_a(self, **cfg):
            self.configured.append('a')

        def configure_b(self, **cfg):
            self.configured.append('b')

        @property
        def configure_c(self, **cfg):
            self.configured.append('c')

    app = App()
    app.configure_application()

    assert app.configured == ['a', 'b']


def test_virtual_host_request():
    config = setup()

    class App(Framework):
        testing_config = config

    @App.path(path='/')
    class Root(object):
        pass

    @App.path(path='/blog')
    class Blog(object):
        pass

    @App.view(model=Root)
    def view_root(self, request):
        return request.link(self) + ' - root'

    @App.view(model=Blog)
    def view_blog(self, request):
        return request.link(self) + ' - blog'

    config.commit()

    app = App()
    app.configure_application()

    c = Client(app)

    response = c.get('/')
    assert response.body == b'http://localhost/ - root'

    response = c.get('/blog')
    assert response.body == b'http://localhost/blog - blog'

    # X_VHM_HOST is a simple prefix..
    response = c.get('/', headers={'X_VHM_HOST': 'http://example.org'})
    assert response.body == b'http://example.org/ - root'

    response = c.get('/blog', headers={'X_VHM_HOST': 'http://example.org'})
    assert response.body == b'http://example.org/blog - blog'

    # .. though it won't lead to '//'s in the url
    response = c.get('/', headers={'X_VHM_HOST': 'http://example.org/'})
    assert response.body == b'http://example.org/ - root'

    # X_VHM_ROOT set to '/' has no influence
    response = c.get('/', headers={'X_VHM_ROOT': '/'})
    assert response.body == b'http://localhost/ - root'

    # just like X_VHM_HOST it tries to not introduce any '//'s
    response = c.get('/blog', headers={'X_VHM_ROOT': '/blog'})
    assert response.body == b'http://localhost/ - blog'

    response = c.get('/blog', headers={'X_VHM_ROOT': '/blog/'})
    assert response.body == b'http://localhost/ - blog'

    # X_VHM_HOST and X_VHM_ROOT may be used together
    response = c.get('/blog', headers={
        'X_VHM_ROOT': '/blog', 'X_VHM_HOST': 'https://blog.example.org/'})
    assert response.body == b'https://blog.example.org/ - blog'

    response = c.get('/blog', headers={
        'X_VHM_ROOT': '/blog',
        'X_VHM_HOST': 'https://blog.example.org/'})
    assert response.body == b'https://blog.example.org/ - blog'


def test_registered_upgrade_tasks(postgres_dsn):

    app = Framework()

    app.configure_application(dsn=postgres_dsn)
    app.namespace = 'foo'
    app.set_application_id('foo/bar')

    assert app.session().query(UpgradeState).count() > 0


def test_browser_session_request():
    config = setup()

    class App(Framework):
        testing_config = config

    @App.path(path='/')
    class Root(object):
        pass

    @App.view(model=Root)
    def view_root(self, request):
        # the session id is only available if there's a change in the
        # browser session
        request.browser_session['foo'] = 'bar'
        return request.cookies['session_id']

    @App.view(model=Root, name='login')
    def view_login(self, request):
        request.browser_session.logged_in = True
        return 'logged in'

    @App.view(model=Root, name='status')
    def view_status(self, request):
        if request.browser_session.has('logged_in'):
            return 'logged in'
        else:
            return 'logged out'

    config.commit()

    app = App()
    app.application_id = 'test'
    app.configure_application(identity_secure=False)  # allow http

    app.cache_backend = 'dogpile.cache.memory'
    app.cache_backend_arguments = {}

    c1 = Client(app)
    c2 = Client(app)

    c1.get('/').text == c1.get('/').text
    c1.get('/').text != c2.get('/').text
    c2.get('/').text == c2.get('/').text

    c1.get('/status').text == 'logged out'
    c2.get('/status').text == 'logged out'

    c1.get('/login')

    c1.get('/status').text == 'logged in'
    c2.get('/status').text == 'logged out'

    app.application_id = 'tset'
    c1.get('/status').text == 'logged out'

    app.application_id = 'test'
    c1.get('/status').text == 'logged in'


def test_browser_session_dirty():
    config = setup()

    class App(Framework):
        testing_config = config

    @App.path(path='/')
    class Root(object):
        pass

    @App.view(model=Root, name='undirty')
    def view_undirty(self, request):
        request.browser_session.get('foo')
        return ''

    @App.view(model=Root, name='dirty')
    def view_dirty(self, request):
        request.browser_session['foo'] = 'bar'
        return ''

    config.commit()

    app = App()
    app.application_id = 'test'
    app.configure_application(identity_secure=False)  # allow http

    app.cache_backend = 'dogpile.cache.memory'
    app.cache_backend_arguments = {}

    client = Client(app)

    client.get('/undirty')
    assert 'session_id' not in client.cookies

    client.get('/dirty')
    assert 'session_id' in client.cookies

    old_session_id = client.cookies['session_id']

    client.get('/undirty')
    assert client.cookies['session_id'] == old_session_id

    client.get('/undirty')
    assert client.cookies['session_id'] == old_session_id


def test_request_messages():
    config = setup()

    class App(Framework):
        testing_config = config

    @App.path(path='/')
    class Root(object):
        pass

    class Message(object):
        def __init__(self, text, type):
            self.text = text
            self.type = type

    @App.path(model=Message, path='/messages')
    def get_message(text, type):
        return Message(text, type)

    @App.view(model=Message, name='add')
    def view_add_message(self, request):
        request.message(self.text, self.type)

    @App.view(model=Root)
    def view_root(self, request):
        return json.dumps(list(request.consume_messages()))

    config.commit()

    app = App()
    app.application_id = 'test'
    app.configure_application(identity_secure=False)  # allow http

    app.cache_backend = 'dogpile.cache.memory'
    app.cache_backend_arguments = {}

    c1 = Client(app)
    c2 = Client(app)
    c1.get('/messages/add?text=one&type=info')
    c1.get('/messages/add?text=two&type=warning')
    c2.get('/messages/add?text=three&type=error')

    messages = json.loads(c1.get('/').text)
    assert len(messages) == 2
    assert messages[0][0] == 'one'
    assert messages[1][0] == 'two'
    assert messages[0][1] == 'info'
    assert messages[1][1] == 'warning'

    messages = json.loads(c1.get('/').text)
    assert len(messages) == 0

    messages = json.loads(c2.get('/').text)
    assert len(messages) == 1

    assert messages[0][0] == 'three'
    assert messages[0][1] == 'error'

    messages = json.loads(c2.get('/').text)
    assert len(messages) == 0


def test_fix_webassets_url():
    config = setup()

    import onegov.core
    import more.transaction
    import more.webassets
    config.scan(more.transaction)
    config.scan(more.webassets)
    config.scan(onegov.core)
    config.commit()

    class App(Framework):
        testing_config = config

    @App.path(path='/')
    class Root(object):
        pass

    @App.html(model=Root)
    def view_root(self, request):
        return '/' + request.app.webassets_url + '/jquery.js'

    config.commit()

    class TestServer(Server):

        def configure_morepath(self, *args, **kwargs):
            pass

    server = TestServer(Config({
        'applications': [
            {
                'path': '/towns/*',
                'application': App,
                'namespace': 'towns'
            }
        ]
    }))

    client = Client(server)

    # more.webassets doesn't know about virtual hosting (that is to say
    # Morepath does not know about it).
    #
    # Since it wants to create urls for the root of the application ('/'),
    # it will create something like '/xxx/jquery.js'
    #
    # We really want '/towns/test/xxx' here, which is something the onegov
    # core Framework application fixes through a tween.
    response = client.get('/towns/test')
    assert response.body == (b'http://localhost/towns/test/'
                             b'7da9c72a3b5f9e060b898ef7cd714b8a/jquery.js')


def test_sign_unsign():
    framework = Framework()
    framework.identity_secret = 'test'
    framework.application_id = 'one'

    assert framework.sign('foo').startswith('foo.')
    assert framework.unsign(framework.sign('foo')) == 'foo'

    signed_by_one = framework.sign('foo')
    framework.application_id = 'two'
    assert framework.unsign(signed_by_one) is None
    framework.application_id = 'one'
    assert framework.unsign(signed_by_one) == 'foo'

    signed = framework.sign('foo')
    framework.identity_secret = 'asdf'
    assert framework.unsign(signed) is None

    signed = framework.sign('foo')
    framework.unsign('bar' + signed) is None


def test_csrf_secret_key():
    app = Framework()

    with pytest.raises(AssertionError):
        app.configure_application(identity_secret='test', csrf_secret='test')

    with pytest.raises(AssertionError):
        app.configure_application(identity_secret='very-secret-key')

    with pytest.raises(AssertionError):
        app.configure_application(csrf_secret='another-very-secret-key')

    app.configure_application(identity_secret='x', csrf_secret='y')


def test_csrf():

    class MyForm(Form):
        name = StringField(u'Name')

    config = setup()

    class App(Framework):
        testing_config = config

    @App.path(path='/')
    class Root(object):
        pass

    @App.view(model=Root, request_method='GET')
    def view_get_root(self, request):
        form = request.get_form(MyForm, i18n_support=False)
        return form.csrf_token._value()

    @App.view(model=Root, request_method='POST')
    def view_post_root(self, request):
        if request.get_form(MyForm, i18n_support=False).validate():
            return 'success'
        else:
            return 'fail'

    config.commit()

    app = App()
    app.application_id = 'test'
    app.configure_application(
        identity_secure=False,
        disable_memcached=True,
        csrf_time_limit=60
    )

    client = Client(app)
    csrf_token = client.get('/').text
    assert client.post('/', {'csrf_token': csrf_token}).text == 'success'
    assert client.post('/', {'csrf_token': csrf_token + 'x'}).text == 'fail'
    assert client.post('/', {'csrf_token': csrf_token}).text == 'success'

    with freeze_time(datetime.now() + timedelta(minutes=2)):
        assert client.post('/', {'csrf_token': csrf_token}).text == 'fail'


def test_send_email(smtpserver):

    app = Framework()
    app.mail_host, app.mail_port = smtpserver.addr
    app.mail_sender = 'noreply@example.org'
    app.mail_force_tls = False
    app.mail_username = None
    app.mail_password = None
    app.mail_use_directory = False

    app.send_email(
        reply_to='info@example.org',
        receivers=['recipient@example.org'],
        subject="Test E-Mail",
        content="This e-mail is just a test"
    )

    transaction.commit()

    assert len(smtpserver.outbox) == 1
    message = smtpserver.outbox[0]

    assert message['Sender'] == 'noreply@example.org'
    assert message['From'] == 'noreply@example.org'
    assert message['Reply-To'] == 'info@example.org'
    assert message['Subject'] == 'Test E-Mail'
    assert message.get_payload()[0].as_string() == (
        'Content-Type: text/html; charset="utf-8"\n'
        'MIME-Version: 1.0\n'
        'Content-Transfer-Encoding: base64\n\n'
        'VGhpcyBlLW1haWwgaXMganVzdCBhIHRlc3Q=\n'
    )


def test_send_email_with_name(smtpserver):

    app = Framework()
    app.mail_host, app.mail_port = smtpserver.addr
    app.mail_sender = 'noreply@example.org'
    app.mail_force_tls = False
    app.mail_username = None
    app.mail_password = None
    app.mail_use_directory = False

    app.send_email(
        reply_to='Govikon <info@example.org>',
        receivers=['recipient@example.org'],
        subject="Test E-Mail",
        content="This e-mail is just a test"
    )

    transaction.commit()

    assert len(smtpserver.outbox) == 1
    message = smtpserver.outbox[0]

    assert message['Sender'] == 'Govikon <noreply@example.org>'
    assert message['From'] == 'Govikon <noreply@example.org>'
    assert message['Reply-To'] == 'Govikon <info@example.org>'
    assert message['Subject'] == 'Test E-Mail'
    assert message.get_payload()[0].as_string() == (
        'Content-Type: text/html; charset="utf-8"\n'
        'MIME-Version: 1.0\n'
        'Content-Transfer-Encoding: base64\n\n'
        'VGhpcyBlLW1haWwgaXMganVzdCBhIHRlc3Q=\n'
    )


def test_send_email_to_maildir(temporary_directory):

    app = Framework()
    app.mail_sender = 'noreply@example.org'
    app.mail_use_directory = True
    app.mail_directory = temporary_directory

    app.send_email(
        reply_to='Govikon <info@example.org>',
        receivers=['recipient@example.org'],
        subject="Test E-Mail",
        content="This e-mail is just a test"
    )

    assert not os.listdir(temporary_directory)

    transaction.commit()

    assert set(os.listdir(temporary_directory)) == {'cur', 'new', 'tmp'}

    new_emails = os.path.join(temporary_directory, 'new')
    assert len(os.listdir(new_emails)) == 1

    new_email = os.path.join(new_emails, os.listdir(new_emails)[0])
    with open(new_email, 'r') as f:
        email = f.read()

    assert 'Subject: Test E-Mail' in email
    assert 'Reply-To: Govikon <info@example.org>' in email
    assert 'From: Govikon <noreply@example.org>' in email
    assert 'Sender: Govikon <noreply@example.org>' in email
    assert 'To: recipient@example.org' in email


def test_send_email_is_8859_1(smtpserver):
    app = Framework()
    app.mail_host, app.mail_port = smtpserver.addr
    app.mail_sender = u'noreply@example.org'
    app.mail_force_tls = False
    app.mail_username = None
    app.mail_password = None
    app.mail_use_directory = False

    app.send_email(
        reply_to=u'Gövikon <info@example.org>',
        receivers=[u'recipient@example.org'],
        subject=u"Nüws",
        content=u"This e-mäil is just a test"
    )

    assert len(smtpserver.outbox) == 0
    transaction.commit()

    assert len(smtpserver.outbox) == 1
    message = smtpserver.outbox[0]

    def decode(header):
        name, addr = parseaddr(header)

        try:
            name = decode_header(name)[0][0].decode('utf-8')
        except AttributeError:
            pass

        return name, addr

    assert decode(message['Sender']) == (u"Gövikon", 'noreply@example.org')
    assert decode(message['From']) == (u"Gövikon", 'noreply@example.org')
    assert decode(message['Reply-To']) == (u"Gövikon", 'info@example.org')

    assert decode_header(message['Subject'])[0][0].decode('utf-8') \
        == u"Nüws"

    assert message.get_payload()[0].as_string() == (
        'Content-Type: text/html; charset="utf-8"\n'
        'MIME-Version: 1.0\n'
        'Content-Transfer-Encoding: base64\n\n'
        'VGhpcyBlLW3DpGlsIGlzIGp1c3QgYSB0ZXN0\n'
    )


def test_send_email_unicode(smtpserver):
    app = Framework()
    app.mail_host, app.mail_port = smtpserver.addr
    app.mail_sender = u'noreply@example.org'
    app.mail_force_tls = False
    app.mail_username = None
    app.mail_password = None
    app.mail_use_directory = False

    app.send_email(
        reply_to=u'👴 <info@example.org>',
        receivers=[u'recipient@example.org'],
        subject=u"👍",
        content=u"👍"
    )

    assert len(smtpserver.outbox) == 0
    transaction.commit()

    assert len(smtpserver.outbox) == 1
    message = smtpserver.outbox[0]

    def decode(header):
        name, addr = parseaddr(header)

        try:
            name = decode_header(name)[0][0].decode('utf-8')
        except AttributeError:
            pass

        return name, addr

    assert decode(message['Sender']) == (u"👴", 'noreply@example.org')
    assert decode(message['From']) == (u"👴", 'noreply@example.org')
    assert decode(message['Reply-To']) == (u"👴", 'info@example.org')
    assert decode_header(message['Subject'])[0][0].decode('utf-8') == u"👍"

    assert message.get_payload()[0].as_string() == (
        'Content-Type: text/html; charset="utf-8"\n'
        'MIME-Version: 1.0\n'
        'Content-Transfer-Encoding: base64\n\n'
        '8J+RjQ==\n'
    )


def test_object_by_path():
    config = setup()

    class App(Framework):
        testing_config = config

    @App.path(path='/')
    class Root(object):
        pass

    @App.path(path='/pages', absorb=True)
    class Page(object):
        def __init__(self, absorb):
            self.absorb = absorb

    config.commit()

    app = App()
    assert isinstance(app.object_by_path('/'), Root)
    assert isinstance(app.object_by_path('https://www.example.org/'), Root)

    page = app.object_by_path('/pages/foo/bar')
    assert page.absorb == 'foo/bar'
    assert isinstance(page, Page)

    assert app.object_by_path('/pages').absorb == ''

    # works, because 'foobar' is a view of the root
    assert isinstance(app.object_by_path('/foobar'), Root)
    assert app.object_by_path('/asdf/asdf') is None


def test_send_email_transaction(smtpserver):
    config = setup()

    import more.transaction
    import more.webassets
    import onegov.core

    config.scan(more.transaction)
    config.scan(more.webassets)
    config.scan(onegov.core)

    class App(Framework):
        testing_config = config

    @App.path(path='/')
    class Root(object):
        pass

    @App.view(model=Root, name='send-fail')
    def fail_send(self, request):
        app.send_email(
            reply_to=u'Gövikon <info@example.org>',
            receivers=[u'recipient@example.org'],
            subject=u"Nüws",
            content=u"This e-mäil is just a test"
        )
        assert False

    @App.view(model=Root, name='send-ok')
    def success_send(self, request):
        app.send_email(
            reply_to=u'Gövikon <info@example.org>',
            receivers=[u'recipient@example.org'],
            subject=u"Nüws",
            content=u"This e-mäil is just a test"
        )

    config.commit()

    app = App()
    app.application_id = 'test'
    app.configure_application(identity_secure=False)  # allow http
    app.mail_host, app.mail_port = smtpserver.addr
    app.mail_sender = u'noreply@example.org'
    app.mail_force_tls = False
    app.mail_username = None
    app.mail_password = None
    app.mail_use_directory = False

    app.cache_backend = 'dogpile.cache.memory'
    app.cache_backend_arguments = {}

    client = Client(app)

    with pytest.raises(AssertionError):
        client.get('/send-fail')

    assert len(smtpserver.outbox) == 0

    client.get('/send-ok')
    assert len(smtpserver.outbox) == 1
