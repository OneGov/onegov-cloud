from __future__ import annotations

import morepath
import onegov.core
import onegov.onboarding
import os.path
import pytest

from onegov.core.utils import scan_morepath_modules
from uuid import uuid4


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator


@pytest.fixture(scope="function")
def onboarding_app(
    postgres_dsn: str,
    temporary_directory: str,
    maildir: str,
    es_url: str,
    redis_url: str
) -> Iterator[onegov.onboarding.OnboardingApp]:

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
        depot_backend='depot.io.memory.MemoryFileStorage',
        redis_url=redis_url,
        onboarding={
            'onegov.town6': {
                'namespace': 'town6_' + uuid4().hex,
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
            'directory': maildir,
            'sender': 'mails@govikon.ch'
        },
        'transactional': {
            'directory': maildir,
            'sender': 'mails@govikon.ch'
        }
    }
    app.maildir = maildir  # type: ignore[attr-defined]

    yield app
