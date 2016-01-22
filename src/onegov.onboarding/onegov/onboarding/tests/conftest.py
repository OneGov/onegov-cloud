import onegov.core
import onegov.onboarding
import os.path
import pytest

from morepath import setup
from onegov.core.utils import scan_morepath_modules
from uuid import uuid4


@pytest.yield_fixture(scope="function")
def onboarding_app(postgres_dsn, temporary_directory):

    config = setup()
    scan_morepath_modules(onegov.onboarding.OnboardingApp, config)
    config.commit()

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
        onboarding={
            'onegov.town': {
                'namespace': 'town_' + uuid4().hex,
                'domain': 'example.org'
            }
        }
    )
    app.set_application_id(app.namespace + '/' + 'test')

    yield app
