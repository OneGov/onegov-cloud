import morepath
import onegov.core
import onegov.onboarding
import os.path
import pytest

from onegov.core.utils import scan_morepath_modules
from uuid import uuid4


@pytest.yield_fixture(scope="function")
def onboarding_app(postgres_dsn, temporary_directory, smtp, es_url):

    scan_morepath_modules(onegov.onboarding.OnboardingApp)
    morepath.commit(onegov.onboarding.OnboardingApp)

    app = onegov.onboarding.OnboardingApp()
    app.namespace = 'test_' + uuid4().hex
    app.configure_application(
        dsn=postgres_dsn,
        filestorage='fs.osfs.OSFS',
        filestorage_options={
            'root_path': os.path.join(temporary_directory, 'file-storage'),
            'create': True
        },
        identity_secure=False,
        disable_memcached=True,
        depot_backend='depot.io.memory.MemoryFileStorage',
        onboarding={
            'onegov.town': {
                'namespace': 'town_' + uuid4().hex,
                'domain': 'example.org',
                'configuration': {
                    'depot_backend': 'depot.io.memory.MemoryFileStorage'
                }
            }
        },
        elasticsearch_hosts=[es_url]
    )
    app.set_application_id(app.namespace + '/' + 'test')

    app.mail = {
        'marketing': {
            'host': smtp.address[0],
            'port': smtp.address[1],
            'force_tls': False,
            'username': None,
            'password': None,
            'use_directory': False,
            'sender': 'mails@govikon.ch'
        },
        'transactional': {
            'host': smtp.address[0],
            'port': smtp.address[1],
            'force_tls': False,
            'username': None,
            'password': None,
            'use_directory': False,
            'sender': 'mails@govikon.ch'
        }
    }

    yield app
