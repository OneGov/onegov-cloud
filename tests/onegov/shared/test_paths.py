import os.path

from onegov.shared import asset


def test_assets() -> None:
    assert os.path.exists(asset('js/form_dependencies.js'))
