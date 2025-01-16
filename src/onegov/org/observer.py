from __future__ import annotations

from onegov.core.orm import observes as base_observes


from typing import Any, TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable

    _F = TypeVar('_F', bound=Callable[..., Any])


def observes(*paths: str) -> Callable[[_F], _F]:
    return base_observes(*paths, scope='onegov.org.app.OrgApp')
