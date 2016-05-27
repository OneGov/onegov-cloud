import pytest
import os.path
import yaml

from onegov.core.cli import command_group


@pytest.fixture(scope='session', autouse=True)
def cache_password_hashing(monkeysession):
    pass  # override the password hashing set by onegov.testing for the core


@pytest.fixture(scope='function')
def cli(request):
    cli = command_group()

    @cli.command(context_settings=request.param or {})
    def create():
        nonlocal cli
        cli.called = True

        def perform(request, app):
            cli.called_request = True

        return perform

    return cli


@pytest.fixture(scope='function')
def cli_config(postgres_dsn, temporary_directory):
    cfg = {
        'applications': [
            {
                'path': '/foobar/*',
                'application': 'onegov.core.Framework',
                'namespace': 'foobar',
                'configuration': {
                    'dsn': postgres_dsn
                }
            }
        ]
    }

    path = os.path.join(temporary_directory, 'onegov.yml')

    with open(path, 'w') as f:
        f.write(yaml.dump(cfg))

    return path
