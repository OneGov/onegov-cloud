import onegov.core
import onegov.town
import pytest
import transaction

from onegov.core.utils import module_path
from onegov.testing.utils import create_app
from onegov.town import TownApp
from onegov.town.initial_content import builtin_form_definitions
from onegov.town.initial_content import create_new_organisation
from onegov.user import User


@pytest.yield_fixture(scope='session')
def handlers():
    yield onegov.ticket.handlers
    onegov.ticket.handlers.registry = {}


@pytest.yield_fixture(scope='session')
def forms():
    yield list(builtin_form_definitions(
        module_path('onegov.town', 'forms/builtin')))


@pytest.yield_fixture(scope='function')
def town_app(request):
    yield create_town_app(request, use_elasticsearch=False)


@pytest.yield_fixture(scope='function')
def es_town_app(request):
    yield create_town_app(request, use_elasticsearch=True)


def create_town_app(request, use_elasticsearch):
    app = create_app(TownApp, request, use_elasticsearch=False)
    session = app.session()

    forms = request.getfixturevalue('forms')
    create_new_organisation(
        app, 'Govikon', 'mails@govikon.ch', forms, create_files=False)

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
