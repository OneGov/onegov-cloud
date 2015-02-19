import tempfile
import textwrap

from onegov.server.application import Application
from onegov.server.config import Config, ApplicationConfig


def test_static_application_config():
    cfg = ApplicationConfig({
        'path': '/application/',
        'application': 'onegov.server.application.Application',
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
            configuration:
              foo: bar
          - path: /wildcard/*
            application: onegov.server.application.Application
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
