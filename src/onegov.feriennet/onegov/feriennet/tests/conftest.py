import transaction
import pytest

from onegov.feriennet import FeriennetApp
from onegov.feriennet.initial_content import create_new_organisation
from onegov.testing.utils import create_app
from onegov.user import User


@pytest.yield_fixture(scope='function')
def feriennet_app(request):
    yield create_feriennet_app(request, use_elasticsearch=False)


@pytest.yield_fixture(scope='function')
def es_feriennet_app(request):
    yield create_feriennet_app(request, use_elasticsearch=True)


def create_feriennet_app(request, use_elasticsearch):
    app = create_app(
        app_class=FeriennetApp,
        request=request,
        use_elasticsearch=use_elasticsearch)

    session = app.session()

    org = create_new_organisation(app, name="Govikon")
    org.meta['reply_to'] = 'mails@govikon.ch'

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
