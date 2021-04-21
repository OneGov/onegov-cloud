import pytest
import transaction

from onegov.fsi.initial_content import create_new_organisation
from onegov.translator_directory import TranslatorDirectoryApp
from onegov.user import User
from sqlalchemy.orm.session import close_all_sessions
from tests.onegov.fsi.common import global_password
from tests.onegov.fsi.common import hashed_password as _hashed_password
from tests.shared import Client as BaseClient
from tests.shared.utils import create_app


class Client(BaseClient):

    use_intercooler = True
    skip_first_form = True

    def login_member(self, to=None):
        return self.login('member@example.org', global_password, to)


@pytest.fixture(scope='session')
def plain_password():
    return global_password


@pytest.fixture(scope='session')
def hashed_password():
    return _hashed_password


@pytest.fixture(scope='function')
def translator_app(request, hashed_password):
    yield create_translator_app(request, False, hashed_password)


@pytest.fixture(scope='function')
def es_translator_app(request, hashed_password):
    yield create_translator_app(request, True, hashed_password)


@pytest.fixture(scope='function')
def client(translator_app):
    return Client(translator_app)


@pytest.fixture(scope='function')
def client_with_es(es_translator_app):
    return Client(es_translator_app)


def create_translator_app(request, use_elasticsearch, hashed_password):

    app = create_app(
        app_class=TranslatorDirectoryApp,
        request=request,
        use_elasticsearch=use_elasticsearch
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
        password_hash=hashed_password,
        role='admin'
    ))
    session.add(User(
        username='editor@example.org',
        password_hash=hashed_password,
        role='editor'
    ))

    session.add(User(
        username='member@example.org',
        password_hash=hashed_password,
        role='member'
    ))

    transaction.commit()
    close_all_sessions()

    return app
