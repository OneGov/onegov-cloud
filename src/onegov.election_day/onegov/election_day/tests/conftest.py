import more.webassets
import onegov.core
import onegov.town
import os.path
import pytest
import textwrap

from morepath import setup
from uuid import uuid4


@pytest.yield_fixture(scope="function")
def election_day_app(postgres_dsn, temporary_directory):

    config = setup()
    config.scan(more.webassets)
    config.scan(onegov.core)
    config.scan(onegov.election_day)
    config.commit()

    app = onegov.election_day.ElectionDayApp()
    app.namespace = 'test_' + uuid4().hex
    app.configure_application(
        dsn=postgres_dsn,
        filestorage='fs.osfs.OSFS',
        filestorage_options={
            'root_path': os.path.join(temporary_directory, 'file-storage'),
            'create': True
        },
        identity_secure=False,
        disable_memcached=True
    )
    app.set_application_id(app.namespace + '/' + 'test')

    app.filestorage.setcontents('principal.yml', textwrap.dedent("""
        name: Kanton Govikon
    """))

    yield app
