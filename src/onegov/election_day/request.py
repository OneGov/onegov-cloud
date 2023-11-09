from onegov.core.request import CoreRequest


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.election_day.app import ElectionDayApp


# NOTE: Currently this is purely for type checking, so we know the requests
#       in our election day app have the election day app available
# FIXME: Maybe we want to make Request generic in app instead?
class ElectionDayRequest(CoreRequest):
    if TYPE_CHECKING:
        app: 'ElectionDayApp'
