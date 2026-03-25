from __future__ import annotations

from onegov.fedpol import FedpolApp
from onegov.town6.custom import get_global_tools


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.fedpol.request import FedpolRequest


@FedpolApp.template_variables()
def get_template_variables(request: FedpolRequest) -> dict[str, Any]:
    return {
        'global_tools': tuple(get_global_tools(request)),
    }
