import more.webassets
import onegov.core
import onegov.town
import pytest
import transaction

from morepath import setup
from onegov.town.initial_content import add_initial_content
from onegov.user import UserCollection
from uuid import uuid4


@pytest.yield_fixture(scope="function")
def town_app(postgres_dsn):
    config = setup()
    config.scan(more.webassets)
    config.scan(onegov.core)
    config.scan(onegov.town)
    config.commit()

    app = onegov.town.TownApp()
    app.namespace = 'test_' + uuid4().hex
    app.configure_application(
        dsn=postgres_dsn,
        filestorage='fs.memoryfs.MemoryFS',
        identity_secure=False,
        disable_memcached=True
    )
    app.set_application_id(app.namespace + '/' + 'test')

    add_initial_content(app.session(), 'Govikon')

    users = UserCollection(app.session())
    users.add('admin@example.org', 'hunter2', 'admin')
    users.add('editor@example.org', 'hunter2', 'editor')

    transaction.commit()

    yield app
