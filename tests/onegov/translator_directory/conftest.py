import pytest
import transaction

from onegov.fsi.initial_content import create_new_organisation
from onegov.translator_directory import TranslatorDirectoryApp
from onegov.user import User
from sqlalchemy.orm.session import close_all_sessions
from tests.shared import Client as BaseClient
from tests.shared.utils import create_app
from onegov.core.crypto import hash_password


class Client(BaseClient):

    use_intercooler = True
    skip_n_forms = 1

    def login_member(self, to=None):
        return self.login('member@example.org', 'hunter2', to)


@pytest.fixture(scope='function')
def translator_app(request):
    yield create_translator_app(request, False)


@pytest.fixture(scope='function')
def es_translator_app(request):
    yield create_translator_app(request, True)


@pytest.fixture(scope='function')
def client(translator_app):
    return Client(translator_app)


@pytest.fixture(scope='function')
def client_with_es(es_translator_app):
    return Client(es_translator_app)


def create_translator_app(request, use_elasticsearch):

    app = create_app(
        app_class=TranslatorDirectoryApp,
        request=request,
        use_elasticsearch=use_elasticsearch,
        websockets={
            'client_url': 'ws://localhost:8766',
            'manage_url': 'ws://localhost:8766',
            'manage_token': 'super-super-secret-token'
        }
    )

    session = app.session()

    org = create_new_organisation(app, name="Übersetzerverzeichnis")
    org.meta['reply_to'] = 'mails@govikon.ch'
    org.meta['locales'] = 'de_CH'

    # usually we don't want to create the users directly, anywhere else you
    # *need* to go through the UserCollection. Here however, we can improve
    # the test speed by not hashing the password for every test.

    session.add(User(
        username='admin@example.org',
        password_hash=hash_password('hunter2'),
        role='admin'
    ))
    session.add(User(
        username='editor@example.org',
        password_hash=hash_password('hunter2'),
        role='editor'
    ))

    session.add(User(
        username='member@example.org',
        password_hash=hash_password('hunter2'),
        role='member'
    ))

    transaction.commit()
    close_all_sessions()

    return app
