import pytest
import transaction

from onegov.core.csv import CSVFile
from onegov.core.utils import module_path
from onegov.user import User
from onegov.winterthur import WinterthurApp
from onegov.winterthur.initial_content import create_new_organisation
from onegov_testing.utils import create_app
from pathlib import Path


@pytest.fixture()
def fixtures():
    return Path(module_path('onegov.winterthur', 'tests/fixtures'))


@pytest.fixture(scope='session', autouse=True)
def scan_dependencies():
    import importscan
    import onegov

    importscan.scan(onegov.org, ignore=['.test', '.tests'])


@pytest.fixture()
def streets_csv(fixtures):
    with (fixtures / 'streets.csv').open('rb') as f:
        yield CSVFile(f)


@pytest.fixture()
def addresses_csv(fixtures):
    with (fixtures / 'addresses.csv').open('rb') as f:
        yield CSVFile(f)


@pytest.yield_fixture(scope='function')
def winterthur_app(request):
    yield create_winterthur_app(request, use_elasticsearch=False)


@pytest.yield_fixture(scope='function')
def es_winterthur_app(request):
    yield create_winterthur_app(request, use_elasticsearch=True)


def create_winterthur_app(request, use_elasticsearch):

    app = create_app(
        app_class=WinterthurApp,
        request=request,
        use_elasticsearch=use_elasticsearch)

    session = app.session()

    org = create_new_organisation(app, name="Winterthur")
    org.meta['reply_to'] = 'mails@govikon.ch'
    org.meta['locales'] = 'de_CH'

    # usually we don't want to create the users directly, anywhere else you
    # *need* to go through the UserCollection. Here however, we can improve
    # the test speed by not hashing the password for every test.
    test_password = request.getfixturevalue('test_password')

    session.add(User(
        username='admin@example.org',
        password_hash=test_password,
        role='admin'
    ))
    session.add(User(
        username='editor@example.org',
        password_hash=test_password,
        role='editor'
    ))

    transaction.commit()
    session.close_all()

    return app
