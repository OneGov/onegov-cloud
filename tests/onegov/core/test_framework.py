import morepath
import os
import transaction
import pytest

from base64 import b64encode
from cached_property import cached_property
from datetime import datetime, timedelta
from freezegun import freeze_time
from gettext import NullTranslations
from itsdangerous import BadSignature, Signer
from onegov.core.custom import json
from onegov.core.framework import Framework
from onegov.core.html import html_to_text
from onegov.core.i18n import translation_chain
from onegov.core.mail import Attachment
from onegov.core.redirect import Redirect
from onegov.core.upgrade import UpgradeState
from onegov.server import Config, Server
from tempfile import NamedTemporaryFile
from unittest.mock import patch
from urllib.parse import parse_qsl
from webtest import TestApp as Client
from wtforms import Form, StringField
from wtforms.validators import InputRequired


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


def test_virtual_host_request(redis_url):

    class App(Framework):
        pass

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

    app = App()
    app.namespace = 'foo'
    app.configure_application(redis_url=redis_url)
    app.set_application_id('foo/bar')

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


def test_browser_session_request(redis_url):

    class App(Framework):
        pass

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

    app = App()
    app.application_id = 'test'
    app.configure_application(identity_secure=False, redis_url=redis_url)

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


def test_browser_session_dirty(redis_url):

    class App(Framework):
        pass

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

    app = App()
    app.application_id = 'test'
    app.configure_application(identity_secure=False, redis_url=redis_url)

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


def test_request_messages(redis_url):

    class App(Framework):
        pass

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

    app = App()
    app.application_id = 'test'
    app.configure_application(identity_secure=False, redis_url=redis_url)

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


def test_fix_webassets_url(redis_url):

    import onegov.core
    import more.transaction
    import more.webassets
    morepath.scan(more.transaction)
    morepath.scan(more.webassets)
    morepath.scan(onegov.core)

    class App(Framework):
        pass

    @App.path(path='/')
    class Root(object):
        pass

    @App.html(model=Root)
    def view_root(self, request):
        return '/' + request.app.config.webasset_registry.url + '/jquery.js'

    class TestServer(Server):

        def configure_morepath(self, *args, **kwargs):
            pass

    server = TestServer(Config({
        'applications': [
            {
                'path': '/towns/*',
                'application': App,
                'namespace': 'towns',
                'configuration': {
                    'redis_url': redis_url
                }
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
    framework.unsafe_identity_secret = 'test'
    framework.application_id = 'one'

    assert framework.sign('foo').startswith('foo.')
    assert framework.unsign(framework.sign('foo')) == 'foo'

    signed_by_one = framework.sign('foo')
    framework.application_id = 'two'
    assert framework.unsign(signed_by_one) is None
    framework.application_id = 'one'
    assert framework.unsign(signed_by_one) == 'foo'

    signed = framework.sign('foo')
    framework.unsafe_identity_secret = 'asdf'
    assert framework.unsign(signed) is None

    signed = framework.sign('foo')
    framework.unsign('bar' + signed) is None


def test_custom_signer():
    framework = Framework()
    framework.unsafe_identity_secret = 'test'
    framework.application_id = 'one'

    signed = Signer(framework.identity_secret).sign(b'foobar')
    assert Signer(framework.identity_secret).unsign(signed) == b'foobar'

    signed = Signer(framework.identity_secret).sign(b'foobar')
    assert Signer(framework.identity_secret).unsign(signed) == b'foobar'

    framework.application_id = 'two'

    with pytest.raises(BadSignature):
        Signer(framework.identity_secret).unsign(signed)


def test_csrf_secret_key():
    app = Framework()

    with pytest.raises(AssertionError):
        app.configure_application(identity_secret='test', csrf_secret='test')

    with pytest.raises(AssertionError):
        app.configure_application(identity_secret='very-secret-key')

    with pytest.raises(AssertionError):
        app.configure_application(csrf_secret='another-very-secret-key')

    app.configure_application(identity_secret='x', csrf_secret='y')


def test_csrf(redis_url):

    class MyForm(Form):
        name = StringField('Name')

    class App(Framework):
        pass

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

    app = App()
    app.application_id = 'test'
    app.configure_application(
        identity_secure=False,
        csrf_time_limit=60,
        redis_url=redis_url
    )

    client = Client(app)
    csrf_token = client.get('/').text
    assert client.post('/', {'csrf_token': csrf_token}).text == 'success'
    assert client.post('/', {'csrf_token': csrf_token + 'x'}).text == 'fail'
    assert client.post('/', {'csrf_token': csrf_token}).text == 'success'

    with freeze_time(datetime.now() + timedelta(minutes=2)):
        assert client.post('/', {'csrf_token': csrf_token}).text == 'fail'


def test_get_form(redis_url):

    class PlainForm(Form):
        called = False

    class OnRequestForm(Form):
        def on_request(self):
            self.called = True

    class App(Framework):
        pass

    @App.path(path='/')
    class Root(object):
        pass

    @App.form(model=Root, form=PlainForm, name='plain')
    def view_get_plain(self, request, form):
        return form.called and 'called' or 'not-called'
        assert form.model is self
        assert form.request is request

    @App.form(model=Root, form=OnRequestForm, name='on-request')
    def view_get_on_request(self, request, form):
        return form.called and 'called' or 'not-called'
        assert form.model is self
        assert form.request is request

    App.commit()

    app = App()
    app.application_id = 'test'
    app.configure_application(
        identity_secure=False,
        csrf_time_limit=60,
        redis_url=redis_url,
    )

    client = Client(app)
    assert client.get('/plain').text == 'not-called'
    assert client.get('/on-request').text == 'called'


def test_get_localized_form(redis_url):

    class LocalizedForm(Form):
        name = StringField('Name', validators=[InputRequired()])

    class App(Framework):
        locales = {}
        default_locale = None

    @App.path(path='/')
    class Root(object):
        pass

    @App.form(model=Root, form=LocalizedForm, name='form')
    def view_get_form(self, request, form):
        assert form.model is self
        assert form.request is request
        assert form.validate() == False
        return form.errors['name'][0]

    App.commit()

    app = App()
    app.application_id = 'test'
    app.configure_application(
        identity_secure=False,
        csrf_time_limit=60,
        redis_url=redis_url
    )

    client = Client(app)
    assert client.get('/form').text == 'This field is required.'

    App.locales = {'de'}
    assert client.get('/form').text == 'This field is required.'

    App.default_locale = 'de'
    assert client.get('/form').text == 'Dieses Feld wird benötigt.'


def test_fixed_translation_chain_length(redis_url):

    def translation_chain_length(form):
        return sum(1 for t in translation_chain(form.meta._translations))

    class LocalizedForm(Form):
        name = StringField('Name', validators=[InputRequired()])

    class App(Framework):
        locales = {'de'}
        default_locale = 'de'
        translation_chain_length = None

        @cached_property
        def translations(self):
            return {'de': NullTranslations()}

    @App.path(path='/')
    class Root(object):
        pass

    @App.form(model=Root, form=LocalizedForm, name='form')
    def view_get_form(self, request, form):
        form.validate()
        request.app.translation_chain_length = translation_chain_length(form)

    App.commit()

    app = App()
    app.application_id = 'test'
    app.configure_application(
        identity_secure=False,
        csrf_time_limit=60,
        redis_url=redis_url
    )

    client = Client(app)

    client.get('/form')
    initial_length = app.translation_chain_length

    client.get('/form')
    assert app.translation_chain_length == initial_length


def test_send_email(tmpdir):

    maildir = tmpdir.mkdir('mail')
    app = Framework()

    app.mail = {
        'marketing': {
            'directory': str(maildir),
            'sender': 'noreply@example.org'
        }
    }

    app.send_email(
        reply_to='info@example.org',
        receivers=['recipient@example.org'],
        subject="Test E-Mail",
        content='This e-mail is just a test. '
        '<a href="mailto:unsubscribe@example.org">unsubscribe</a>',
        headers={'List-Unsubscribe': '<mailto:unsubscribe@example.org>'}
    )

    transaction.commit()

    files = maildir.listdir()
    assert len(files) == 1
    messages = json.loads(files[0].read_text('utf-8'))
    assert len(messages) == 1
    message = messages[0]

    assert message['From'] == 'noreply@example.org'
    assert message['ReplyTo'] == 'info@example.org'
    assert message['Subject'] == 'Test E-Mail'
    assert message['MessageStream'] == 'marketing'
    headers = {h['Name']: h['Value'] for h in message['Headers']}
    assert headers['List-Unsubscribe'] == '<mailto:unsubscribe@example.org>'


def test_send_email_with_name(tmpdir):

    maildir = tmpdir.mkdir('mail')
    app = Framework()
    app.mail = {
        'transactional': {
            'directory': str(maildir),
            'sender': 'noreply@example.org'
        }
    }

    app.send_email(
        reply_to='Govikon <info@example.org>',
        receivers=['recipient@example.org'],
        subject="Test E-Mail",
        content="This e-mail is just a test",
        category='transactional'
    )

    transaction.commit()

    files = maildir.listdir()
    assert len(files) == 1
    messages = json.loads(files[0].read_text('utf-8'))
    assert len(messages) == 1
    message = messages[0]

    assert message['From'] == 'Govikon <noreply@example.org>'
    assert message['ReplyTo'] == 'Govikon <info@example.org>'
    assert message['Subject'] == 'Test E-Mail'


def test_email_attachments(tmpdir):

    maildir = tmpdir.mkdir('mail')
    app = Framework()
    app.mail = {
        'transactional': {
            'directory': str(maildir),
            'sender': 'noreply@example.org'
        }
    }

    tempfile = NamedTemporaryFile(suffix='.txt', mode='w', delete=False)
    tempfile.write('First')
    tempfile.close()
    attachments = [tempfile.name]

    attachment = Attachment(
        'at.txt', content='Second', content_type='text/custom'
    )
    attachments.append(attachment)

    app.send_email(
        reply_to='Govikon <info@example.org>',
        receivers=['recipient@example.org'],
        subject="Test E-Mail",
        content="This e-mail is just a test",
        attachments=attachments,
        category='transactional'
    )
    transaction.commit()
    files = maildir.listdir()
    messages = json.loads(files[0].read_text('utf-8'))
    assert len(messages) == 1
    message = messages[0]

    attachments = message['Attachments']
    assert len(attachments) == 2
    assert attachments[0]['Name'] == os.path.basename(tempfile.name)
    assert attachments[0]['Content'] == b64encode(
        'First'.encode('utf-8')
    ).decode('utf-8')
    assert attachments[0]['ContentType'] == 'text/plain'
    assert attachments[1]['Name'] == 'at.txt'
    assert attachments[1]['Content'] == b64encode(
        'Second'.encode('utf-8')
    ).decode('utf-8')
    assert attachments[1]['ContentType'] == 'text/custom'


def test_html_to_text():
    html = (
        "<h1>Date</h1><p>6. April 1984</p>\n"
        "<h1>Path</h1><p>/foo-bar</p>\n"
    )

    plaintext = html_to_text(html)
    assert plaintext == "# Date\n\n6. April 1984\n\n# Path\n\n/foo-bar"


def test_object_by_path():

    class App(Framework):
        pass

    @App.path(path='/')
    class Root(object):
        pass

    @App.path(path='/pages', absorb=True)
    class Page(object):
        def __init__(self, absorb):
            self.absorb = absorb

    App.commit()

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


def test_send_email_transaction(tmpdir, redis_url):

    import more.transaction
    import more.webassets
    import onegov.core

    morepath.scan(more.transaction)
    morepath.scan(more.webassets)
    morepath.scan(onegov.core)

    class App(Framework):
        pass

    @App.path(path='/')
    class Root(object):
        pass

    @App.view(model=Root, name='send-fail')
    def fail_send(self, request):
        app.send_email(
            reply_to='Gövikon <info@example.org>',
            receivers=['recipient@example.org'],
            subject="Nüws",
            content="This e-mäil is just a test",
            category='transactional'
        )
        assert False

    @App.view(model=Root, name='send-ok')
    def success_send(self, request):
        app.send_email(
            reply_to='Gövikon <info@example.org>',
            receivers=['recipient@example.org'],
            subject="Nüws",
            content="This e-mäil is just a test",
            category='transactional'
        )

    maildir = tmpdir.mkdir('mail')
    app = App()
    app.application_id = 'test'
    app.configure_application(identity_secure=False, redis_url=redis_url)
    app.mail = {
        'transactional': {
            'directory': str(maildir),
            'sender': 'noreply@example.org'
        }
    }

    app.cache_backend = 'dogpile.cache.memory'
    app.cache_backend_arguments = {}

    client = Client(app)

    with pytest.raises(AssertionError):
        client.get('/send-fail')

    assert len(maildir.listdir()) == 0

    client.get('/send-ok')
    assert len(maildir.listdir()) == 1


def test_send_email_plaintext_alternative(tmpdir):

    maildir = tmpdir.mkdir('mail')
    app = Framework()
    app.mail = {
        'transactional': {
            'directory': str(maildir),
            'sender': 'noreply@example.org'
        }
    }

    app.send_email(
        reply_to='Govikon <info@example.org>',
        receivers=['recipient@example.org'],
        subject="Test E-Mail",
        content='<a href="http://example.org">This e-mail is just a test</a>',
        category='transactional'
    )

    transaction.commit()

    files = maildir.listdir()
    assert len(files) == 1
    messages = json.loads(files[0].read_text('utf-8'))
    assert len(messages) == 1
    message = messages[0]

    assert message['From'] == 'Govikon <noreply@example.org>'
    assert message['ReplyTo'] == 'Govikon <info@example.org>'
    assert message['Subject'] == 'Test E-Mail'
    assert message['HtmlBody'] == (
        '<a href="http://example.org">This e-mail is just a test</a>'
    )
    assert message['TextBody'] == (
        '[This e-mail is just a test](http://example.org)'
    )


def test_send_marketing_email_batch(tmpdir):

    maildir = tmpdir.mkdir('mail')
    app = Framework()

    app.mail = {
        'marketing': {
            'directory': str(maildir),
            'sender': 'noreply@example.org'
        }
    }

    unsubscribe = 'mailto:info@example.org'

    # NOTE: We use plaintext only to speed up the test
    mails = [
        app.prepare_email(
            reply_to='info@example.org',
            subject=f'Subject {index}',
            plaintext=f'Content {index}. {unsubscribe}',
            headers={'List-Unsubscribe': f'<{unsubscribe}>'}
        )
        for index in range(1, 1251)
    ]
    app.send_marketing_email_batch(mails)

    transaction.commit()

    files = sorted(maildir.listdir())
    assert len(files) == 3
    messages = json.loads(files[0].read_text('utf-8'))
    assert len(messages) == 500

    message = messages[0]
    assert message['From'] == 'noreply@example.org'
    assert message['ReplyTo'] == 'info@example.org'
    assert message['Subject'] == 'Subject 1'
    assert message['MessageStream'] == 'marketing'

    messages = json.loads(files[1].read_text('utf-8'))
    assert len(messages) == 500

    message = messages[0]
    assert message['From'] == 'noreply@example.org'
    assert message['ReplyTo'] == 'info@example.org'
    assert message['Subject'] == 'Subject 501'
    assert message['MessageStream'] == 'marketing'

    messages = json.loads(files[2].read_text('utf-8'))
    assert len(messages) == 250

    message = messages[0]
    assert message['From'] == 'noreply@example.org'
    assert message['ReplyTo'] == 'info@example.org'
    assert message['Subject'] == 'Subject 1001'
    assert message['MessageStream'] == 'marketing'


def test_send_marketing_email_batch_size_limit(tmpdir):

    maildir = tmpdir.mkdir('mail')
    app = Framework()

    app.mail = {
        'marketing': {
            'directory': str(maildir),
            'sender': 'noreply@example.org'
        }
    }

    unsubscribe = 'mailto:info@example.org'
    content = 'a' * 1_000_000  # 1 MB
    content += ' ' + unsubscribe
    # NOTE: We use plaintext only to speed up the test
    mails = [
        app.prepare_email(
            reply_to='info@example.org',
            subject=f'Subject {index}',
            plaintext=content,
            headers={'List-Unsubscribe': f'<{unsubscribe}>'}
        )
        for index in range(1, 75)
    ]
    app.send_marketing_email_batch(mails)

    transaction.commit()

    files = sorted(maildir.listdir())
    assert len(files) == 2
    payload = files[0].read_binary()
    assert len(payload) < 50_000_000
    messages = json.loads(payload.decode('utf-8'))
    assert len(messages) == 49

    message = messages[0]
    assert message['From'] == 'noreply@example.org'
    assert message['ReplyTo'] == 'info@example.org'
    assert message['Subject'] == 'Subject 1'
    assert message['MessageStream'] == 'marketing'

    payload = files[1].read_binary()
    assert len(payload) < 50_000_000
    messages = json.loads(payload.decode('utf-8'))
    assert len(messages) == 25

    message = messages[0]
    assert message['From'] == 'noreply@example.org'
    assert message['ReplyTo'] == 'info@example.org'
    assert message['Subject'] == 'Subject 50'
    assert message['MessageStream'] == 'marketing'


def test_send_marketing_email_batch_missing_unsubscribe(tmpdir):

    maildir = tmpdir.mkdir('mail')
    app = Framework()

    app.mail = {
        'marketing': {
            'directory': str(maildir),
            'sender': 'noreply@example.org'
        },
        'transactional': {
            'directory': str(maildir),
            'sender': 'noreply@example.org'
        },
    }

    # NOTE: We use plaintext only to speed up the test
    with pytest.raises(AssertionError):
        mails = [
            app.prepare_email(
                reply_to='info@example.org',
                subject=f'Subject {index}',
                plaintext=f'Content {index}',
            )
            for index in range(1, 10)
        ]
        app.send_marketing_email_batch(mails)


def test_send_marketing_email_batch_illegal_category(tmpdir):

    maildir = tmpdir.mkdir('mail')
    app = Framework()

    app.mail = {
        'marketing': {
            'directory': str(maildir),
            'sender': 'noreply@example.org'
        },
        'transactional': {
            'directory': str(maildir),
            'sender': 'noreply@example.org'
        },
    }

    # NOTE: We use plaintext only to speed up the test
    mails = [
        app.prepare_email(
            reply_to='info@example.org',
            subject=f'Subject {index}',
            plaintext=f'Content {index}',
            category='transactional',
        )
        for index in range(1, 10)
    ]
    with pytest.raises(AssertionError):
        app.send_marketing_email_batch(mails)


def test_send_zulip(session):
    with patch('urllib.request.urlopen') as urlopen:
        app = Framework()
        app.configure_application()

        thread = app.send_zulip('Zulip integration', 'It works!')
        assert thread is None

        app.zulip_url = 'https://seantis.zulipchat.com/api/v1/messages'
        app.zulip_stream = 'Testing'
        app.zulip_user = 'test-bot@seantis.zulipchat.com'
        app.zulip_key = 'aabbcc'

        thread = app.send_zulip('Zulip integration', 'It works!')
        assert thread is not None
        thread.join()

        assert urlopen.called
        url = urlopen.call_args[0][0].get_full_url()
        data = dict(parse_qsl(urlopen.call_args[0][1].decode('utf-8')))
        headers = urlopen.call_args[0][0].headers

        assert url == 'https://seantis.zulipchat.com/api/v1/messages'
        assert data == {
            'type': 'stream',
            'to': 'Testing',
            'subject': 'Zulip integration',
            'content': 'It works!'
        }
        assert headers == {
            'Authorization':
            'Basic dGVzdC1ib3RAc2VhbnRpcy56dWxpcGNoYXQuY29tOmFhYmJjYw==',
            'Content-length': 68,
            'Content-type': 'application/x-www-form-urlencoded'
        }


def test_generic_redirect(redis_url):

    import more.transaction
    import more.webassets
    import onegov.core

    morepath.scan(more.transaction)
    morepath.scan(more.webassets)
    morepath.scan(onegov.core)

    class App(Framework):
        pass

    @App.path(path='/foo')
    class FooRedirect(Redirect):
        to = '/bar'

    @App.path(path='/bar', absorb=True)
    class BarRedirect(Redirect):
        to = '/foo'

    App.commit()

    app = App()
    app.namespace = 'test'
    app.configure_application(identity_secure=False, redis_url=redis_url)
    app.set_application_id('test/test')

    client = Client(app)

    assert client.get('/foo', status=302).location.endswith('/bar')
    assert client.get('/fooo', status=404)
    assert client.get('/foo/bar', status=404)

    assert client.get('/bar', status=302).location.endswith('/foo')
    assert client.get('/barr', status=404)
    assert client.get('/bar/foo', status=302).location.endswith('/foo/foo')
