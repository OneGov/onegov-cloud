from __future__ import annotations

from onegov.core.utils import module_path


def asset(path: str) -> str:
    """ Returns the absolute path to an asset path relative to this module. """
    return module_path('onegov.shared', 'assets' + '/' + path.lstrip('/'))
