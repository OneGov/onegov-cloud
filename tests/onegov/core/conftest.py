import os.path
import pytest
import transaction
import yaml

from tests.shared import Client
from tests.shared.utils import create_app
from onegov.core.cli import command_group
from onegov.core.elements import Element
from onegov.core.framework import Framework
from onegov.core.layout import ChameleonLayout


@pytest.fixture(scope='session', autouse=True)
def cache_password_hashing(monkeysession):
    pass  # override the password hashing set by tests.shared for the core


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
def cli_config(postgres_dsn, redis_url, temporary_directory):
    cfg = {
        'applications': [
            {
                'path': '/foobar/*',
                'application': 'onegov.core.Framework',
                'namespace': 'foobar',
                'configuration': {
                    'dsn': postgres_dsn,
                    'redis_url': redis_url,
                }
            }
        ]
    }

    path = os.path.join(temporary_directory, 'onegov.yml')

    with open(path, 'w') as f:
        f.write(yaml.dump(cfg))

    return path


@pytest.fixture(scope='function')
def render_element(request):
    class App(Framework):
        pass

    @App.path(path='/element', model=Element)
    def get_element(app):
        return app.element

    @App.html(model=Element)
    def render_element(self, request):
        return self(ChameleonLayout(getattr(self, 'model', None), request))

    app = create_app(App, request, use_elasticsearch=False)
    transaction.commit()

    client = Client(app)

    def render(element):
        app.element = element
        return client.get('/element')

    return render


@pytest.fixture(scope='function')
def maildir_app(temporary_directory, maildir):
    app_cfg = {
        'mail': {
            'marketing': {
                'sender': 'noreply@example.org',
                'directory': maildir
            },
            'transactional': {
                'sender': 'noreply@example.org',
                'directory': maildir
            }
        }
    }

    cfg = {
        'applications': [
            {
                'path': '/foobar/*',
                'application': 'onegov.core.Framework',
                'namespace': 'foobar',
                'configuration': app_cfg
            }
        ]
    }

    with open(os.path.join(temporary_directory, 'onegov.yml'), 'w') as f:
        f.write(yaml.dump(cfg))

    app = Framework()
    app.configure_application(**app_cfg)

    return app
