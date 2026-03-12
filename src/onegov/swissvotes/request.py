from __future__ import annotations

from onegov.core.request import CoreRequest


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.swissvotes.app import SwissvotesApp


# NOTE: Currently this is purely for type checking
class SwissvotesRequest(CoreRequest):
    if TYPE_CHECKING:
        app: SwissvotesApp
