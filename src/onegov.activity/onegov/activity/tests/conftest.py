from onegov.user import UserCollection
from pytest import fixture


@fixture(scope='function')
def owner(session):
    return UserCollection(session).add(
        username='owner@example.org',
        password='hunter2',
        role='editor'
    )


@fixture(scope='function')
def secondary_owner(session):
    return UserCollection(session).add(
        username='secondary@example.org',
        password='hunter2',
        role='editor'
    )
