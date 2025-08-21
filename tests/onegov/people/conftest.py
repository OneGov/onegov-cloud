from __future__ import annotations

import pytest
from onegov.core import Framework
from onegov.file import DepotApp
from os import path
from tests.shared.utils import create_app
from yaml import dump


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from onegov.core.orm import SessionManager


@pytest.fixture(scope='function')
def cfg_path(
    postgres_dsn: str,
    session_manager: SessionManager,
    temporary_directory: str,
    redis_url: str
) -> str:

    cfg = {
        'applications': [
            {
                'path': '/foo/*',
                'application': 'onegov.core.Framework',
                'namespace': 'foo',
                'configuration': {
                    'dsn': postgres_dsn,
                    'redis_url': redis_url
                }
            }
        ]
    }

    session_manager.ensure_schema_exists('foo-bar')

    cfg_path = path.join(temporary_directory, 'onegov.yml')
    with open(cfg_path, 'w') as f:
        f.write(dump(cfg))

    return cfg_path


class TestApp(Framework, DepotApp):
    __test__ = False


@pytest.fixture(scope='function')
def test_app(request: pytest.FixtureRequest) -> Iterator[TestApp]:
    app = create_app(TestApp, request, use_maildir=False)
    yield app
    app.session_manager.dispose()
