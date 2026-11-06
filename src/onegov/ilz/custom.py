from __future__ import annotations

from onegov.ilz import ILZApp
from onegov.town6.custom import get_global_tools


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.ilz.request import ILZRequest


@ILZApp.template_variables()
def get_template_variables(request: ILZRequest) -> dict[str, Any]:
    return {
        'global_tools': tuple(get_global_tools(request)),
    }
