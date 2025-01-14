from __future__ import annotations

from onegov.core.request import CoreRequest


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.gazette.app import GazetteApp


# NOTE: Currently this is purely for type checking, so we know the requests
#       in our election day app have the election day app available
# FIXME: Maybe we want to make Request generic in app instead?
class GazetteRequest(CoreRequest):
    if TYPE_CHECKING:
        app: GazetteApp
