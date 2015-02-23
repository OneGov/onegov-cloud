import tempfile
import textwrap
import pytest

from onegov.server import errors
from onegov.server.application import Application
from onegov.server.config import Config, ApplicationConfig


def test_static_application_config():
    cfg = ApplicationConfig({
        'path': '/application/',
        'application': 'onegov.server.application.Application',
        'namespace': 'test'
    })

    assert cfg.path == '/application'
    assert cfg.application_class is Application
    assert cfg.configuration == {}
    assert cfg.root == '/application'
    assert cfg.is_static


def test_wildcard_application_config():
    cfg = ApplicationConfig({
        'path': '/application/*',
        'application': 'onegov.server.application.Application',
        'namespace': 'test',
        'configuration': {
            'foo': 'bar'
        }
    })

    assert cfg.path == '/application/*'
    assert cfg.application_class is Application
    assert cfg.configuration == {'foo': 'bar'}
    assert cfg.root == '/application'
    assert not cfg.is_static


def test_config_from_yaml():
    yaml = textwrap.dedent("""
        applications:
          - path: /static
            application: onegov.server.application.Application
            namespace: static
            configuration:
              foo: bar
          - path: /wildcard/*
            application: onegov.server.application.Application
            namespace: wildcard
            configuration:
              bar: foo
    """)

    with tempfile.NamedTemporaryFile('w') as f:
        f.write(yaml)
        f.flush()

        config = Config.from_yaml_file(f.name)

    assert len(config.applications) == 2
    assert config.applications[0].is_static
    assert config.applications[0].path == '/static'
    assert config.applications[0].root == '/static'
    assert config.applications[0].application_class is Application
    assert config.applications[0].configuration == {'foo': 'bar'}

    assert not config.applications[1].is_static
    assert config.applications[1].path == '/wildcard/*'
    assert config.applications[1].root == '/wildcard'
    assert config.applications[1].application_class is Application
    assert config.applications[1].configuration == {'bar': 'foo'}


def test_unique_namespace():
    with pytest.raises(errors.ApplicationConflictError):
        Config({
            'applications': [
                {
                    'path': '/one/*',
                    'application': 'onegov.server.application.Application',
                    'namespace': 'test',
                },
                {
                    'path': '/two/*',
                    'application': 'onegov.server.application.Application',
                    'namespace': 'test',
                }
            ]
        })
