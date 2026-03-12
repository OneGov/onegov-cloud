from __future__ import annotations

import morepath

from onegov.core.framework import Framework
from onegov.core.theme import get_filename
from webtest import TestApp as Client


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.request import CoreRequest
    from onegov.core.theme import Theme
else:
    Theme = object


class MockTheme(Theme):

    def __init__(self, name: str, version: str, result: str = '') -> None:
        self.name = name  # type: ignore[misc]
        self.version = version
        self.result = result
        self.default_options: dict[str, Any] = {}

    def compile(self, options: dict[str, Any] | None = None) -> str:
        return self.result.format(**(options or self.default_options))


def test_get_filename() -> None:
    theme = MockTheme('test', '1.0')

    assert get_filename(theme).endswith('.css')
    assert get_filename(theme) == get_filename(theme)
    assert get_filename(theme) != get_filename(MockTheme('test', '1.1'))
    assert get_filename(theme) != get_filename(MockTheme('another', '1.0'))
    assert get_filename(theme, {'x': 1}) == get_filename(theme, {'x': 1})
    assert get_filename(theme, {'x': 1}) != get_filename(theme)
    assert get_filename(theme, {'x': 1}) != get_filename(theme, {'x': 2})


def test_theme_application(temporary_directory: str, redis_url: str) -> None:

    class App(Framework):
        theme_options = {
            'color': 'red'
        }

    @App.path('/')
    class Model:
        pass

    @App.setting(section='core', name='theme')
    def get_theme() -> MockTheme:
        return MockTheme('test', '1.0', 'body {{ background: {color} }}')

    @App.view(model=Model)
    def view_file(self: Model, request: CoreRequest) -> str:
        return request.theme_link

    import onegov.core
    import more.transaction
    import more.webassets
    morepath.scan(more.transaction)
    morepath.scan(more.webassets)
    morepath.scan(onegov.core)
    morepath.commit(App)

    app = App()
    app.namespace = 'tests'
    app.configure_application(
        redis_url=redis_url,
        filestorage='fs.osfs.OSFS',
        filestorage_options={
            'root_path': temporary_directory
        }
    )
    app.set_application_id('tests/foo')

    client = Client(app)
    theme_url = client.get('/').text

    assert 'background: red' in client.get(theme_url).text

    app.set_application_id('tests/bar')

    theme_url = client.get('/').text
    assert 'background: red' in client.get(theme_url).text

    app.theme_options = {
        'color': 'blue'
    }

    new_theme_url = client.get('/').text
    assert theme_url != new_theme_url
